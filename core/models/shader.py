from __future__ import annotations

from OpenGL.GL.shaders import compileProgram, compileShader
from OpenGL.GL import (
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER, 
    glUseProgram, 
    glGetUniformLocation, 
    glUniform1i,
    glUniform1f,
    glUniform3fv,
    glUniform3iv,
    glUniformMatrix3fv,
    glUniformMatrix4fv,
    glDeleteProgram,
    GL_COMPUTE_SHADER, 
    glDispatchCompute,
    glMemoryBarrier,
    GL_SHADER_STORAGE_BARRIER_BIT,
    GL_ALL_BARRIER_BITS,
    GL_FALSE,
    glGetError
)
from math import ceil

MAX_CONCURENT_SHADERS = 128


class Shader:
    """
    Un shader individuel
    """
    __slots__ = ("_used_by", "init_on_creation", "vertex_path", "fragment_path", "shaders", "uniform_location_cache")

    def __init__(self, vertex_path: str, fragment_path:str, init_on_creation:bool=False) -> None:
        self._used_by = 0 # Le nombre d'entités qui utilisent ce shader
        
        self.vertex_path = vertex_path
        self.fragment_path = fragment_path
        self.uniform_location_cache = {}
        # Définis dans self.init_shader()
        self.shaders = None

        if init_on_creation:
            self.init_shader()

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
    
    def use(self) -> None:
        if self.shaders == None:
            raise Exception("Le compute shader n'a pas été correctement initialisé!")
        glUseProgram(self.shaders)

    def find_uniform(self, name: str) -> int:
        if not (name in self.uniform_location_cache):
            self.uniform_location_cache[name] = glGetUniformLocation(self.shaders, name)
        return self.uniform_location_cache[name]

    def set_int(self, uniform_name: str, value: int) -> None:
        self.use()
        glUniform1i(
            self.find_uniform(uniform_name),
            value
        )

    def set_float(self, uniform_name: str, value: float) -> None:
        self.use()
        glUniform1f(
            self.find_uniform(uniform_name),
            value
        )

    def set_vec3(self, uniform_name: str, value: list[float]) -> None:
        self.use()
        glUniform3fv(
            self.find_uniform(uniform_name),
            1,
            value
        )

    def set_ivec3(self, uniform_name: str, value: list[int]) -> None:
        self.use()
        glUniform3iv(
            self.find_uniform(uniform_name), 
            1,
            value

        )

    def set_mat3x3(self, uniform_name: str, value: list[list[float]]) -> None:
        self.use()
        glUniformMatrix3fv(
            self.find_uniform(uniform_name),
            1, 
            GL_FALSE,
            value
        )

    def set_mat4x4(self, uniform_name: str, value: list[list[float]]) -> None:
        self.use()
        glUniformMatrix4fv(
            self.find_uniform(uniform_name),
            1, 
            GL_FALSE,
            value
        )

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


class ComputeShader:
    def __init__(self, filename: str, init_on_creation: bool=False) -> None:
        self.filename = filename
        self.shader = None
        self.uniform_location_cache = {}
        if init_on_creation:
            self.init_shader()

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

    def find_uniform(self, name: str) -> int:
        if not (name in self.uniform_location_cache):
            self.uniform_location_cache[name] = glGetUniformLocation(self.shader, name)
        return self.uniform_location_cache[name]

    def dispatch(self, n_instances: int):
        self.use()
        #Dans tout les compute shaders, j'ai mis le paramètre:
        # layout(local_size_x = 64, local_size_y = 1, local_size_z = 1) in;
        # Ca veut dire que 1 groupe a une taille locale de 64, donc pour avoir le bon nombre d'invocations
        # du shader on divise le nombre d'instance par 64.
        glDispatchCompute(ceil(n_instances/64), 1, 1)
        glMemoryBarrier(GL_ALL_BARRIER_BITS)

    def set_int(self, uniform_name: str, value: int) -> None:
        self.use()
        glUniform1i(
            self.find_uniform(uniform_name),
            value
        )

    def set_float(self, uniform_name: str, value: float) -> None:
        self.use()
        glUniform1f(
            self.find_uniform(uniform_name),
            value
        )

    def set_vec3(self, uniform_name: str, value: list[float]) -> None:
        self.use()
        glUniform3fv(
            self.find_uniform(uniform_name),
            1,
            value
        )

    def set_ivec3(self, uniform_name: str, value: list[int]) -> None:
        self.use()
        glUniform3iv(
            self.find_uniform(uniform_name), 
            1,
            value

        )

    def set_mat3x3(self, uniform_name: str, value: list[list[float]]) -> None:
        self.use()
        glUniformMatrix3fv(
            self.find_uniform(uniform_name),
            1, 
            GL_FALSE,
            value
        )

    def set_mat4x4(self, uniform_name: str, value: list[list[float]]) -> None:
        self.use()
        glUniformMatrix4fv(
            self.find_uniform(uniform_name),
            1, 
            GL_FALSE,
            value
        )
