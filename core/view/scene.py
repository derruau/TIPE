"""
Une scène contient toutes les entités du niveau, c'est elle qui les gère 
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.models.entity import Entity, Eulers
    from core.controller.manager import Manager
    from core.models.shader import Shader
    from core.models.mesh import Mesh
    from core.models.material import Material

from core.models.entity import Camera

MAX_SCENE_ENTITIES = 128

class Scene:
    def __init__(
            self,
            manager: Manager,
            cam_pos: list[float],
            cam_eulers: Eulers
        ) -> None:
        self.available_entity_id = {id: True for id in range(MAX_SCENE_ENTITIES)}
        self.entities: dict[int: Entity] = {}
        self.manager = manager

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
        if entity.has_mesh:
            self.manager.mesh_manager.add_mesh_use(entity.mesh_id)
        if entity.has_material:
            self.manager.material_manager.add_material_use(entity.material_id)
        if entity.has_shaders:
            self.manager.shader_manager.add_shader_use(entity.shader_id)

        return id

    def destroy_entity(self, id) -> bool:
        """
        Méthode à utiliser si on veut supprimer une entitée de la scène
        """
        if not self.is_id_in_use(id):
            # L'entitée n'existe pas
            return False

        entity: Entity = self.entities[id]
        if entity.has_mesh:
            self.manager.mesh_manager.remove_mesh_use(entity.mesh_id)
        if entity.has_material:
            self.manager.material_manager.remove_material_use(entity.material_id)
        if entity.has_shaders:
            self.manager.shader_manager.remove_shader_use(entity.shader_id)
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
