"""
On appelle material une image projetée sur un triangle qui compose une mesh
"""
from OpenGL.GL import *
from PIL import Image

MAX_CONCURENT_MATERIALS = 128

class Material:
    __slots__ = ("_used_by", "_keep_in_memory", "material_path", "texture")

    def __init__(self, material_path: str, keep_in_memory: bool) -> None:
        """
        Initialise la classe. 
        Si keep_in_memory = True, garde la texture en mémoire même si aucune mesh ne l'utilise
        """
        self._used_by = 0
        self._keep_in_memory = keep_in_memory

        self.material_path = material_path
        # Définit dans self.init_material()
        self.texture = None
        

    def init_material(self, id: int):
        """
        Ouvre le fichier qui contient le material et l'initialise en VRAM
        """
        # Dans le vocabulaire OpenGL, une texture est un conteneur qui contient 1 ou plusieurs images au même format
        self.texture = glGenTextures(1)
        # GL_TEXTURE_2D est une collection d'images à 2 dimensions
        # C'est à dire qu'elles ont une hauteur et une largeur non nulle, mais une profondeur nulle
        glActiveTexture(GL_TEXTURE0 + id)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        # Répéter la texture sur l'axe s (axe des abscisses) si la face est trop grande
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        # Répéter la texture sur l'axe t (axe des ordonnées) si la face est trop grande
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # Paramètres esthétiques pour que la texture ait un meilleur rendu 
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        with Image.open(self.material_path, mode = "r") as image:
            image_width, image_height = image.size
            image = image.convert("RGBA")
            image_data = bytes(image.tobytes())
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        glGenerateMipmap(GL_TEXTURE_2D)

    def use(self, id:int) -> None:
        """
        Permet de dire à OpenGL quelle texture utiliser lorsqu'il dessine une mesh
        À utiliser avant mesh.prepare_to_draw()
        """
        glActiveTexture(GL_TEXTURE0 + id)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def destroy(self) -> None:
        """
        Libère la mémoire utilisée par la texture
        """
        glDeleteTextures(1, (self.texture,))

class MaterialManager:
    __slots__ = ("available_material_id", "materials")

    def __init__(self) -> None:
        # Chaque nombre représente le nombre de materials qui ont cette ID qui actuellement en cours d'utilisation
        self.available_material_id = {id: True for id in range(MAX_CONCURENT_MATERIALS)}
        self.materials: dict[int: Material] = {}

    def get_available_id(self) -> int:
        """
        Parcours la liste des ID disponible et renvoie la première disponible
        """
        for k,v in self.available_material_id.items():
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
        Renvoie si l'ID fournie est utilisée par un shader
        """
        return not self.available_material_id[id]

    def get_materials(self) -> dict[int: Material]:
        """
        Renvoie le dictionnaire contenant touts les shaders, la clé est l'ID du shader et la valeur le en lui même
        """
        return self.materials
    
    def append_material(self, material: Material) -> int:
        """
        Méthode à utiliser si on veut ajouter un shader à la scène
        """
        id = self.get_available_id()
        if not self.is_id_valid(id):
            return -1
        
        self.available_material_id[id] = False
        self.materials[id] = material
        return id

    def remove_material(self, id: int) -> bool:
        """
        Méthode à utiliser si on veut supprimer un material du Manager
        """
        if not self.is_id_in_use(id):
            # Le material n'existe pas
            return False

        material: Material = self.materials[id]

        
        del material
        self.available_material_id[id] = True
        return True

    def clean(self, force: bool = False) -> None:
        """
        Supprime de la mémoire les materials qui ne sont plus utilisés par une entitée ET qui ont le paramètre _keep_in_memory = False

        Où sinon si force = True, tout les shaders sont supprimés de la mémoire, même si _keep_in_memory = True
        """
        for id, available in self.available_material_id.items():
            if available:
                continue
            material: Material = self.get_materials()[id]
            if ((material._used_by == 0) and (material._keep_in_memory == False)) or force:
                material.destroy()
                self.remove_material(id)

    def destroy(self) -> bool:
        """
        Méthode à utiliser si on veut supprimer le manager en entier ainsi que tout les shaders qui lui sont associés
        """
        self.clean(True)

    def add_material_use(self, material_id: int) -> None:
        """
        Préviens le Manager qu'une entité utilise le material d'ID material_id
        """
        material:Material = self.get_materials()[material_id]
        material._used_by += 1

    def remove_material_use(self, material_id: int) -> None:
        """
        Préviens le Manager qu'une entité n'utilise plus le material d'ID material_id
        """
        material: Material = self.get_materials()[material_id]
        material._used_by -= 1


