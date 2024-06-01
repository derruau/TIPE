from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.models.mesh import Mesh
    from core.models.material import Material
    from core.models.shader import Shader
"""
Une entité est une classe générale qui contient les paramètres suivant:
- Une position (x, y, z)
- Une rotation (pitch, yaw, roll)

"""
import pyrr
import numpy as np
from typing import Callable, TypedDict, NotRequired
from math import sqrt

PI = 3.14159

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
        return (self.eulers * 0.01745).copy() if not self.is_rad else self.eulers.copy()

    def __repr__(self) -> str:
        if self.is_rad:
            return f"rotation par rapport à \n - x: {self.get_rad()[0]} rad \n - y: {self.get_rad()[1]} rad \n - z: {self.get_rad()[2]} rad"
        return f"rotation par rapport à \n - x: {self.get_degrees()[0]} ° \n - y: {self.get_degrees()[1]} ° \n - z: {self.get_degrees()[2]} °"


class EntityOptions(TypedDict):
    """
    - mesh_id: Préciser l'ID de la mesh associée à l'entitée, si l'entitée en possède. 
    - shader_id: Préciser l'ID du shaders à utiliser pour faire le rendu de la mesh si l'entitée en possède une
    - material_id: Préciser l'ID du Material à appliquer à la Mesh. Pour l'instant, le moteur de jeu ne supporte qu'un material par Mesh
    - update: Vous pouvez passer une fonction quelconque qui sera appelée à chaque fois qu'on update le Rendering Engine. Cette fonction a la signature suivante: ```update(delta: float): None``` et `delta` est le temps écoulé entre 2 frames
    """
    mesh_id: NotRequired[int]
    shader_id: NotRequired[int]
    material_d: NotRequired[int]
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
        rotation: La rotation par rapport à chaque axe. 
        scale: Le facteur d'échelle par rapport à chaque axe, par exemple scale[0] est l'échelle par rapport à l'axe x, etc... \\
        options: Les arguments optionnels associés à une entitée, par exemple une mesh, des shaders, un material, etc... 
        """
        self.is_fluid = False
        self.label: str = DEFAULT_ENTITY_LABEL
        self.position = np.array(position, np.float32)
        self.eulers = rotation.get_rad()
        self.scale = np.array(scale, np.float32)

        self.has_mesh = False
        self.has_material = False
        self.has_shaders = False
        self.has_update_func = False
        _keys = options.keys()
        if "mesh" in _keys:
            self.has_mesh = True
            self.mesh: Mesh= options.get("mesh", None)
            self.mesh.init_mesh()
            if "shaders" in _keys:
                self.has_shaders = True
                self.shaders: Shader= options.get("shaders", None)
                self.shaders.init_shader()
            if "material" in _keys:
                self.has_material = True
                self.material: Material = options.get("material", None)
                self.material.init_material()
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
            pyrr.matrix44.create_from_eulers(self.eulers, np.float32)
        )
        m = pyrr.matrix44.multiply(
            m,
            pyrr.matrix44.create_from_translation(self.position, np.float32)
        )
        return m

    def set_label(self, label: str) -> None:
        """
        Donne un nom à l'entitée. Utile lorsqu'on veut débugger.
        """
        self.label = label

    def get_label(self) -> str:
        """
        Renvoie le nom de l'entitée. Si elle n'en a pas, renvoie None.
        """
        return self.label
    
    def __repr__(self) -> str:
        """
        Comment apparait l'entitée lorsqu'on la print.
        """
        return f"{self.label}:\n - Position: {self.position} \n - Rotation: {self.eulers} \n - Echelle: {self.scale}"

    def set_scale(self, scale: list[float]) -> None:
        self.scale = np.array(scale, np.float32)

    def get_scale(self) -> list[float]:
        return self.scale.tolist()

    def set_position(self, position: list[float]) -> None:
        self.position = np.array(position, np.float32)

    def get_position(self) -> list[float]:
        return self.position.tolist()

    def set_orientation(self, eulers: Eulers) -> None:
        self.eulers = eulers

    def get_orientation(self) -> Eulers:
        return self.eulers
    
    def get_distance_from(self, point: list[float]):
        pos: list[float] = self.get_position()
        v = [pos[0] - point[0], pos[1] - point[1], pos[2] - point[2]]
        return sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    
    def destroy(self) -> None:
        if self.has_mesh:
            self.mesh.destroy()
        if self.has_material:
            self.material.destroy()
        if self.has_shaders:
            self.shaders.destroy()

    def draw(self, scene):
        """
        On passe la scène car dès fois on en a besoin pour certains objets (notamment le fluide)
        """
        if self.has_mesh:
            self.mesh.draw()

    def __repr__(self) -> str:
        return self.get_label()


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

        super().__init__(position, eulers, [1.0, 1.0, 1.0])
        
        self.update(0)
        self.set_label("Camera")

    def update(self, delta: float) -> None:
        """
        Met à jour le système de coordonnée local de la caméra
        """
        phi = self.eulers[0]
        theta = self.eulers[1]
        # Le vecteur vers lequel la caméra pointe (convertion des coordonnées sphériques en cartésiennes)
        self.forward = np.array(
            [
                np.sin(theta) * np.cos(phi),
                np.cos(theta),
                np.sin(theta) * np.sin(phi),
            ],
        np.float32)
        # Je sais pas trop pk j'ai besoin de faire un *-1 mais sans ça le vecteur forward est dans la mauvaise direction
        # Ça a changé quand j'ai implémenté la rotation autour d'un point fixe, avant ça marchait bien sans...
        self.forward *= -1

        # Le vecteur qui pointe vers la droite de la caméra par rapport à sa vue
        self.right = np.cross(self.forward, GLOBAL_Y)

        # Le vecteur qui pointe vers le haut de la caméra par rapport à sa vue
        self.up = np.cross(self.right, self.forward)
    
    def get_view_matrix(self) -> pyrr.Matrix44:
        """
        Retourne la "View Matrix" qui est la matrice de transformation qui simule le mouvement de la caméra dans la scène.
        """
        view_matrix = pyrr.matrix44.create_look_at(
            self.position,
            self.position + self.forward,
            self.up,
            np.float32
        )
        return view_matrix

    def move_camera(
            self, 
            d_pos: np.ndarray, 
            d_abs_pos: np.ndarray = np.array([0,0,0], np.float32)
            ) -> None:
        """
        Bouge la caméra selon ses coordonnées locales. \\
        d_pos est un vecteur où tout les composants sont soit 0, soit 1
        """
        self.position += self.forward*d_pos[0] \
            + self.right*d_pos[1] \
            + self.up*d_pos[2] \
            + d_abs_pos

    def change_orientation(self, d_eulers: Eulers) -> None:
        """
        Change l'orientation de la caméra tout en gardant les angles dans leurs intervalles respectifs
        """
        self.eulers += d_eulers.get_rad()

        self.eulers[0] %= 2*PI
        self.eulers[1] = min(3, max(0.1, self.eulers[1])) # 0 ça représente le haut et 3 ~ pi le bas
        self.eulers[2] %= 2*PI

    def look_at(self, point: list[float]):
        v = np.array(point) - self.get_position()
        l = sqrt(v[0]*v[0]+ v[1]*v[1] + v[2]*v[2])
        v = v/l
        self.forward = v

    def set_position(self, position: np.ndarray) -> None:
        self.position = position

    def set_orientation(self, euleurs: Eulers) -> None:
        self.eulers = euleurs.get_rad()

    def get_orientation(self) -> Eulers:
        return Eulers(True, self.eulers)
    
    def get_position(self) -> np.ndarray:
        return self.position

