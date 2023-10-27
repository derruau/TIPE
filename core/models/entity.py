"""
Une entité est une classe générale qui contient les paramètres suivant:
- Une position (x, y, z)
- Une rotation (pitch, yaw, roll)

"""
import pyrr
import numpy as np
from typing import Callable, TypedDict, NotRequired
from mesh import Mesh
from material import Material


DEFAULT_ENTITY_LABEL = "Entitée"
# Définition des axes
GLOBAL_X = np.array([1,0,0], dtype=np.float32)
GLOBAL_Y = np.array([0,1,0], dtype=np.float32)
GLOBAL_Z = np.array([0,0,1], dtype=np.float32)


class Eulers:
    """
    Couche d'abstraction sur les angles, qui permet de convertir de degrés à radians.
    """
    def __init__(self, is_rad: bool, eulers: list[float]) -> None:
        """
        is_rad: Est ce que l'angle fourni est en radians?
        eulers: La rotation par rapport à chaque axe (x, y et z)
        """
        self.is_rad = is_rad
        self.eulers = np.array(eulers, np.float32)

    def set_degrees(self, eulers: list[float]) -> None:
        """
        Définir un nouvel angle et le nouvel angle est en degrés
        """
        self.is_rad = False
        self.eulers = np.array(eulers, np.float32)

    def set_rad(self, eulers: list[float]) -> None:
        """
        Définir un nouvel angle et le nouvel angle est en radians
        """
        self.is_rad = True
        self.eulers = np.array(eulers, np.float32)

    def get_degrees(self) -> np.ndarray:
        """
        Retourne l'angle en degrés
        """
        return self.eulers * 57.29578 if self.is_rad else self.eulers
    
    def get_rad(self) -> np.ndarray:
        """
        Retourne l'angle en radians
        """
        return self.eulers * 0.01745 if not self.is_rad else self.eulers


class EntityOptions(TypedDict):
    """
    - mesh: Si une mesh est associée à l'entitée, le préciser ici. 
    - shader_id: Préciser l'ID du shaders à utiliser pour faire le rendu de la mesh si l'entitée en possède une
    - material: Le Material à appliquer à la Mesh. Pour l'instant, le moteur de jeu ne supporte qu'un material par Mesh
    - update: Vous pouvez passer une fonction quelconque qui sera appelée à chaque fois qu'on update le Rendering Engine. Cette fonction a la signature suivante: ```update(delta: float): None``` et `delta` est le temps écoulé entre 2 frames
    """
    mesh: NotRequired[Mesh]
    shader_id: NotRequired[int]
    material: NotRequired[Material]
    update: NotRequired[Callable[[float], None]]


class Entity:
    """
    La classe la plus générale qui définit un objet de la scène. \\
    Fondamentalement, une entitée est une position associé à une rotation et une échelle de taille. \\
    Elle peut cependant contenir des options telle qu'une mesh. Pour voir toutes les options, regarder la classe EntityOptions
    """
    def __init__(
            self,
            position: list[float], 
            rotation: Eulers, 
            scale: list[float],
            **options: EntityOptions
            ) -> None:
        """
        position: En coordonnées cartésiennes dans le format [x, y, z] \\
        rotation: La rotation par rapport à chaque axe EN RADIANS, par exemple rotation[0] est la rotation par rapport à l'axe x, etc... \\
        scale: Le facteur d'échelle par rapport à chaque axe, par exemple scale[0] est l'échelle par rapport à l'axe x, etc... \\
        options: Les arguments optionnels associés à une entitée, par exemple une mesh, des shaders, un material, etc... 
        """
        self.label: str = DEFAULT_ENTITY_LABEL
        self.position = np.array(position, np.float32)
        self.rotation = rotation.get_rad()
        self.scale = np.array(scale, np.float32)

        self.has_mesh = False
        self.has_material = False
        self.has_shaders = False
        self.has_update_func = False
        _keys = options.keys()
        if "mesh" in _keys:
            self.has_mesh = True
            self.mesh = options.get("mesh", None)
            if "shader_id" in _keys:
                self.has_shaders = True
                self.shader_id = options.get("shader_id", None)
            if "meterial" in _keys:
                self.has_material = True
                self.material = options.get("material", None)
        if "update" in _keys:
            self.has_update_func = True
            self.update_func = options.get("update")

    def update(self, delta: float) -> None:
        """
        À préciser pour tout les types d'entités. \\
        delta est le temps écoulé entre 2 frames.
        """
        if self.has_update_func:
            self.update_func(delta)

    def get_model_matrix(self) -> pyrr.Matrix44:
        """
        Renvoie la matrice de transformations M, dite matrice modèle telle que:
        M = T*R*S
        où:
          T est la matrice de translation
          R est la matrice de rotation
          S est la matrice de mise à l'échelle  
        """
        m = pyrr.matrix44.create_from_scale(self.scale, np.float32)
        m = pyrr.matrix44.multiply(
            m,
            pyrr.matrix44.create_from_eulers(self.rotation, np.float32)
        )
        m = pyrr.matrix44.multiply(
            m,
            pyrr.matrix44.create_from_translation(self.position, np.float32)
        )
        return m

    def set_label(self, label: str) -> None:
        self.label = label

    def get_label(self) -> str:
        return self.label
    
    def __repr__(self) -> str:
        return f"{self.label}:\n - Position: {self.position} \n - Rotation: {self.rotation} \n - Echelle: {self.scale}"


