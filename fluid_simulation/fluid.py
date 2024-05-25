from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.view.scene import Scene
    from core.models.material import MaterialManager
    from core.models.mesh import MeshManager
    from core.models.shader import ShaderManager

import numpy as np
from core.view.scene import Scene 
from core.models.entity import Entity, Eulers
from core.models.material import Material
from core.models.mesh import Mesh
from core.models.shader import Shader, ComputeShader
from OpenGL.GL import *
from math import floor, log2

PARTICLEAREA_MESH = Mesh("./assets/cube.obj", GL_TRIANGLES, False)
PARTICLEAREA_MATERIAL = Material("./assets/white_borders.png", False)
PARTICLEAREA_SHADERS = Shader("./core/shaders/vertex.glsl", "./core/shaders/fragment.glsl", False)
PARTICLEAREA_LABEL = "PARTICLEAREA"

FLUIDPARTICLE_MESH = Mesh("./assets/sphere.obj", GL_TRIANGLES, False)
FLUIDPARTICLE_SHADERS = Shader("./fluid_simulation/fluid_vertex.glsl", "./fluid_simulation/fluid_fragment.glsl", False)
FLUIDPARTICLE_COMPUTE = ComputeShader("./fluid_simulation/fluid_compute.glsl")
FLUIDPARTICLE_PADDING = 0.01

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
        self.is_fluid = True
        
        # Les 2 buffers qui contiennent les positions et vitesses des particules
        self.particles_data_buffers = None
        self.draw_buffer_index = 0

        self.particle_count = particle_count
        self.particle_size = particle_size
        self.particle_mesh: Mesh = particle_mesh
        self.particle_shaders: Shader = particle_shaders

        self.simulation_corner_1 = np.array(simulation_corner_1, np.float32)
        self.simulation_corner_2 = np.array(simulation_corner_2, np.float32)

        self.particlearea = None
        self.particlearea_initialized = False

    def create_buffer(self, data: np.ndarray, binding_point: 1):
        buffer = glGenBuffers(1)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, buffer)
        glNamedBufferStorage(buffer, data.nbytes, data, GL_DYNAMIC_STORAGE_BIT)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding_point, buffer)
        return buffer
    
    def dispatch_compute_shader(self):
        pass

    def init_fluid_shaders(self):
        # Initialisation du fragment et vertex shader
        self.particle_shaders.init_shader()
        self.particle_mesh.init_mesh()
        glUseProgram(self.particle_shaders.get_shaders())
        glUniform1f(
            glGetUniformLocation(self.particle_shaders.get_shaders(), "particleSize"),
            self.particle_size
        )
        
        # Initialisation du compute shader
        FLUIDPARTICLE_COMPUTE.init_shader()
        FLUIDPARTICLE_COMPUTE.use()
        glUniform3fv(
            glGetUniformLocation(FLUIDPARTICLE_COMPUTE.get(), "sim_corner_1"), 1,
            self.simulation_corner_1.tolist()
        )
        glUniform3fv(
            glGetUniformLocation(FLUIDPARTICLE_COMPUTE.get(), "sim_corner_2"), 1 ,
            self.simulation_corner_2.tolist()
        )

    def create_bounding_box(self, mesh_manager: MeshManager, material_manager: MaterialManager, shader_manager: ShaderManager):
        position = 0.5*(self.simulation_corner_1 + self.simulation_corner_2)
        scale = abs(self.simulation_corner_1 - self.simulation_corner_2)

        particlearea_mesh_id = mesh_manager.append_mesh(PARTICLEAREA_MESH)
        mesh_manager.get_meshes()[particlearea_mesh_id].init_mesh()
        particlearea_shader_id = shader_manager.append_shader(PARTICLEAREA_SHADERS)
        shader_manager.get_shaders()[particlearea_shader_id].init_shader()
        particlearea_material_id = material_manager.append_material(PARTICLEAREA_MATERIAL)
        material_manager.get_materials()[particlearea_material_id].init_material(particlearea_material_id)

        self.particlearea = Entity(
            position.tolist(),
            Eulers(False, [0, 0, 0]), 
            scale.tolist(), 
            mesh_id=particlearea_mesh_id, 
            shader_id=particlearea_shader_id, 
            material_id=particlearea_material_id
        )
        self.particlearea.set_label(PARTICLEAREA_LABEL)
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

    def init_fluid(self, mesh_manager: MeshManager, material_manager: MaterialManager, shader_manager: ShaderManager) -> None:
        self.init_fluid_shaders()

        position, scale = self.create_bounding_box(mesh_manager, material_manager, shader_manager)

        initial_positions = self.create_initial_particle_positions(position, scale)

        # Creation du buffer positions
        self.create_buffer(initial_positions, 1)
        # Création du buffer predictedPositions
        self.create_buffer(initial_positions, 2)
        # Création du buffer velocities
        self.create_buffer(np.array([0] * self.particle_count, dtype=np.float32), 3)
        # Creation du buffer Densities
        self.create_buffer(np.array([0] * self.particle_count, dtype=np.float32), 4)
        # Création du buffer SpatialIndices
        self.create_buffer(np.array([0] * self.particle_count, dtype=np.float32), 5)
        # Création du buffer SpatialOffsets
        self.create_buffer(np.array([0] * self.particle_count, dtype=np.float32), 6)

    def draw(self, scene: Scene):
        particlearea_material: Material = scene.manager.material_manager.get_materials()[self.particlearea.material_id]
        particlearea_material.use(self.particlearea.material_id)
        particlearea_shader: Shader = scene.manager.shader_manager.get_shaders()[self.particlearea.shader_id]
        glUseProgram(particlearea_shader.get_shaders())
        glUniformMatrix4fv(
                        glGetUniformLocation(particlearea_shader.get_shaders(), "model"),
                        1,
                        GL_FALSE,
                        self.particlearea.get_model_matrix()
        )
        particlearea_mesh: Mesh = scene.manager.mesh_manager.get_meshes()[self.particlearea.mesh_id]
        particlearea_mesh.prepare_to_draw()
        particlearea_mesh.draw()

        glUseProgram(self.particle_shaders.get_shaders())
        glUniform3fv(
            glGetUniformLocation(self.particle_shaders.get_shaders(), "camPos"), 1,
            scene.get_camera().get_position()
        )
        self.particle_mesh.prepare_to_draw()
        glDrawArraysInstanced(GL_TRIANGLES, 0, self.particle_mesh.vertex_count ,self.particle_count)

    def switch_draw_buffer(self):
        # Bitwise xor
        self.draw_buffer_index = self.draw_buffer_index ^ 1

    def update(self, delta:float):
        FLUIDPARTICLE_COMPUTE.use()
        glUniform1f(
            glGetUniformLocation(FLUIDPARTICLE_COMPUTE.get(), "delta"),
            delta
        )
        glDispatchCompute(self.particle_count, 1, 1)
        glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT)


