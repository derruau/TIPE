from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.view.scene import Scene

import numpy as np
from enum import Enum
from core.view.scene import Scene 
from core.models.entity import Entity, Eulers
from core.models.material import Material
from core.models.mesh import Mesh
from core.models.shader import Shader, ComputeShader
from OpenGL.GL import *
from math import floor, log2
from OpenGL.arrays.numbers import NumberHandler


PARTICLEAREA_MESH = Mesh("./assets/cube.obj", GL_TRIANGLES, False)
PARTICLEAREA_MATERIAL = Material("./assets/white_borders.png", False)
PARTICLEAREA_SHADERS = Shader("./core/shaders/vertex.glsl", "./core/shaders/fragment.glsl", False)
PARTICLEAREA_LABEL = "PARTICLEAREA"

FLUIDPARTICLE_MESH = Mesh("./assets/sphere.obj", GL_TRIANGLES, False)
FLUIDPARTICLE_SHADERS = Shader("./fluid_simulation/fluid_vertex.glsl", "./fluid_simulation/fluid_fragment.glsl", False)
FLUIDPARTICLE_COMPUTE = ComputeShader("./fluid_simulation/fluid_compute.glsl")
FLUIDPARTICLE_PADDING = 0.01

POSITIONS_BINDING_POINT = 1
PREDICTED_POSITIONS_BINDING_POINT = 2
VELOCITIES_BINDING_POINT = 3
DENSITIES_BINDING_POINT = 4
SPATIAL_INDICES_BINDING_POINT = 5
SPATIAL_OFFSETS_BINDING_POINT = 6
PARAMS_BINDING_POINT = 7

class SimParams(Enum):
    # Le premier composant représent l'offset en mémoire (un float => 4 bytes etc...)
    # Le 2eme composant représente la taille en byte du paramètre
    # Le 3eme argument c'est le type de donnée (pour les listes c'est le type des éléments de la liste)
    SIMULATION_CORNER_1 = (0, 12, np.float32)
    SIMULATION_CORNER_2 = (12, 12, np.float32)
    PARTICLE_COUNT = (24, 4, np.int32)
    PARTICLE_SIZE = (28, 4, np.float32)
    SMOOTHING_RADIUS = (32, 4, np.float32)
    TARGET_DENSITY = (36, 4, np.float32)
    PRESSURE_CST = (40, 4, np.float32)
    GRAVITY = (44, 4, np.float32)
    DELTA = (48, 4, np.float32)
    DISABLE_SIMULATION = (52, 4, bool)



def create_storage_buffer(data: np.ndarray, binding_point: 1):
    buffer = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buffer)
    glNamedBufferStorage(buffer, data.nbytes, data, GL_DYNAMIC_STORAGE_BIT)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding_point, buffer)
    return buffer

def create_uniform_buffer(binding_point: int):
    buffer = glGenBuffers(1)
    glBindBuffer(GL_UNIFORM_BUFFER, buffer)
    glBindBufferBase(GL_UNIFORM_BUFFER, binding_point, buffer)
    return buffer
    