class Camera(Entity):
    """
    La caméra est l'entitée depuis laquelle on voit le monde. \\
    On considère que la caméra est montée sur une gimbal, donc son orientation est repérée dans les coordonnées sphériques EN RADIANS (r, theta, phi) où r=1 \\
    On a:
     - phi appartient à l'intervalle [-pi/2, pi/2]
     - theta appartient à l'intervalle [0, 2pi[
    """
    def __init__(self, 
                 position: list[float], 
                 eulers: Eulers, 
                 ) -> None:
        """
        position: la position en coordonnées cartésiennes de la caméra.
        eulers: (theta, phi). en coordonéées sphériques. theta représente l'orientation verticalle, et phi l'orientation horizontale
        """

        super().__init__(position, Eulers(True, [0, 0, 0]), [1.0, 1.0, 1.0])
        self.update()

    def update(self) -> None:
        """
        Met à jour le système de coordonnée local de la caméra
        """
        theta = self.eulers[1]
        phi = self.eulers[2]

        # Le vecteur vers lequel la caméra pointe (convertion des coordonnées sphériques en cartésiennes)
        self.forward = np.array(
            [
                np.sin(theta) * np.cos(phi),
                np.sin(theta) * np.sin(phi),
                np.cos(theta)
            ],
        np.float32)

        # Le vecteur qui pointe vers la droite de la caméra par rapport à sa vue
        self.right = np.cross(self.forward, GLOBAL_Z)

        # Le vecteur qui pointe vers le haut de la caméra par rapport à sa vue
        self.up = np.cross(self.right, self.forward)
    
    def get_view_matrix(self) -> pyrr.Matrix44:
        """
        Retourne la "View Matrix" qui est la matrice de transformation qui simule le mouvement de la caméra dans la scène.
        """
        return pyrr.matrix44.create_look_at(
            self.position,
            self.position + self.forward,
            self.up,
            np.float32
        )

    def move_camera(self, d_pos: list[float]) -> None:
        """
        Bouge la caméra selon ses coordonnées locales. \\
        d_pos est un vecteur où tout les composants sont soit 0, soit 1
        """
        self.position += self.forward*d_pos[0] + self.right*d_pos[1] + self.up*d_pos[2]

    def change_orientation(self, d_eulers: Eulers) -> None:
        """
        Change l'orientation de la caméra tout en gardant les angles dans leurs intervalles respectifs
        """
        self.eulers += d_eulers.get_rad()

        self.eulers[0] %= 6.28319 # 2*PI
        self.eulers[1] = min(1.5, max(-1.5, self.eulers[1])) # 1.5 rad ~ 86°
        self.eulers[2] %= 6.28319 # 2*PI
