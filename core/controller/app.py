"""
App est le fichier maître du moteur de jeu, c'est par lui que tout commence
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.view.scene import Scene
    from core.controller.controls import InputScheme

from OpenGL.GL import *
import glfw
import numpy as np
from OpenGL.GL.shaders import compileProgram, compileShader
from core.view.rendering_engine import RenderingEngine

WINDOW_HEIGHT = 480
WINDOW_WIDTH = 640 
WINDOW_TITLE = "Moteur de jeu"


class App:
    #__slots__ = ("window", "last_time", "frames_rendered", "keys", "handle_inputs", "input_scheme")

    def __init__(self, scene: Scene, input_scheme: InputScheme, handle_inputs: callable) -> None:
        """
        Création d'une fenêtre et lancement du moteur de jeu. \\
        scène: passer la scène que l'application doit afficher. \\
        input_scheme: l'objet contenant le schéma des inputs \\
        handle_inputs: une fonction ayant la signature ```handle_keys(window, keys: dict[int: bool], scene: Scene): None``` qui s'occupe de voir comment
        """
        self._init_glfw()

        self._init_window(input_scheme, handle_inputs)

        self._init_OpenGL()

        self.scene = scene
        self.scene.manager.init_managers()
        self.rendering_engine = RenderingEngine(self.scene)

        self.mainloop()

    def _init_glfw(self) -> void:
        self.last_time = 0
        self.delta = 0
        self.frames_rendered = 0
        if not glfw.init():
            raise RuntimeError("Impossible d'initialiser GLFW.")
        
        glfw.set_error_callback(self.error_callback)

    def _init_window(self, input_scheme: InputScheme, handle_inputs: callable) -> void:
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, None, None)

        if not self.window:
            raise RuntimeError("Impossible de créer la fenêtre.")
        
        glfw.make_context_current(self.window)
        self.keys:dict[int: bool] = {}
        self.input_scheme = input_scheme
        self.handle_inputs = handle_inputs
        glfw.set_key_callback(self.window, self.keys_callback)
        glfw.swap_interval(1)
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_HIDDEN)

    def _init_OpenGL(self):
        glClearColor(0.1, 0.2, 0.2, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def error_callback(self, error: int, description: str):
        print(f"Code erreur GLFW {error}: {description}")

    def keys_callback(self, window, key: int, scancode: int, action: int, mods: int):
        key_name = glfw.get_key_name(key, scancode)
        if key_name == None:
            # TODO: À refaire impérativement, ça marche même pas!!
            # C'est horrible à lire et je DOIS refaire ça plus proprement
            # Un rappel de pk je fais ça: j'arrive pas à faire correspondre l'argument key de cette fonction et getattr(glfw, 'KEY_{key}')
            if key == glfw.KEY_LEFT_SHIFT:
                self.keys["left_shift"] = True if action == glfw.PRESS else False
            if key == glfw.KEY_SPACE:
                self.keys["space"] = True if action == glfw.PRESS else False
            elif mods == glfw.MOD_ALT:
                self.keys["alt"] = True if action == glfw.PRESS else False
            elif mods == glfw.MOD_CAPS_LOCK:
                self.keys["caps_lock"] = True if action == glfw.PRESS else False
            elif mods == glfw.MOD_CONTROL:
                self.keys["ctrl"] = True if action == glfw.PRESS else False
            elif mods == glfw.MOD_NUM_LOCK:
                self.keys["num_lock"] = True if action == glfw.PRESS else False
            elif mods == glfw.MOD_SUPER:
                self.keys["super"] = True if action == glfw.PRESS else False
            return
        match action:
            case glfw.PRESS:        
                self.keys[key_name] = True
            case glfw.RELEASE:
                self.keys[key_name] = False

    def calculate_fps(self):
        current_time = glfw.get_time()
        delta_t = current_time - self.last_time
        self.delta = delta_t
        if delta_t >=1:
            framerate = max(1, int(self.frames_rendered / delta_t))
            glfw.set_window_title(self.window, f"Tourne avec {framerate}fps")
            self.last_time = current_time
            self.frames_rendered = -1

        self.frames_rendered += 1

    def mainloop(self):
        while not glfw.window_should_close(self.window):
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.handle_inputs(self.window, self.keys, self.scene, self.input_scheme)
            glfw.poll_events()

            self.rendering_engine.render(self.delta)

            glfw.swap_buffers(self.window)
            self.calculate_fps()
        self.quit()

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

    def quit(self):
        glfw.destroy_window(self.window)
        glfw.terminate()
        self.scene.manager.destroy()
        self.scene.destroy_scene()
