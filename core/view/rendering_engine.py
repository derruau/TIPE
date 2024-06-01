from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.view.scene import Scene
    from core.models.shader import Shader
    from core.models.entity import Entity

import numpy as np
from OpenGL.GL import *


FOV_Y = 45
NEAR_CLIPPING_PLANE = 0.1
FAR_CLIPPING_PLANE = 50

class Vertices:
    """
    Une couche d'abstraction pour le format des points passés à OpenGL.
    On a la représentation suivante pour chaque point:
        x, y, z,    s, t,    n_x, n_y, n_z
    où
        - x, y, z: La position du point
        - s, t: La position de la texture sur ce point
        - n_x, n_y, n_z: La direction de la normale en ce point
    """

    __slots__ = ("vertices")

    def __init__(self, vertices: list[float]) -> None:
        """
        Initialisation
        """
        if len(vertices) % 8 == 0:
            self.vertices = np.array(vertices, dtype=np.float32)
            return
        raise TypeError("Le format des points n'est pas le bon, pour chaque point on doit avoir: \n    x, y, z,    s, t,    n_x, n_y, n_z")
    
    def get(self) -> np.ndarray:
        """
        Retourne les points
        """
        return self.vertices
    
    def __repr__(self) -> str:
        string = ""
        for p in range(len(self.vertices) // 8):
            point_string = f"""Point:
            x: {self.vertices[p+0]}, y: {self.vertices[p+1]}, z: {self.vertices[p+2]},
            s: {self.vertices[p+3]}, t: {self.vertices[p+4]},
            n_x: {self.vertices[p+5]}, n_y: {self.vertices[p+6]}, n_z: {self.vertices[p+7]}
"""
            string = string + point_string
        return f"Nombre de points: {len(self.vertices) // 8} \n" + string

class RenderingEngine:
    def __init__(self, scene: Scene, render_to_frame_buffer: bool = False, dimensions: tuple[int, int] = (0, 0)) -> None:
        self.scene = scene
        self.render_to_frame_buffer = render_to_frame_buffer
        self.dimensions = dimensions

        if render_to_frame_buffer:
            self.frame_buffer = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, self.frame_buffer)
            
            # TextureBuffer
            self.frame_buffer_texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.frame_buffer_texture)

            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, dimensions[0], dimensions[1], 0, GL_RGB, GL_UNSIGNED_BYTE, None)
            
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.frame_buffer_texture, 0)

            # Depth et Stencil buffer
            self.depth_stencil_buffer = glGenRenderbuffers(1)
            glBindRenderbuffer(GL_RENDERBUFFER, self.depth_stencil_buffer)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, dimensions[0], dimensions[1])
            glBindRenderbuffer(GL_RENDERBUFFER, 0)

            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, self.depth_stencil_buffer)

            if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                raise "Le framebuffer n'a pas été correctement initialisé"

        scene.set_one_time_uniforms()


    def render(self, delta: float) -> None:
        if self.render_to_frame_buffer:
            glBindFramebuffer(GL_FRAMEBUFFER, self.frame_buffer)
            # Pour que le buffer fasse le rendu de toute la scène.
            glViewport(0, 0, self.dimensions[0], self.dimensions[1])

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        view_matrix = self.scene.get_camera().get_view_matrix()
        self.scene.set_view_matrix(view_matrix)
        entity: Entity
        for entity in self.scene.get_entities().values():
            if entity.has_mesh:
                if entity.has_shaders:
                    shaders: Shader = entity.shaders
                    shaders.set_mat4x4("model", entity.get_model_matrix())
                    if entity.has_material:
                        shaders.set_int("imageTexture", entity.material.get_id())
                        entity.material.use()
            entity.draw(self.scene)
            entity.update(delta)

        #On revient sur le framebuffer de glfw
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def destroy(self) -> None:
        if self.render_to_frame_buffer:
            glDeleteFramebuffers(1, self.frame_buffer)

