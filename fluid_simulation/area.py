from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.view.scene import Scene
    from core.shaders import ShaderManager
    from core.controller.manager import Manager

import numpy as np
import ctypes
from core.models.entity import Entity, EntityOptions, Eulers
from core.models.material import Material
from core.models.mesh import Mesh, load_mesh
from core.models.shader import Shader, ComputeShader
from OpenGL.GL import *

PARTICLEAREA_MESH = Mesh("./assets/cube.obj", GL_TRIANGLES, False)
PARTICLEAREA_MATERIAL = Material("./assets/white_borders.png", False)
PARTICLEAREA_SHADERS = Shader("./core/shaders/vertex.glsl", "./core/shaders/fragment.glsl", False)

FLUIDPARTICLE_MESH = Mesh("./assets/sphere.obj", GL_TRIANGLES, False)
FLUIDPARTICLE_SHADERS = Shader("./fluid_simulation/fluid_vertex.glsl", "./fluid_simulation/fluid_fragment.glsl", False)
FLUIDPARTICLE_COMPUTE = ComputeShader("./fluid_simulation/fluid_compute.glsl")

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

        self.simulation_corner_1 = simulation_corner_1
        self.simulation_corner_2 = simulation_corner_2

    def init_fluid(self) -> None:
        FLUIDPARTICLE_COMPUTE.init_shader()
        self.particle_shaders.init_shader()
        self.particle_mesh.init_mesh()
        glUseProgram(self.particle_shaders.get_shaders())
        glUniform1f(
            glGetUniformLocation(self.particle_shaders.get_shaders(), "particleSize"),
            self.particle_size
        )

        initial_fluid_data = [
            self.simulation_corner_1[0] + 0.5*(self.simulation_corner_1[0] - self.simulation_corner_2[0]), # position axe x
            self.simulation_corner_1[1] + 0.5*(self.simulation_corner_1[1] - self.simulation_corner_2[1]), # position axe y
            self.simulation_corner_1[2] + 0.5*(self.simulation_corner_1[2] - self.simulation_corner_2[2]), # position axe z
            0, # vitesse axe x
            0, # vitesse axe y
            0, # vitesse axe z
        ]
        initial_fluid_data = np.array([
            0, 0, 0, # Position
            0, # Dummy, pour l'alignement avec la struct dans fluid_vertex.glsl
            0, 0, 0, # Vitesse
            0, # Dummy, pour l'alignement avec la struct dans fluid_vertex.glsl
            1, 0, 0,
            0, # Dummy, pour l'alignement avec la struct dans fluid_vertex.glsl
            0, 0, 0
        ], dtype=np.float32)
        #initial_fluid_data = np.array(initial_fluid_data, np.float32)
        #self.particles_data_buffers = np.empty(2, dtype=np.uint32)
        self.particles_data_buffers = glGenBuffers(2)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.particles_data_buffers[0])
        glNamedBufferStorage(self.particles_data_buffers[0], initial_fluid_data.nbytes, initial_fluid_data, GL_DYNAMIC_STORAGE_BIT)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, self.particles_data_buffers[0])
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.particles_data_buffers[1])
        glNamedBufferStorage(self.particles_data_buffers[1], initial_fluid_data.nbytes, initial_fluid_data, GL_DYNAMIC_STORAGE_BIT)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, self.particles_data_buffers[1])
    
    def draw(self, scene: Scene):
        glUseProgram(self.particle_shaders.get_shaders())
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
