# from OpenGL.GL import *
# import ctypes
# import numpy as np
# from OpenGL.GL.shaders import compileProgram, compileShader
# from core.models.mesh import Mesh
# from core.models.material import Material
# import glfw
import numpy as np
import glfw
from core.controller.controls import InputScheme
from core.controller.app import App
from core.controller.manager import Manager
from core.models.entity import Entity, Eulers
from core.models.material import Material, MaterialManager
from core.models.mesh import Mesh, MeshManager
from core.models.shader import Shader, ShaderManager
from core.view.scene import Scene
from core.view.rendering_engine import RenderingEngine

WINDOW_HEIGHT = 480
WINDOW_WIDTH = 680 
WINDOW_TITLE = "Moteur de jeu"

GLOBAL_X = np.array([1,0,0], dtype=np.float32)
GLOBAL_Y = np.array([0,1,0], dtype=np.float32)
GLOBAL_Z = np.array([0,0,1], dtype=np.float32)

FOV_Y = 45.0
ASPECT_RATIO = WINDOW_WIDTH / WINDOW_HEIGHT
NEAR_PLANE_CLIPPING = 0.1
FAR_PLANE_CLIPPING = 50.0


SPEED = 0.3
CAM_SENSITIVITY = 0.2
VERTICAL_INVERT = -1
HORIZONTAL_INVERT = 1

def handle_inputs(window, keys: dict[int, bool], scene :Scene, input_scheme: InputScheme) -> None:
    handle_keys(window, keys, scene, input_scheme)
    handle_mouse(window, keys, scene, input_scheme)

def handle_keys(window, keys: dict[int, bool], scene: Scene, input_scheme: InputScheme) -> None:
    camera = scene.get_camera()
    d_pos = np.array([0, 0, 0], np.float32)
    if input_scheme.should_action_happen("walk_forward", keys):
        d_pos += GLOBAL_X
    if input_scheme.should_action_happen("walk_left", keys):
        d_pos -= GLOBAL_Y
    if input_scheme.should_action_happen("walk_right", keys):
        d_pos += GLOBAL_Y
    if input_scheme.should_action_happen("walk_backward", keys):
        d_pos -= GLOBAL_X

    if input_scheme.should_action_happen("quit_game", keys):
        print("Quitting...")
        glfw.set_window_should_close(window, True)
    
    # Normalisation du vecteur
    l = (d_pos[0]**2 + d_pos[1]**2 + d_pos[2]**2)**(1/2)
    if l > 0.000001:
        d_pos /= l
        d_pos *= SPEED

        camera.move_camera(d_pos)
        print("position: ", camera.position)

def handle_mouse(window, keys: dict[int, bool], scene: Scene, input_scheme: InputScheme) -> None:
    camera = scene.get_camera()
    x,y = glfw.get_cursor_pos(window)
    d_eulers = CAM_SENSITIVITY * (WINDOW_WIDTH / 2 - x) * GLOBAL_Z * HORIZONTAL_INVERT
    d_eulers += CAM_SENSITIVITY * (WINDOW_HEIGHT / 2 - y) * GLOBAL_Y * VERTICAL_INVERT

    camera.change_orientation(Eulers(False, d_eulers.tolist()))
    glfw.set_cursor_pos(window, WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)


def start_game() -> None:
    shader_manager = ShaderManager(FOV_Y, ASPECT_RATIO, NEAR_PLANE_CLIPPING, FAR_PLANE_CLIPPING)
    cube_shader = Shader("./core/shaders/vertex.glsl", "./core/shaders/fragment.glsl", False)
    cube_shader_id = shader_manager.append_shader(cube_shader)

    material_manager = MaterialManager()
    cube_material = Material("./assets/orange_placeholder.png", False)
    cube_material_id = material_manager.append_material(cube_material)

    mesh_manager = MeshManager()
    cube_mesh = Mesh("./assets/cube.obj", False)
    cube_mesh_id = mesh_manager.append_mesh(cube_mesh)
    cube = Entity(
        [1.0, 0.0, 0.0],
        Eulers(False, [0, 0, 0]), 
        [1.0, 1.0, 1.0], 
        mesh_id=cube_mesh_id, 
        shader_id=cube_shader_id, 
        material_id=cube_material_id
        ) 
    
    manager = Manager(shader_manager, material_manager, mesh_manager)
    
    scene = Scene(manager, [0, 0, 0], Eulers(False, [0, 0, 0]))
    scene.append_entity(cube)

    input_scheme = InputScheme("./core/controller/controls.cfg")

    app = App(scene, input_scheme, handle_inputs)

if __name__ == "__main__":
    start_game()


# class App:
#     __slots__ = ("window", "last_time", "frames_rendered", "keys")

#     def __init__(self) -> None:
#         self._init_glfw()

#         self._init_window()

#         self._init_OpenGL()

#         self.mainloop()


#     def _init_glfw(self) -> void:
#         self.last_time = 0
#         self.frames_rendered = 0
#         if not glfw.init():
#             raise RuntimeError("Impossible d'initialiser GLFW.")
        
#         glfw.set_error_callback(self.error_callback)


#     def _init_window(self) -> void:
#         glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
#         glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
#         glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE)
#         self.window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, None, None)

#         if not self.window:
#             raise RuntimeError("Impossible de créer la fenêtre.")
        
#         glfw.make_context_current(self.window)
#         self.keys = {}
#         glfw.set_key_callback(self.window, self.keys_callback)
#         glfw.swap_interval(1)

#     def _init_OpenGL(self):
#         glClearColor(0.1, 0.2, 0.2, 1)
#         glEnable(GL_DEPTH_TEST)
#         glEnable(GL_BLEND)
#         glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


