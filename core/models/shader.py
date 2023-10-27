import pyrr
import numpy as np
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GL import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, glUseProgram, glGetUniformLocation, glUniformMatrix4fv, glUniform1i
from core.models.material import Material

MAX_CONCURENT_SHADERS = 128


class Shader:
    """
    Un shader individuel
    """
    def __init__(self, vertex_path: str, fragment_path:str) -> None:
        self.shaders = self.createShader(vertex_path, fragment_path)

    def get_shaders(self):
        return self.shaders
    
    def set_uniform(self, name: str, value: any) -> None:
        pass

    def createShader(self, vertexShaderPath: str, fragmentShaderPath: str):
        with open(vertexShaderPath, "r") as f:
            vertex_src = f.readlines()
        with open(fragmentShaderPath, "r") as f:
            fragment_src = f.readlines()

        shader = compileProgram(
            compileShader(vertex_src, GL_VERTEX_SHADER),
            compileShader(fragment_src, GL_FRAGMENT_SHADER)
        )

        return shader

class ShaderManager:
    """
    Une classe qui contient tout les shaders initialisés dans le jeu
    """
    def __init__(self, fov_y:float, aspect_ratio: float, near_clipping_plane: float, far_clipping_plane: float) -> None:
        self.available_shaders_id = {id: True for id in range(MAX_CONCURENT_SHADERS)}
        self.shaders: dict[int: Shader] = {}
        self.fov_y = fov_y,
        self.aspect_ratio = aspect_ratio
        self.near_clipping_plane = near_clipping_plane
        self.far_clipping_plane = far_clipping_plane

    def get_available_id(self) -> int:
        """
        Parcours la liste des ID disponible et renvoie la première disponible
        """
        for k,v in self.available_shaders_id:
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
        return not self.available_shaders_id[id]

    def get_shaders(self) -> dict[int: Shader]:
        """
        Renvoie le dictionnaire contenant touts les shaders, la clé est l'ID du shader et la valeur le en lui même
        """
        return self.shaders
    
    def append_shader(self, shader: Shader) -> int:
        """
        Méthode à utiliser si on veut ajouter un shader à la scène
        """
        id = self.get_available_id()
        if not self.is_id_valid(id):
            return -1
        
        self.available_shaders_id[id] = False
        self.shaders[id] = shader
        return id

    def destroy_shader(self, id) -> bool:
        """
        Méthode à utiliser si on veut supprimer un shader de la scène
        """
        if not self.is_id_in_use(id):
            # Le shader n'existe pas
            return False

        shader: Shader = self.shaders[id]

        
        del shader
        self.available_shaders_id[id] = True
        return True

    def destroy(self) -> bool:
        """
        Méthode à utiliser si on veut supprimer le manager en entier
        """
        r = True
        for id, available in self.available_shaders_id:
            if available == False:
                r = r and self.destroy_shader(id)
        return r

    def set_one_time_uniforms(self) -> None:
        projection = pyrr.matrix44.create_perspective_projection(
            self.fov_y,
            self.aspect_ratio,
            self.near_clipping_plane,
            self.far_clipping_plane,
            np.float32
            )
        for shader in self.get_shaders():
            glUniformMatrix4fv(
                glGetUniformLocation(shader.get_shaders(), "projection"),
                projection
            )
    
    def set_projection_settings(self, fov_y: float, aspect_ratio: float, near_clipping_plane: float, far_clipping_plane: float) -> None:
        self.fov_y = fov_y
        self.aspect_ratio = aspect_ratio
        self.near_clipping_plane = near_clipping_plane
        self.far_clipping_plane = far_clipping_plane
    
    def get_projection_settings(self) -> tuple:
        """
        Retourne le tuple suivant: (fov_y, aspect_ratio, near_clipping_plane, far_clipping_plane)
        """
        return (self.fov_y, self.aspect_ratio, self.near_clipping_plane, self.far_clipping_plane)

    def set_material(self, shader_id: int, material: Material) -> None:
        if not self.is_id_in_use(shader_id):
            raise Exception("L'ID du shader n'est pas valable")
        shader = self.get_shaders()[shader_id]
        glUniform1i(
            glGetUniformLocation(shader, "imageTexture"),
            0
        )
