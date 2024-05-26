"""
Une scène contient toutes les entités du niveau, c'est elle qui les gère 
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.models.entity import Entity, Eulers

import pyrr
import numpy as np
from core.models.entity import Camera
from OpenGL.GL import (
    glGenBuffers,
    glBindBuffer,
    GL_UNIFORM_BUFFER,
    glBufferData,
    GL_STREAM_DRAW,
    glBindBufferBase
)


MAX_SCENE_ENTITIES = 128

class Scene:
    def __init__(
            self,
            fov_y: float,
            aspect_ratio: float,
            near_plane_clipping: float,
            far_plane_clipping :float,
            cam_pos: list[float],
            cam_eulers: Eulers
        ) -> None:
        self.fov_y = fov_y
        self.aspect_ratio = aspect_ratio
        self.near_clipping_plane = near_plane_clipping
        self.far_clipping_plane = far_plane_clipping

        self.available_entity_id = {id: True for id in range(MAX_SCENE_ENTITIES)}
        self.entities: dict[int: Entity] = {}


        cam = Camera(cam_pos, cam_eulers)
        self.cam_id = self.append_entity(cam)

    def get_available_id(self) -> int:
        """
        Parcours la liste des ID disponible et renvoie la première disponible
        """
        for k,v in self.available_entity_id.items():
            if v == True:
                return k
        return -1
    
    def is_id_valid(self, id: int) -> bool:
        """
        Renvoie si l'ID fournie est valide dans le sens où elle n'est pas illégale, pas dans le sens où elle est disponible
        """
        return id >= 0
    
    def is_id_in_use(self, id: int) -> bool:
        """
        Renvoie si l'ID fournie est utilisée par une entitée
        """
        return not self.available_entity_id[id]

    def is_label_used(self, label: str) ->bool:
        for e in self.entities:
            if e.get_label() == label:
                return True
        return False

    def get_entities(self) -> dict[int: Entity]:
        """
        Renvoie le dictionnaire contenant toutes les entités, la clé est l'ID de l'entitée et la valeur l'entitée en elle même
        """
        return self.entities
    
    def append_entity(self, entity: Entity) -> int:
        """
        Méthode à utiliser si on veut ajouter une entitée à la scène
        """
        id = self.get_available_id()
        if not self.is_id_valid(id):
            return -1
        
        self.available_entity_id[id] = False
        self.entities[id] = entity

        init_method = getattr(entity, "mounted", None)
        if callable(init_method):
            entity.mounted(self)

        # if entity.has_mesh:
        #     self.manager.mesh_manager.add_mesh_use(entity.mesh_id)
        # if entity.has_material:
        #     self.manager.material_manager.add_material_use(entity.material_id)
        # if entity.has_shaders:
        #     self.manager.shader_manager.add_shader_use(entity.shader_id)

        return id

    def destroy_entity(self, id) -> bool:
        """
        Méthode à utiliser si on veut supprimer une entitée de la scène
        """
        if not self.is_id_in_use(id):
            # L'entitée n'existe pas
            return False

        entity: Entity = self.entities[id]
        entity.destroy()
        del entity
        self.available_entity_id[id] = True
        
        return True

    def destroy_scene(self) -> bool:
        """
        Méthode à utiliser si on veut supprimer la scène en entier
        """
        r = True
        for id, available in self.available_entity_id.items():
            if available == False:
                r = r and self.destroy_entity(id)
        return r
    
    def update_scene(self, delta: float):
        """
        Met à jour toutes les entités de la scène dans l'ordre croissant de leurs ID.
        """
        for entity in self.get_entities().values():
            entity.update(delta)

    def get_camera(self) -> Camera:
        """
        Retourne la caméra de la scène
        """
        return self.get_entities()[self.cam_id]

    def set_one_time_uniforms(self) -> None:
        """
        Initialise les uniformes à ne mettre qu'une seule fois. Telle que la caméra.
        """
        projection = pyrr.matrix44.create_perspective_projection(
            self.fov_y,
            self.aspect_ratio,
            self.near_clipping_plane,
            self.far_clipping_plane,
            np.float32
            )
        buf = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, buf)
        glBufferData(GL_UNIFORM_BUFFER, projection.nbytes, projection, GL_STREAM_DRAW)
        # Les matrices sont au points de binding 7
        glBindBufferBase(GL_UNIFORM_BUFFER, 0, buf)

    def set_projection_settings(self, fov_y: float, aspect_ratio: float, near_clipping_plane: float, far_clipping_plane: float) -> None:
        """
        Permet de re-paramétrer les paramètres de projection de la camera.
        """
        self.fov_y = fov_y
        self.aspect_ratio = aspect_ratio
        self.near_clipping_plane = near_clipping_plane
        self.far_clipping_plane = far_clipping_plane
    
    def get_projection_settings(self) -> tuple:
        """
        Retourne le tuple suivant: (fov_y, aspect_ratio, near_clipping_plane, far_clipping_plane)
        """
        return (self.fov_y, self.aspect_ratio, self.near_clipping_plane, self.far_clipping_plane)

    def set_view_matrix(self, view_matrix: pyrr.Matrix44) -> None:
        """
        Permet d'update la view_matrix sur tout les shaders du manager.
        """
        projection = pyrr.matrix44.create_perspective_projection(
            self.fov_y,
            self.aspect_ratio,
            self.near_clipping_plane,
            self.far_clipping_plane,
            np.float32
            )
        matrices = np.array([projection, view_matrix], dtype=np.float32)
        buf = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, buf)
        glBufferData(GL_UNIFORM_BUFFER, matrices.nbytes, matrices, GL_STREAM_DRAW)
        # Les matrices projection et view sont au binding 0
        glBindBufferBase(GL_UNIFORM_BUFFER, 0, buf)
