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
    if input_scheme.should_action_happen("go_up", keys):
        d_pos += GLOBAL_Z
    if input_scheme.should_action_happen("go_down", keys):
        d_pos -= GLOBAL_Z

    if input_scheme.should_action_happen("quit_game", keys):
        print("Quitting...")
        glfw.set_window_should_close(window, True)
    
    # Normalisation du vecteur
    l = (d_pos[0]**2 + d_pos[1]**2 + d_pos[2]**2)**(1/2)
    if l > 0.000001:
        d_pos /= l
        d_pos *= SPEED

        camera.move_camera(d_pos)

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


