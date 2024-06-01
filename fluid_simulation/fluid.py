from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.view.scene import Scene

import numpy as np
import ctypes as ct
from enum import Enum
from core.view.scene import Scene 
from core.models.entity import Entity, Eulers
from core.models.material import Material
from core.models.mesh import Mesh
from core.models.shader import Shader, ComputeShader
from OpenGL.GL import *
from math import floor, log2

FLUID_SHADER_PATH = {
    "VERTEX":  "./fluid_simulation/fluid_vertex.vert",
    "FRAGMENT": "./fluid_simulation/fluid_fragment.frag",
    "DENSITIES": "./fluid_simulation/compute_shaders/density.comp",
    "EXTERNAL_FORCES": "./fluid_simulation/compute_shaders/external_forces.comp",
    "GPU_SORT_OFFSET": "./fluid_simulation/compute_shaders/gpu_sort_offset.comp",
    "GPU_SORT": "./fluid_simulation/compute_shaders/gpu_sort.comp",
    "PRESSURE": "./fluid_simulation/compute_shaders/pressure.comp",
    "SPATIAL_HASH": "./fluid_simulation/compute_shaders/spatial_hash.comp",
    "UPDATE_POSITION": "./fluid_simulation/compute_shaders/update_pos.comp",
    "VISCOSITY": "./fluid_simulation/compute_shaders/viscosity.comp",
}

PARTICLEAREA_MESH = Mesh("./assets/cube/cube.obj", GL_TRIANGLES, False)
PARTICLEAREA_MATERIAL = Material("./assets/cube//white_borders.png", False)
PARTICLEAREA_SHADERS = Shader("./assets/cube/vertex.vert", "./assets/cube/fragment.frag", False)
PARTICLEAREA_LABEL = "PARTICLEAREA"

FLUIDPARTICLE_MESH = Mesh("./assets/sphere.obj", GL_TRIANGLES, False)
FLUIDPARTICLE_SHADERS = Shader(FLUID_SHADER_PATH["VERTEX"], FLUID_SHADER_PATH["FRAGMENT"], False)
FLUIDPARTICLE_PADDING = 0.01

#NE PAS CHANGER CES VALEURS
POSITIONS_BINDING_POINT = 1
PREDICTED_POSITIONS_BINDING_POINT = 2
VELOCITIES_BINDING_POINT = 3
DENSITIES_BINDING_POINT = 4
SPATIAL_INDICES_BINDING_POINT = 5
SPATIAL_OFFSETS_BINDING_POINT = 6
PARAMS_BINDING_POINT = 7

class SimParams(Enum):
    """ 
    Le premier composant représent l'offset en mémoire (un float => 4 bytes etc...)
    Le 2eme composant représente la taille en byte du paramètre
    Le 3eme argument c'est le type de donnée (pour les listes c'est le type des éléments de la liste)
    """
    SIMULATION_CORNER_1 = (0, 16, np.float32)
    SIMULATION_CORNER_2 = (16, 12, np.float32)
    PARTICLE_COUNT = (28, 4, np.int32)
    PARTICLE_SIZE = (32, 4, np.float32)
    SMOOTHING_RADIUS = (36, 4, np.float32)
    TARGET_DENSITY = (40, 4, np.float32)
    PRESSURE_CST = (44, 4, np.float32)
    GRAVITY = (48, 4, np.float32)
    DELTA = (52, 4, np.float32)
    COLLISION_DAMPING_FACTOR = (56, 4, np.float32)
    VISCOSITY_STRENGTH = (60, 4, np.float32)
    DISABLE_SIMULATION = (64, 4, bool)


def create_buffer(data: np.ndarray, binding_point: int):
    """
    Crée un SSBO avec les données data.
    Bien veiller à ce que le binding point soit unique dans toute la codebase car 
    les SSBO sont communs à tout les shaders.
    """
    buffer = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buffer)
    glNamedBufferStorage(buffer, data.nbytes, data, GL_DYNAMIC_STORAGE_BIT)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding_point, buffer)
    return buffer


