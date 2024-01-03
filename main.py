import numpy as np
import glfw
from OpenGL.GL import GL_POINTS, GL_TRIANGLES, GL_QUADS, GL_LINE
from core.controller.controls import InputScheme
from core.controller.app import App
from core.controller.manager import Manager
from core.models.entity import Entity, Eulers
from core.models.material import Material, MaterialManager
from core.models.mesh import Mesh, MeshManager
from core.models.shader import Shader, ShaderManager
from core.view.scene import Scene

PI = 3.14159

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
HORIZONTAL_INVERT = -1
CAMERA_MOVEMENT_THRESHOLD = 0.00001
DEFAULT_CAMERA_POSITION = [0, 1, -10]
DEFAULT_CAMERA_ANGLE = Eulers(False, [PI/2, PI/2, 0])

def handle_inputs(window, keys: dict[int, bool], scene :Scene, input_scheme: InputScheme) -> None:
    """
    Est passé en paramètre de la classe App.
    Elle s'occupe de gérer les actions lorsqu'on appuie sur le clavier et lorsqu'on bouge la camera
    """
    handle_keys(window, keys, scene, input_scheme)
    handle_mouse(window, keys, scene, input_scheme)

def handle_keys(window, keys: dict[int, bool], scene: Scene, input_scheme: InputScheme) -> None:
    """
    S'occupe de définir les actions à effectuer lorsqu'on appuie sur une quelconque touche du clavier.
    Il est recommandé de ne pas traiter les boutons de la souris dans cette fonctions pour des raisons de clareté du code.
    """
    camera = scene.get_camera()
    d_pos = np.array([0, 0, 0], np.float32)
    d_abs_pos = np.array([0,0,0], np.float32)
    if input_scheme.should_action_happen("walk_forward", keys):
        d_pos += GLOBAL_X
    if input_scheme.should_action_happen("walk_left", keys):
        d_pos -= GLOBAL_Y
    if input_scheme.should_action_happen("walk_right", keys):
        d_pos += GLOBAL_Y
    if input_scheme.should_action_happen("walk_backward", keys):
        d_pos -= GLOBAL_X
    if input_scheme.should_action_happen("go_up", keys):
        d_abs_pos += GLOBAL_Y
    if input_scheme.should_action_happen("go_down", keys):
        d_abs_pos -= GLOBAL_Y

    if input_scheme.should_action_happen("quit_game", keys):
        print("Quitting...")
        glfw.set_window_should_close(window, True)

    if input_scheme.should_action_happen("reset", keys):
        camera.set_position(np.array(DEFAULT_CAMERA_POSITION, np.float32))
        camera.set_orientation(DEFAULT_CAMERA_ANGLE)
    
    # Normalisation du vecteur
    l = (d_pos[0]**2 + d_pos[1]**2 + d_pos[2]**2)**(1/2)
    l_abs = (d_abs_pos[0]**2 + d_abs_pos[1]**2 + d_abs_pos[2]**2)**(1/2)
    if l > CAMERA_MOVEMENT_THRESHOLD:
        d_pos /= l
        d_pos *= SPEED
    if l_abs > CAMERA_MOVEMENT_THRESHOLD:
        d_abs_pos /= l_abs
        d_abs_pos *= SPEED

    camera.move_camera(d_pos, d_abs_pos)

def handle_mouse(window, keys: dict[int, bool], scene: Scene, input_scheme: InputScheme) -> None:
    """
    S'occupe de définir les actions à effectuer lorsqu'on bouge la souris et qu'on appuie sur ses boutons.
    """
    camera = scene.get_camera()
    x,y = glfw.get_cursor_pos(window)
    d_eulers = CAM_SENSITIVITY * (WINDOW_WIDTH / 2 - x) * GLOBAL_X * HORIZONTAL_INVERT
    d_eulers += CAM_SENSITIVITY * (WINDOW_HEIGHT / 2 - y) * GLOBAL_Y * VERTICAL_INVERT

    camera.change_orientation(Eulers(False, d_eulers.tolist()))
    glfw.set_cursor_pos(window, WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)


def start_game() -> None:
    """
    Fonction principale de ce script. Elle initialise la scène avec les objets et invoque l'application
    """
    shader_manager = ShaderManager(FOV_Y, ASPECT_RATIO, NEAR_PLANE_CLIPPING, FAR_PLANE_CLIPPING)
    cube_shader = Shader("./core/shaders/vertex.glsl", "./core/shaders/fragment.glsl", False)
    cube_shader_id = shader_manager.append_shader(cube_shader)
    arrow_shader = Shader("./core/shaders/arrow_vertex.glsl", "./core/shaders/arrow_fragment.glsl", False)
    arrow_shader_id = shader_manager.append_shader(arrow_shader)

    material_manager = MaterialManager()
    cube_material = Material("./assets/white_borders.png", False)
    cube_material_id = material_manager.append_material(cube_material)
    orange_placeholder = Material("./assets/orange_placeholder.png", False)
    orange_placeholder_id = material_manager.append_material(orange_placeholder)

    mesh_manager = MeshManager()
    cube_mesh = Mesh("./assets/cube.obj", GL_TRIANGLES,False)
    cube_mesh_id = mesh_manager.append_mesh(cube_mesh)
    arrow_mesh = Mesh("./assets/arrow.obj", GL_TRIANGLES, False)
    arrow_mesh_id = mesh_manager.append_mesh(arrow_mesh)
    plane_mesh = Mesh("./assets/plane.obj", GL_TRIANGLES, False)
    plane_mesh_id = mesh_manager.append_mesh(plane_mesh)

    cube = Entity(
        [0.0, 1.0, 0.0],
        Eulers(False, [0, 0, 0]), 
        [1.0, 1.0, 1.0], 
        mesh_id=cube_mesh_id, 
        shader_id=cube_shader_id, 
        material_id=cube_material_id
        )
    
    arrow = Entity(
        GLOBAL_Y,
        Eulers(False, [0, 0,0]),
        [1.0, 1.0, 1.0],
        mesh_id = arrow_mesh_id,
        shader_id = arrow_shader_id
    )

    plane = Entity(
        [0, 0, 0],
        Eulers(False, [0, 0, 0]),
        [100, 1, 100],
        mesh_id = plane_mesh_id,
        shader_id = cube_shader_id,
        material_id = orange_placeholder_id
    )
    
    manager = Manager(shader_manager, material_manager, mesh_manager)
    
    scene = Scene(manager, DEFAULT_CAMERA_POSITION, DEFAULT_CAMERA_ANGLE)
    scene.append_entity(cube)
    scene.append_entity(arrow)
    scene.append_entity(plane)

    input_scheme = InputScheme("./core/controller/controls.cfg")

    app = App(scene, input_scheme, handle_inputs, WINDOW_HEIGHT, WINDOW_WIDTH, WINDOW_TITLE)

if __name__ == "__main__":
    start_game()


