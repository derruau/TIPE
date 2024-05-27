from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.view.scene import Scene
    from core.models.mesh import Mesh
    from core.models.material import Material
    from core.models.shader import Shader

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
    def __init__(self, scene: Scene) -> None:
        self.scene = scene

        scene.set_one_time_uniforms()


    def render(self, delta: float) -> None:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        view_matrix = self.scene.get_camera().get_view_matrix()
        self.scene.set_view_matrix(view_matrix)
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
        glFlush()

