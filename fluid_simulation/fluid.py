from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.view.scene import Scene
    from core.shaders import ShaderManager
    from core.controller.manager import Manager
    from core.models.material import MaterialManager
    from core.models.mesh import MeshManager
    from core.models.shader import ShaderManager

import numpy as np
import ctypes
from core.view.scene import Scene 
from core.models.entity import Entity, EntityOptions, Eulers
from core.models.material import Material
from core.models.mesh import Mesh, load_mesh
from core.models.shader import Shader, ComputeShader
from OpenGL.GL import *
from math import floor

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


    def init_fluid(self, mesh_manager: MeshManager, material_manager: MaterialManager, shader_manager: ShaderManager) -> None:
        # Fragment et vertex shader
        self.particle_shaders.init_shader()
        self.particle_mesh.init_mesh()
        glUseProgram(self.particle_shaders.get_shaders())
        glUniform1f(
            glGetUniformLocation(self.particle_shaders.get_shaders(), "particleSize"),
            self.particle_size
        )
        
        # Compute shader
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

        # Cube qui sert de rebord à la simulation
        particlearea_position = 0.5*(self.simulation_corner_1 + self.simulation_corner_2)
        particlearea_scale = abs(self.simulation_corner_1 - self.simulation_corner_2)

        particlearea_mesh_id = mesh_manager.append_mesh(PARTICLEAREA_MESH)
        mesh_manager.get_meshes()[particlearea_mesh_id].init_mesh()
        particlearea_shader_id = shader_manager.append_shader(PARTICLEAREA_SHADERS)
        shader_manager.get_shaders()[particlearea_shader_id].init_shader()
        particlearea_material_id = material_manager.append_material(PARTICLEAREA_MATERIAL)
        material_manager.get_materials()[particlearea_material_id].init_material(particlearea_material_id)

        self.particlearea = Entity(
            particlearea_position.tolist(),
            Eulers(False, [0, 0, 0]), 
            particlearea_scale.tolist(), 
            mesh_id=particlearea_mesh_id, 
            shader_id=particlearea_shader_id, 
            material_id=particlearea_material_id
        )
        self.particlearea.set_label(PARTICLEAREA_LABEL)

        max_particles_x = floor(particlearea_scale[0]/((self.particle_size + FLUIDPARTICLE_PADDING)))
        max_particles_y = floor(particlearea_scale[1]/((self.particle_size + FLUIDPARTICLE_PADDING)))
        max_particles_z = floor(particlearea_scale[2]/((self.particle_size + FLUIDPARTICLE_PADDING)))
        max_particles = max_particles_x * max_particles_y * max_particles_z
        if self.particle_count > max_particles:
            print(f"Trop de particules dans la zone de simulation, le nombre de particule est donc réduit au maximum: {max_particles}")
            self.particle_count = max_particles

        data = []
        for i in range(self.particle_count):
            px = particlearea_position[0] + particlearea_scale[0] - self.particle_size - (i % max_particles_x)*(2*self.particle_size + FLUIDPARTICLE_PADDING)
            py = particlearea_position[1] + particlearea_scale[1] - self.particle_size - (floor(i/max_particles_x)% max_particles_y) *(2*self.particle_size + FLUIDPARTICLE_PADDING)
            pz = particlearea_position[2] + particlearea_scale[2] - self.particle_size - floor(i/(max_particles_x*max_particles_y))*(2*self.particle_size + FLUIDPARTICLE_PADDING)
            data.extend([
                px, py, pz, # Position
                0, # padding
                0,0,0, # vitesse
                0 # padding
                ])
        data.pop(-1)
        initial_fluid_data = np.array(data, dtype=np.float32)

        self.particles_data_buffers = glGenBuffers(2)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.particles_data_buffers[0])
        glNamedBufferStorage(self.particles_data_buffers[0], initial_fluid_data.nbytes, initial_fluid_data, GL_DYNAMIC_STORAGE_BIT)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, self.particles_data_buffers[0])
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, self.particles_data_buffers[1])
        glNamedBufferStorage(self.particles_data_buffers[1], initial_fluid_data.nbytes, initial_fluid_data, GL_DYNAMIC_STORAGE_BIT)
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, self.particles_data_buffers[1])
    

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
