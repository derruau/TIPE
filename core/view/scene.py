"""
Une scène contient toutes les entités du niveau, c'est elle qui les gère 
"""
from core.models.entity import Camera, Entity, Eulers
from core.models.shader import ShaderManager
from OpenGL.GL import glDeleteProgram


MAX_SCENE_ENTITIES = 128

class Scene:
    def __init__(self, shader_manager:ShaderManager,cam_pos: float[list], cam_eulers: Eulers) -> None:
        self.available_entity_id = {id: True for id in range(MAX_SCENE_ENTITIES)}
        self.entities: dict[int: Entity] = {}
        self.shader_manager = shader_manager

        cam = Camera(cam_pos, cam_eulers)
        self.cam_id = self.append_entity(cam)

    def get_available_id(self) -> int:
        """
        Parcours la liste des ID disponible et renvoie la première disponible
        """
        for k,v in self.available_entity_id:
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
        return id

    def destroy_entity(self, id) -> bool:
        """
        Méthode à utiliser si on veut supprimer une entitée de la scène
        """
        if not self.is_id_in_use(id):
            # L'entitée n'existe pas
            return False

        entity: Entity = self.entities[id]
        # Pas une bonne solution car si je delete un material utilisé par un autre objet dans la scene par exemple, c'est la grosse merde
        # Peut être adopter le système du manager pour tout les scripts du dossier model??
        # On a déjà scène qui est un EntityManager et ShaderManager 
        # if entity.has_mesh:
        #     entity.mesh.destroy()
        # if entity.has_material:
        #     entity.material.destroy()
        # if entity.has_shaders:
        #     self.shader_manager.destroy_shader(entity.shader_id)
        
        del entity
        self.available_entity_id[id] = True
        return True

    def destroy_scene(self) -> bool:
        """
        Méthode à utiliser si on veut supprimer la scène en entier
        """
        r = True
        for id, available in self.available_entity_id:
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