class Fluid(Entity):
    def __init__(self, particle_count: int, particle_size: float, simulation_corner_1: list[float], simulation_corner_2: list[float], particle_mesh: Mesh = FLUIDPARTICLE_MESH, particle_shaders: Shader = FLUIDPARTICLE_SHADERS) -> None:
        # Setup de l'entitée associé au Fluide
        fluid_position = [
            simulation_corner_1[0] + 0.5*(simulation_corner_1[0] - simulation_corner_2[0]),
            simulation_corner_1[1] + 0.5*(simulation_corner_1[1] - simulation_corner_2[1]),
            simulation_corner_1[2] + 0.5*(simulation_corner_1[2] - simulation_corner_2[2])
        ]
        super().__init__(fluid_position, Eulers(False, [0, 0, 0]), [1.0, 1.0, 1.0])
        
        #paramètres de la simulation
        self.simulation_corner_1 = np.array(simulation_corner_1, dtype=np.float32)
        self.simulation_corner_2 = np.array(simulation_corner_2, dtype=np.float32)
        self.particle_count = particle_count
        self.particle_size = particle_size
        self.smoothing_radius = 0.35
        self.target_density = 35.5
        self.pressure_cst = 27.33
        self.gravity = -10.0
        self.delta = 0.0
        self.collision_damping_factor = 0.5
        self.viscosity_strength = 0.06
        self.disable_simulation = True
        
        # Références aux buffers au cas où on en ai besoin
        self.params_buffer = None
        self.storage_buffers = [0] * 7

        #Différents shaders et objets associés au fluide
        self.particle_mesh: Mesh = particle_mesh
        self.particle_shaders: Shader = particle_shaders
        self.particle_area = None

    def init_fluid_shaders(self) -> None:
        """
        Cette fonction initialise les fragment et vertex shaders des particules ainsi que tout
        les compute shaders.
        """
        # Initialisation du fragment et vertex shader
        self.particle_shaders.init_shader()
        self.particle_mesh.init_mesh()
        self.particle_shaders.set_float("particleSize", self.particle_size)

        # Initialisation des compute shader
        self.compute_density = ComputeShader(FLUID_SHADER_PATH["DENSITIES"], init_on_creation=True)
        self.compute_external = ComputeShader(FLUID_SHADER_PATH["EXTERNAL_FORCES"], init_on_creation=True)
        self.compute_pressure = ComputeShader(FLUID_SHADER_PATH["PRESSURE"], init_on_creation=True)
        self.compute_spatial_hash = ComputeShader(FLUID_SHADER_PATH["SPATIAL_HASH"], init_on_creation=True)
        self.compute_viscosity = ComputeShader(FLUID_SHADER_PATH["VISCOSITY"], init_on_creation=True)
        self.compute_update_pos = ComputeShader(FLUID_SHADER_PATH["UPDATE_POSITION"], init_on_creation=True)
        
        self.compute_sort = GPUSort(self.particle_count)

    def create_bounding_box(self, scene: Scene) -> tuple[np.ndarray, np.ndarray]:
        """
        Crée l'entitée visuelle qui indique les limites de la simulation
        """
        position = 0.5*(self.simulation_corner_1 + self.simulation_corner_2)
        scale = abs(self.simulation_corner_1 - self.simulation_corner_2)
        self.scale = scale/2

        self.particle_area = Entity(
            position.tolist(),
            Eulers(False, [0, 0, 0]), 
            scale.tolist(), 
            mesh=PARTICLEAREA_MESH, 
            shaders=PARTICLEAREA_SHADERS, 
            material=PARTICLEAREA_MATERIAL
        )
        self.particle_area.set_label(PARTICLEAREA_LABEL)

        scene.append_entity(self.particle_area)

        return position, scale

    def create_initial_particle_positions(self, position: np.ndarray, scale: np.ndarray) -> np.ndarray:
        """
        Renvoit les positions initiales des particules de la simulation.
        Les particules sont arrangés en grille.
        """
        max_particles_x = floor(scale[0]/((self.particle_size + FLUIDPARTICLE_PADDING)))
        max_particles_y = floor(scale[1]/((self.particle_size + FLUIDPARTICLE_PADDING)))
        max_particles_z = floor(scale[2]/((self.particle_size + FLUIDPARTICLE_PADDING)))
        max_particles = max_particles_x * max_particles_y * max_particles_z
        if self.particle_count > max_particles:
            print(f"Trop de particules dans la zone de simulation, le nombre de particule est donc réduit au maximum: {max_particles}")
            self.particle_count = max_particles
            self.compute_sort.buffer_size = self.particle_count

        data = []
        for i in range(self.particle_count):
            px = position[0] + scale[0] - self.particle_size - (i % max_particles_x)*(2*self.particle_size + FLUIDPARTICLE_PADDING)
            py = position[1] + scale[1] - self.particle_size - (floor(i/max_particles_x)% max_particles_y) *(2*self.particle_size + FLUIDPARTICLE_PADDING)
            pz = position[2] + scale[2] - self.particle_size - floor(i/(max_particles_x*max_particles_y))*(2*self.particle_size + FLUIDPARTICLE_PADDING)
            data.extend([
                px, py, pz, # Position
                0 # padding
                ])
        data.pop(-1)
        return np.array(data, dtype=np.float32)

    def set_simulation_param(self, name: SimParams, value: any) -> None:
        """
        Permet de modifier un des 10 paramètres de la simulation, listés 
        par l'enum SimParams. 

        Noter que les listes doivent être des listes numpy avec un datatype np.float32
        """
        setattr(self, name.name.lower(), value)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.params_buffer)
        if type(value) == np.ndarray:
            if len(value) == 3:
                np.append(value, 0.0)
        else:
            value = np.array([value], dtype=name.value[2])
        glNamedBufferSubData(self.params_buffer, name.value[0], name.value[1], value)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
    def get_simulation_param(self, name: SimParams, from_gpu: bool = False) -> any:
        """
        Retourne le paramètre de la simulation demandé. Tout les paramètres
        qui peuvent être demandés sont dans l'enum SimParams

        Le paramètre from_gpu est pour spécifier si on doit aller chercher le paramètre directement sur la carte graphique
        ou si on prends la valeur en cache dans la classe Fluid
        """
        if from_gpu:
            glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.params_buffer)
            data = glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, name.value[0], name.value[1])
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            if name.value[2] == np.float32:
                d = data.view('<f4')
                return d[0] if len(d) == 1 else d
            if name.value[2] == np.int32:
                d = data.view('<i4')
                return d[0] if len(d) == 1 else d
            if name.value[2] == bool:
                return data.view('<?')[0]
        return getattr(self, name.name.lower())

    def get_buffers(self, binding_point: int, view_as: str = "<f4",start_point: int = 0, size: int = None) -> np.ndarray:
        """
        Retourne un des storage buffers qui contiennent les données des particules.
        Les données que l'on peut avoir sont:
            - POSITIONS_BINDING_POINT = 1
            - PREDICTED_POSITIONS_BINDING_POINT = 2
            - VELOCITIES_BINDING_POINT = 3
            - DENSITIES_BINDING_POINT = 4
            - SPATIAL_INDICES_BINDING_POINT = 5
            - SPATIAL_OFFSETS_BINDING_POINT = 6

        On peut aussi demander un extrait du buffer avec les paramètres start_point et size.
        L'extrait demandé (en octet) avec ces paramètres est [start_point; start_point + size]
        """
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.storage_buffers[binding_point])
        data = None
        if size == None:
            data = glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, start_point, glGetBufferParameteriv(GL_SHADER_STORAGE_BUFFER, GL_BUFFER_SIZE))
        else:
            data = glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, start_point, size)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return data.view(view_as)

    def mounted(self, scene: Scene) -> None:
        """
        Cette fonction est appelée  dans la fonction append_entity de scene.py lorsque 
        le fluide est ajoutée à la scène. Ça sert à automatiquement l'initialiser.
        """
        self.init_fluid_shaders()

        position, scale = self.create_bounding_box(scene)

        initial_positions = self.create_initial_particle_positions(position, scale)

        # Creation des buffers où les données des particules sont stockées
        self.storage_buffers[POSITIONS_BINDING_POINT] = create_buffer(initial_positions, POSITIONS_BINDING_POINT)
        self.storage_buffers[PREDICTED_POSITIONS_BINDING_POINT] = create_buffer(initial_positions, PREDICTED_POSITIONS_BINDING_POINT)
        self.storage_buffers[VELOCITIES_BINDING_POINT] = create_buffer(np.array([0.0] *4* self.particle_count, dtype=np.float32), VELOCITIES_BINDING_POINT)
        self.storage_buffers[DENSITIES_BINDING_POINT] = create_buffer(np.array([0] * self.particle_count, dtype=np.float32), DENSITIES_BINDING_POINT)
        self.storage_buffers[SPATIAL_INDICES_BINDING_POINT] = create_buffer(np.array([0] *4* self.particle_count, dtype=np.int32), SPATIAL_INDICES_BINDING_POINT)
        self.storage_buffers[SPATIAL_OFFSETS_BINDING_POINT] = create_buffer(np.array([0] * self.particle_count, dtype=np.int32), SPATIAL_OFFSETS_BINDING_POINT)
        

        #Création du buffer qui contient les paramètres de la simulation
        # En mémoire les données sont stockés comme ça:
        #              padding
        #                vvv
        # 0.0, 0.0, 0.0, 0.0, # sim_corner_1
        # 0.0, 0.0, 0.0, #sim_corner_2
        # 0.0, # particle_count
        # 0.0, # particle_size
        # 0.0, # smoothing_radius
        # 0.0, # target_density
        # 0.0, # pressure_cst
        # 0.0, # gravity
        # 0.0, # delta
        # 0.0, # collision_damping_factor
        # 0.0, # viscosity_strength 
        # 0.0, # disable_simulation
        dummy_data = np.array([0.0]*17, dtype=np.float32)
        self.params_buffer = create_buffer(dummy_data, PARAMS_BINDING_POINT)
        for param in SimParams:
            val = getattr(self, param.name.lower())
            self.set_simulation_param(param, val)
        
    def draw(self, scene: Scene)-> None:
        """
        Fonction appelée par rendering_engine.py lorsqu'on doit faire le rendu graphique
        du fluide. On 
        """
        PARTICLEAREA_MATERIAL.use()
        PARTICLEAREA_SHADERS.set_mat4x4("model", self.particle_area.get_model_matrix())
        PARTICLEAREA_MESH.draw()

        self.particle_shaders.set_vec3("camPos", scene.get_camera().get_position())
        self.particle_mesh.prepare_to_draw()
        # On dessine des instances de la particule et non n entités disctinctes pour aller beaucoup plus vite
        glDrawArraysInstanced(GL_TRIANGLES, 0, self.particle_mesh.vertex_count ,self.particle_count)

    def update(self, delta:float, force_update = False) -> None:
        """
        Fonction appelée par rendering_engine.py après draw() pour toutes les entités de la scène.
        C'est ici que la position des particules de fluide est mise à jour.
        """
        if self.disable_simulation and not(force_update):
            return 
        
        self.set_simulation_param(SimParams.DELTA, delta)

        self.compute_external.dispatch(self.particle_count)
        self.compute_spatial_hash.dispatch(self.particle_count)
        self.compute_sort.sort_and_calculate_offsets()
        self.compute_density.dispatch(self.particle_count)
        self.compute_pressure.dispatch(self.particle_count)
        self.compute_viscosity.dispatch(self.particle_count)
        self.compute_update_pos.dispatch(self.particle_count)


    def reset_simulation(self, particle_count: int) -> None:
        """
        Reinitialise tout les buffers et permet de changer le nombre de particules de la simulation
        """
        # Stoppe la simulation
        self.set_simulation_param(SimParams.DISABLE_SIMULATION, True)

        #Supprime tout les buffers
        buffers_to_delete = self.storage_buffers[POSITIONS_BINDING_POINT:]
        glDeleteBuffers(len(buffers_to_delete), buffers_to_delete)
        glDeleteBuffers(1, self.params_buffer)

        # Prépare les nouvelles données
        self.particle_count = particle_count
        position = 0.5*(self.simulation_corner_1 + self.simulation_corner_2)
        scale = abs(self.simulation_corner_1 - self.simulation_corner_2)
        initial_positions = self.create_initial_particle_positions(position, scale)

        # Initialisation des storage buffers
        self.storage_buffers[POSITIONS_BINDING_POINT] = create_buffer(initial_positions, POSITIONS_BINDING_POINT)
        self.storage_buffers[PREDICTED_POSITIONS_BINDING_POINT] = create_buffer(initial_positions, PREDICTED_POSITIONS_BINDING_POINT)
        self.storage_buffers[VELOCITIES_BINDING_POINT] = create_buffer(np.array([0.0] *4* self.particle_count, dtype=np.float32), VELOCITIES_BINDING_POINT)
        self.storage_buffers[DENSITIES_BINDING_POINT] = create_buffer(np.array([0] * self.particle_count, dtype=np.float32), DENSITIES_BINDING_POINT)
        self.storage_buffers[SPATIAL_INDICES_BINDING_POINT] = create_buffer(np.array([0] *4* self.particle_count, dtype=np.int32), SPATIAL_INDICES_BINDING_POINT)
        self.storage_buffers[SPATIAL_OFFSETS_BINDING_POINT] = create_buffer(np.array([0] * self.particle_count, dtype=np.int32), SPATIAL_OFFSETS_BINDING_POINT)

        # Initilisation du params buffer
        dummy_data = np.array([0.0]*17, dtype=np.float32)
        self.params_buffer = create_buffer(dummy_data, PARAMS_BINDING_POINT)
        for param in SimParams:
            val = getattr(self, param.name.lower())
            self.set_simulation_param(param, val)


    def destroy(self) -> None:
        """
        Fonction appelée lorsqu'on quitte le programme pour proprement nettoyer
        la mémoire de la carte graphique.
        """
        PARTICLEAREA_MATERIAL.destroy()
        PARTICLEAREA_MESH.destroy()
        PARTICLEAREA_SHADERS.destroy()

        self.particle_mesh.destroy()
        self.particle_shaders.destroy()