#     def error_callback(self, error: int, description: str):
#         print(f"Code erreur GLFW {error}: {description}")


#     def keys_callback(self, window, key: int, scancode: int, action: int, mods: int):
#         state = False
#         match action:
#             case glfw.PRESS:
#                 state = True
#             case glfw.RELEASE:
#                 state = False
#             case _:
#                 return
#         self.keys[key] = state

#     def calculate_fps(self):
#         current_time = glfw.get_time()
#         delta_t = current_time - self.last_time
#         if delta_t >=1:
#             framerate = max(1, int(self.frames_rendered / delta_t))
#             glfw.set_window_title(self.window, f"Tourne avec {framerate}fps")
#             self.last_time = current_time
#             self.frames_rendered = -1

#         self.frames_rendered += 1

#     def handle_inputs(self):
#         if self.keys.get(glfw.KEY_ESCAPE, False) == True:
#             glfw.set_window_should_close(self.window, True)

#     def handle_mouse(self):
#         pass

#     def mainloop(self):
#         while not glfw.window_should_close(self.window):
#             glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
#             self.handle_inputs()
#             self.handle_mouse()
#             glfw.poll_events()


#             glfw.swap_buffers(self.window)
#             self.calculate_fps()
#         self.quit()


#     def quit(self):
#         glfw.destroy_window(self.window)
#         glfw.terminate()


# class App:
#     def __init__(self) -> None:
#         #====================================#
#         # Initialisation de Pygame et OpenGL #
#         #====================================#
#         pg.init()
#         pg.display.gl_set_attribute(pg.GL_CONTEXT_MAJOR_VERSION, 3)
#         pg.display.gl_set_attribute(pg.GL_CONTEXT_MINOR_VERSION, 3)
#         pg.display.gl_set_attribute(pg.GL_CONTEXT_PROFILE_MASK,
#                                     pg.GL_CONTEXT_PROFILE_CORE)
#         # pg.OPENGL: Pour dire à pygame qu'on utilise OPENGL
#         # pg.DOUBLEBUF: On utilise 2 buffers pour faire le rendu graphique, l'un contient l'image actuellement
#         #  à l'écran et l'autre contient l'image que la carte graphique est en train de dessiner
#         pg.display.set_mode((640,480), pg.OPENGL|pg.DOUBLEBUF)
#         self.clock = pg.time.Clock()
#         glClearColor(0.1, 0.2, 0.2, 1)
#         glEnable(GL_DEPTH_TEST)
#         glEnable(GL_BLEND)
#         glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

#         #self.triangle = Triangle()
#         self.shader = self.createShader("./core/shaders/vertex.glsl", "./core/shaders/fragment.glsl")
#         glUseProgram(self.shader)
#         glUniform1i(glGetUniformLocation(self.shader, "imageTexture"), 0)
#         self.cube = Mesh("./assets/cube.obj")
#         self.placeholder_texture = Material("./assets/orange_placeholder.png")

#         self.mainloop()

#     def mainloop(self):
#         running = True
#         while running:
#             # Gère les évènements pygame
#             for event in pg.event.get():
#                 if (event.type == pg.QUIT):
#                     running = False
            
#             # Mets à jours l'écran chaque frame
#             # COLOR_BUFFER: une liste de la couleur de chaque pixel de l'écran
#             glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

#             glUseProgram(self.shader)
#             self.placeholder_texture.use()
#             self.cube.prepare_to_draw()
#             self.cube.draw()

#             # On switch de Buffer pour instantanément afficher la prochaine image
#             pg.display.flip()

#             # Nombre de FPS
#             self.clock.tick(60)
#         self.quit()

#     def quit(self):
#         self.cube.destroy()
#         self.placeholder_texture.destroy()
#         glDeleteProgram(self.shader)
#         pg.quit()

    # def createShader(self, vertexShaderPath: str, fragmentShaderPath: str):
    #     with open(vertexShaderPath, "r") as f:
    #         vertex_src = f.readlines()
    #     with open(fragmentShaderPath, "r") as f:
    #         fragment_src = f.readlines()

    #     shader = compileProgram(
    #         compileShader(vertex_src, GL_VERTEX_SHADER),
    #         compileShader(fragment_src, GL_FRAGMENT_SHADER)
    #     )

    #     return shader
    


# class Triangle:
#     def __init__(self) -> None:
#         # x, y, z, s, t, n_x, n_y, n_z
#         self.vertices = (
#              0.0,  0.5, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0,
#             -0.5, -0.5, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
#              0.5, -0.5, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0,
#         )
#         # Compatibilité avec OpenGL
#         self.vertices = np.array(self.vertices, dtype=np.float32)

#         self.vertex_count = 3

#         self.vao = glGenVertexArrays(1)
#         glBindVertexArray(self.vao)

#         self.vbo = glGenBuffers(1)
#         glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
#         glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)

#         # Attribu 0: la position
#         glEnableVertexAttribArray(0)
#         glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0)) # Les arguments sont: id, nombre de valeurs, type, normaliser les nombres?, stride, startpoint

#         # Attribu 1: la couleur
#         glEnableVertexAttribArray(1)
#         glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))

#     def arm_for_drawing(self) -> None:
#         """
#             Arm the triangle for drawing.
#         """
#         glBindVertexArray(self.vao)
    
#     def draw(self) -> None:
#         """
#             Draw the triangle.
#         """

#         glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)

#     def destroy(self):
#         glDeleteBuffers(1, (self.vbo,))
#         glDeleteVertexArrays(1, (self.vao,))


# if __name__ == "__main__":
#     app = App()

