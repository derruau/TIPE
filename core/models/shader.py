from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.models.material import Material

import pyrr
import numpy as np
from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GL import (
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER, 
    glUseProgram, 
    glGetUniformLocation, 
    glUniform1i, 
    glDeleteProgram,
    GL_COMPUTE_SHADER, 
    glGenBuffers, 
    glBindBuffer, 
    glBufferData, 
    glBindBufferBase,
    GL_UNIFORM_BUFFER, 
    GL_STREAM_DRAW
)


MAX_CONCURENT_SHADERS = 128


class Shader:
    """
    Un shader individuel
    """
    __slots__ = ("_used_by", "_keep_in_memory", "vertex_path", "fragment_path", "shaders")

    def __init__(self, vertex_path: str, fragment_path:str, keep_in_memory: bool) -> None:
        """
        Si keep_in_memory = False, dès qu'aucune entitée n'utilise le shader, elle se fait détruire de la mémoire.
        """
        self._used_by = 0 # Le nombre d'entités qui utilisent ce shader
        self._keep_in_memory = keep_in_memory # Si jamais on doit garder la ressource en mémoire même si elle n'est plus utilisée nulle part
        
        self.vertex_path = vertex_path
        self.fragment_path = fragment_path
        # Définis dans self.init_shader()
        self.shaders = None

    def init_shader(self) -> None:
        """
        A appeler une fois le shader créé.
        """
        self.shaders = self.create_shader(self.vertex_path, self.fragment_path)

    def get_shaders(self):
        """
        Retourne l'objet shader.
        """
        return self.shaders
    
    def set_uniform(self, name: str, type: str, value: any) -> None:
        """
        TODO: A implémenter
        """
        pass

    def destroy(self) -> None:
        """
        Détruit le shader dans la VRAM.
        """
        glDeleteProgram(self.shaders)

    def create_shader(self, vertexShaderPath: str, fragmentShaderPath: str):
        """
        Permet d'initialiser un vertex_shader et un fragment_shader pour les combiner en un objet shader.
        """
        with open(vertexShaderPath, "r") as f:
            vertex_src = f.readlines()
        with open(fragmentShaderPath, "r") as f:
            fragment_src = f.readlines()

        shader = compileProgram(
            compileShader(vertex_src, GL_VERTEX_SHADER),
            compileShader(fragment_src, GL_FRAGMENT_SHADER)
        )

        return shader

    def save_shader_to_cache(self, path: str) -> bool:
        """
        TODO: A implémenter
        """
        pass

    def load_shader_from_cache(self, path: str) -> bool:
        """
        TODO: A implémenter
        """
        pass

    def __repr__(self) -> str:
        """
        La représentation du shader lorsqu'on le print.
        """
        return f'Shader: vertex_path: {self.vertex_path}, fragment_path: {self.fragment_path}'


class ShaderManager:
    """
    Une classe qui contient tout les shaders initialisés dans le jeu
    """
    __slots__ = ("available_shaders_id", "shaders", "fov_y", "aspect_ratio", "near_clipping_plane", "far_clipping_plane")

    def __init__(
            self, 
            fov_y:float, 
            aspect_ratio: float, 
            near_clipping_plane: float, 
            far_clipping_plane: float
            ) -> None:
        """
        Le ShaderManager s'occupe de gérer les différents shaders en mémoire.
        """
        # Chaque nombre représente le nombre de shaders qui ont cette ID qui actuellement en cours d'utilisation
        self.available_shaders_id = {id: True for id in range(MAX_CONCURENT_SHADERS)}
        self.shaders: dict[int: Shader] = {}
        self.fov_y = fov_y
        self.aspect_ratio = aspect_ratio
        self.near_clipping_plane = near_clipping_plane
        self.far_clipping_plane = far_clipping_plane

    def get_available_id(self) -> int:
        """
        Parcours la liste des ID disponible et renvoie la première disponible
        """
        for k,v in self.available_shaders_id.items():
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

    def remove_shader(self, id: int) -> bool:
        """
        Méthode à utiliser si on veut supprimer un shader du Manager
        """
        if not self.is_id_in_use(id):
            # Le shader n'existe pas
            return False

        shader: Shader = self.shaders[id]

        
        del shader
        self.available_shaders_id[id] = True
        return True

    def clean(self, force: bool = False) -> None:
        """
        Supprime de la mémoire les shaders qui ne sont plus utilisés par une entitée ET qui ont le paramètre _keep_in_memory = False

        Où sinon si force = True, tout les shaders sont supprimés de la mémoire, même si _keep_in_memory = True
        """
        for id, available in self.available_shaders_id.items():
            if available:
                continue
            shader: Shader = self.get_shaders()[id]
            if ((shader._used_by == 0) and (shader._keep_in_memory == False)) or force:
                shader.destroy()
                self.remove_shader(id)

    def destroy(self) -> bool:
        """
        Méthode à utiliser si on veut supprimer le manager en entier ainsi que tout les shaders qui lui sont associés
        """
        self.clean(True)

    def add_shader_use(self, shader_id: int) -> None:
        """
        Préviens le Manager qu'une entité utilise le shader d'ID shader_id
        """
        shader:Shader = self.get_shaders()[shader_id]
        shader._used_by += 1

    def remove_shader_use(self, shader_id: int) -> None:
        """
        Préviens le Manager qu'une entité n'utilise plus le shader d'ID shader_id
        """
        shader: Shader = self.get_shaders()[shader_id]
        shader._used_by -= 1

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

    def set_material(self, shader_id: int, material_id: Material) -> None:
        """
        Donne à un shader le material à utiliser comme texture.
        """
        if not self.is_id_in_use(shader_id):
            raise Exception("L'ID du shader n'est pas valable")
        shader: Shader = self.get_shaders()[shader_id]
        glUseProgram(shader.get_shaders())
        glUniform1i(
            glGetUniformLocation(shader.get_shaders(), "imageTexture"),
            material_id
        )

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
        # for shader in self.get_shaders().values():
        #     glUseProgram(shader.get_shaders())
        #     glUniformMatrix4fv(
        #         glGetUniformLocation(shader.get_shaders(), "view"),
        #         1,
        #         GL_FALSE,
        #         view_matrix
        #     )


class ComputeShader:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.shader = None

    def init_shader(self) -> None:
        with open(self.filename, "r") as f:
            compute_shader = f.readlines()
        self.shader = compileProgram(compileShader(compute_shader, GL_COMPUTE_SHADER))

    def get(self):
        return self.shader
    
    def use(self):
        if self.shader == None:
            raise Exception(f"Le compute shader {self.filename} n'a pas été correctement initialisé!")
        glUseProgram(self.shader)