class GPUSort:
    def __init__(self, index_buffer_size: int) -> None:
        self.buffer_size = index_buffer_size
        self.sort_shader = ComputeShader("./fluid_simulation/gpu_sort.glsl")
        self.offset_shader = ComputeShader("./fluid_simulation/gpu_sort_offset.glsl")

        self.sort_shader.init_shader()
        self.offset_shader.init_shader()

        self.numEntries_location = glGetUniformLocation(self.sort_shader.get(), "numEntries")
        self.groupWidth_location = glGetUniformLocation(self.sort_shader.get(), "groupWidth")
        self.groupHeight_location = glGetUniformLocation(self.sort_shader.get(), "groupHeight")
        self.stepIndex_location = glGetUniformLocation(self.sort_shader.get(), "stepIndex")

    def next_power_of_2(self, x):  
        return 1 if x == 0 else 2**(x - 1).bit_length()


    def sort(self):
        self.sort_shader.use()
        glUniform1i(self.numEntries_location, self.buffer_size)
        
        num_stages = log2(self.next_power_of_2(self.buffer_size))

        for stage_index in range(num_stages):
            for step_index in range(stage_index + 1):
                # Même chose que 2**(stage_index - step_index) mais beaucoup plus rapide
                groupWidth = 1 << (stage_index - step_index)
                groupHeigth = 2* groupWidth - 1
                glUniform1i(self.groupWidth_location, groupWidth)
                glUniform1i(self.groupHeight_location, groupHeigth)
                glUniform1i(self.stepIndex_location, step_index)

                glDispatchCompute(self.next_power_of_2(self.buffer_size) // 2, 1, 1)                


    def sort_and_calculate_offsets(self):
        self.sort()

        self.offset_shader.use()
        glUniform1i(
            glGetUniformLocation(self.offset_shader.get(), "numEntries"), self.buffer_size
        )

        glDispatchCompute(self.buffer_size, 1, 1)