class Fluid(Entity):
    def __init__(
            self, 
            particle_count: int,
            particle_size: float,
            simulation_corner_1: list[float], 
            simulation_corner_2: list[float],
            particle_mesh: Mesh = FLUIDPARTICLE_MESH,
            particle_shaders: Shader = FLUIDPARTICLE_SHADERS
        ) -> None:
        # Setup de l'entitée associé au Fluide
        middle_position = [
            simulation_corner_1[0] + 0.5*(simulation_corner_1[0] - simulation_corner_2[0]),
            simulation_corner_1[1] + 0.5*(simulation_corner_1[1] - simulation_corner_2[1]),
            simulation_corner_1[2] + 0.5*(simulation_corner_1[2] - simulation_corner_2[2])
            ]
        super().__init__(middle_position, Eulers(False, [0, 0, 0]), [1.0, 1.0, 1.0])

        #paramètres de la simulation
        self.simulation_corner_1 = np.array(simulation_corner_1, np.float32)
        self.simulation_corner_2 = np.array(simulation_corner_2, np.float32)
        self.particle_size = particle_size
        self.particle_count = particle_count
        self.smoothing_radius = 3.0
        self.target_density = 4.0
        self.pressure_cst = 3.0
        self.gravity = -10.0
        self.delta = 1.0
        self.disable_simulation = False
        

        self.params_buffer = None
        self.storage_buffers = [0] * 7

        #Différents shaders et objets associés au fluide
        self.particle_mesh: Mesh = particle_mesh
        self.particle_shaders: Shader = particle_shaders

        self.particlearea = None

        self.compute_external = ComputeShader("./fluid_simulation/compute_shaders/external_forces.glsl")
        self.compute_external.init_shader()
        self.compute_update_pos = ComputeShader("./fluid_simulation/compute_shaders/update_pos.glsl")
        self.compute_update_pos.init_shader()


    def init_fluid_shaders(self):
        # Initialisation du fragment et vertex shader
        self.particle_shaders.init_shader()
        self.particle_mesh.init_mesh()
        self.particle_shaders.set_float("particleSize", self.particle_size)

        # Initialisation du compute shader
        FLUIDPARTICLE_COMPUTE.init_shader()
        FLUIDPARTICLE_COMPUTE.set_vec3("sim_corner_1", self.simulation_corner_1)
        FLUIDPARTICLE_COMPUTE.set_vec3("sim_corner_2", self.simulation_corner_2)

        self.compute_external.init_shader()

    def create_bounding_box(self, scene: Scene):
        position = 0.5*(self.simulation_corner_1 + self.simulation_corner_2)
        scale = abs(self.simulation_corner_1 - self.simulation_corner_2)

        self.particlearea = Entity(
            position.tolist(),
            Eulers(False, [0, 0, 0]), 
            scale.tolist(), 
            mesh=PARTICLEAREA_MESH, 
            shaders=PARTICLEAREA_SHADERS, 
            material=PARTICLEAREA_MATERIAL
        )
        self.particlearea.set_label(PARTICLEAREA_LABEL)

        scene.append_entity(self.particlearea)

        return position, scale

    def create_initial_particle_positions(self, position, scale):
        max_particles_x = floor(scale[0]/((self.particle_size + FLUIDPARTICLE_PADDING)))
        max_particles_y = floor(scale[1]/((self.particle_size + FLUIDPARTICLE_PADDING)))
        max_particles_z = floor(scale[2]/((self.particle_size + FLUIDPARTICLE_PADDING)))
        max_particles = max_particles_x * max_particles_y * max_particles_z
        if self.particle_count > max_particles:
            print(f"Trop de particules dans la zone de simulation, le nombre de particule est donc réduit au maximum: {max_particles}")
            self.particle_count = max_particles

        data = []
        for i in range(self.particle_count):
            px = position[0] + scale[0] - self.particle_size - (i % max_particles_x)*(2*self.particle_size + FLUIDPARTICLE_PADDING)
            py = position[1] + scale[1] - self.particle_size - (floor(i/max_particles_x)% max_particles_y) *(2*self.particle_size + FLUIDPARTICLE_PADDING)
            pz = position[2] + scale[2] - self.particle_size - floor(i/(max_particles_x*max_particles_y))*(2*self.particle_size + FLUIDPARTICLE_PADDING)
            data.extend([
                px, py, pz, # Position
                0#, # padding
                # 0,0,0, # vitesse
                # 0 # padding
                ])
        data.pop(-1)
        return np.array(data, dtype=np.float32)

    def set_simulation_param(self, name: SimParams, value: any):
        setattr(self, name.name.lower(), value)
        glBindBuffer(GL_UNIFORM_BUFFER, self.params_buffer)
        glBufferSubData(GL_SHADER_STORAGE_BUFFER, name.value[0], name.value[1], np.array([value], dtype=name.value[2]))
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
    def get_simulation_param(self, name: SimParams) -> any:
        glBindBuffer(GL_UNIFORM_BUFFER, self.params_buffer)
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

    def get_buffers(self, binding_point: int, start_point = 0, size = None):
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.storage_buffers[binding_point])
        data = None
        if size == None:
            data = glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, start_point, glGetBufferParameteriv(GL_SHADER_STORAGE_BUFFER, GL_BUFFER_SIZE))
        else:
            data = glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, start_point, size)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return data.view('<f4')

    def mounted(self, scene: Scene) -> None:
        
        self.init_fluid_shaders()

        position, scale = self.create_bounding_box(scene)

        initial_positions = self.create_initial_particle_positions(position, scale)

        # Creation du buffer positions
        self.storage_buffers[POSITIONS_BINDING_POINT] = create_storage_buffer(initial_positions, POSITIONS_BINDING_POINT)
        # Création du buffer predictedPositions
        self.storage_buffers[PREDICTED_POSITIONS_BINDING_POINT] = create_storage_buffer(initial_positions, PREDICTED_POSITIONS_BINDING_POINT)
        # Création du buffer velocities
        self.storage_buffers[VELOCITIES_BINDING_POINT] = create_storage_buffer(np.array([0.1] *3* self.particle_count, dtype=np.float32), VELOCITIES_BINDING_POINT)
        # Creation du buffer Densities
        self.storage_buffers[DENSITIES_BINDING_POINT] = create_storage_buffer(np.array([0] * self.particle_count, dtype=np.float32), DENSITIES_BINDING_POINT)
        # Création du buffer SpatialIndices
        self.storage_buffers[SPATIAL_INDICES_BINDING_POINT] = create_storage_buffer(np.array([0] * self.particle_count, dtype=np.float32), SPATIAL_INDICES_BINDING_POINT)
        # Création du buffer SpatialOffsets
        self.storage_buffers[SPATIAL_OFFSETS_BINDING_POINT] = create_storage_buffer(np.array([0] * self.particle_count, dtype=np.float32), SPATIAL_OFFSETS_BINDING_POINT)

        # On crée le buffer params
        self.params_buffer = create_uniform_buffer(PARAMS_BINDING_POINT)
        for param in SimParams:
            self.set_simulation_param(param, getattr(self, param.name.lower()))

    def draw(self, scene: Scene):
        PARTICLEAREA_MATERIAL.use()
        PARTICLEAREA_SHADERS.set_mat4x4("model", self.particlearea.get_model_matrix())
        PARTICLEAREA_MESH.draw()

        self.particle_shaders.set_vec3("camPos", scene.get_camera().get_position())
        self.particle_mesh.prepare_to_draw()
        glDrawArraysInstanced(GL_TRIANGLES, 0, self.particle_mesh.vertex_count ,self.particle_count)

    def update(self, delta:float):
        self.compute_update_pos.set_float("delta", delta)
        #self.set_simulation_param(SimParams.DELTA, delta)

        #self.compute_external.dispatch(self.particle_count)
        self.compute_update_pos.dispatch(self.particle_count)
        #print(self.get_simulation_param(SimParams.DELTA))
        #print(self.get_buffers(VELOCITIES_BINDING_POINT))
        #Odre de l'update:

        # - calculer les forces externes
        # - spatialHashKernel
        # - gpuSort
        # - densityKernel
        # - pressureKernel
        # - viscosityKernel
        # - updatePositionsKernel
        #   - positions = positions + speed*delta
        #   - resolveCollisions

    def destroy(self):
        PARTICLEAREA_MATERIAL.destroy()
        PARTICLEAREA_MESH.destroy()
        PARTICLEAREA_SHADERS.destroy()

        self.particle_mesh.destroy()
        self.particle_shaders.destroy()

class GPUSort:
    def __init__(self, index_buffer_size: int) -> None:
        self.buffer_size = index_buffer_size
        self.sort_shader = ComputeShader("./fluid_simulation/gpu_sort.glsl")
        self.offset_shader = ComputeShader("./fluid_simulation/gpu_sort_offset.glsl")

        self.sort_shader.init_shader()
        self.offset_shader.init_shader()

    def next_power_of_2(self, x):  
        return 1 if x == 0 else 2**(x - 1).bit_length()


    def sort(self):
        self.sort_shader.set_int("numEntries", self.buffer_size)
        
        num_stages = log2(self.next_power_of_2(self.buffer_size))

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
        self.sort()

        self.offset_shader.set_int("numEntries", self.buffer_size)
        self.offset_shader.dispatch(self.buffer_size)