class GPUSort:
    def __init__(self, index_buffer_size: int) -> None:
        self.buffer_size = index_buffer_size
        self.sort_shader = ComputeShader(FLUID_SHADER_PATH["GPU_SORT"], init_on_creation=True)
        self.offset_shader = ComputeShader(FLUID_SHADER_PATH["GPU_SORT_OFFSET"], init_on_creation=True)

    def next_power_of_2(self, x :int):
        """
        Retourne la puissance de 2 supérieure à x la plus proche.

        Par exemple si x = 14, la fonction renvoit 16
        """  
        return 1 if x == 0 else 2**(x - 1).bit_length()


    def sort(self):
        """
        Utilise l'algorithme de tri bitonique pour trier la grille de partitionnement de l'espace.
        
        ATTENTION: NE CALCULE PAS spatialOffsets!!! POUR CELA, APPELER sort_and_calculate_offsets()
        
        Pour en savoir plus sur comment la fonction marche, regarder ./docs/OpenGL_3D_Engine_Manual.pdf
        """
        self.sort_shader.set_int("numEntries", self.buffer_size)
        
        num_stages = int(log2(self.next_power_of_2(self.buffer_size)))

        for stage_index in range(num_stages):
            for step_index in range(stage_index + 1):
                # Même chose que 2**(stage_index - step_index) mais beaucoup plus rapide
                groupWidth = 1 << (stage_index - step_index)
                groupHeigth = 2* groupWidth - 1
                self.sort_shader.set_int("groupWidth", groupWidth)
                self.sort_shader.set_int("groupHeight", groupHeigth)
                self.sort_shader.set_int("stepIndex", step_index)

                instances_to_dispatch = self.next_power_of_2(self.buffer_size) // 2
                self.sort_shader.dispatch(instances_to_dispatch)


    def sort_and_calculate_offsets(self):
        """
        Fonction à appeler pour effectuer tout le travail et trier
        spatialIndices et calculer spatialOffsets
        """
        self.sort()

        self.offset_shader.set_int("numEntries", self.buffer_size)
        self.offset_shader.dispatch(self.buffer_size)
