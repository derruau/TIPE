import numpy as np
import glfw
from core.controller.controls import InputScheme
from core.controller.app import App
from core.models.entity import Eulers
from core.view.scene import Scene
from fluid_simulation.fluid import Fluid
from math import sin, cos

PI = 3.14159

WINDOW_HEIGHT = 720
WINDOW_WIDTH = 1280 
WINDOW_TITLE = "Moteur de jeu"

GLOBAL_X = np.array([1,0,0], dtype=np.float32)
GLOBAL_Y = np.array([0,1,0], dtype=np.float32)
GLOBAL_Z = np.array([0,0,1], dtype=np.float32)

FOV_Y = 45.0
ASPECT_RATIO = WINDOW_WIDTH / WINDOW_HEIGHT
NEAR_PLANE_CLIPPING = 0.1
FAR_PLANE_CLIPPING = 1000.0


SPEED = 0.3
CAM_SENSITIVITY = 0.2
VERTICAL_INVERT = -1
HORIZONTAL_INVERT = 1
CAMERA_MOVEMENT_THRESHOLD = 0.00001
DEFAULT_CAMERA_POSITION = [0, 1, -20]
DEFAULT_CAMERA_ANGLE = Eulers(True, [-PI/2, PI/2, 0])
CAMERA_PIVOT_POINT = [0, 0, 0]

FLUID_RENDER_WIDTH = 1280
FLUID_RENDER_HEIGHT = 707

def handle_inputs(window, keys: dict[int, bool], scene :Scene, input_scheme: InputScheme) -> None:
    """
    Est passé en paramètre de la classe App.
    Elle s'occupe de gérer les actions lorsqu'on appuie sur le clavier et lorsqu'on bouge la camera
    """
    handle_keys(window, keys, scene, input_scheme)
    handle_mouse(window, keys, scene, input_scheme)
    #print(scene.get_camera().get_orientation())


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

# C'est moche de faire avec une variable globale mais j'ai un peu la flemme de tout refaire donc ça fera le taf pour l'instant
mouse_pos_when_clicked: tuple[int, int] = (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
def handle_mouse(window, keys: dict[int, bool], scene: Scene, input_scheme: InputScheme) -> None:
    """
    S'occupe de définir les actions à effectuer lorsqu'on bouge la souris et qu'on appuie sur ses boutons.
    """
    global mouse_pos_when_clicked
    camera = scene.get_camera()
    if input_scheme.on_press("mouse_left", keys):
        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_HIDDEN)
        mouse_pos_when_clicked = glfw.get_cursor_pos(window)

    if input_scheme.should_action_happen("click", keys):
        r = camera.get_distance_from(CAMERA_PIVOT_POINT)
        phi, theta, _ = camera.get_orientation().get_degrees()
        x,y = glfw.get_cursor_pos(window)
        d_eulers = CAM_SENSITIVITY * (mouse_pos_when_clicked[0] - x) * GLOBAL_X * HORIZONTAL_INVERT
        d_eulers += CAM_SENSITIVITY * (mouse_pos_when_clicked[1] - y) * GLOBAL_Y * VERTICAL_INVERT

        ntheta = (theta + d_eulers[1])* PI / 180
        nphi = (phi + d_eulers[0]) * PI  / 180

        nx = r * sin(ntheta) * cos(nphi) + CAMERA_PIVOT_POINT[0]
        ny = r * cos(ntheta) + CAMERA_PIVOT_POINT[2]
        nz = r * sin(ntheta) * sin(nphi) + CAMERA_PIVOT_POINT[1]

        camera.set_position(np.array([nx, ny, nz], dtype=np.float32))
        camera.look_at(CAMERA_PIVOT_POINT)
        camera.change_orientation(Eulers(False, d_eulers))
        glfw.set_cursor_pos(window, mouse_pos_when_clicked[0], mouse_pos_when_clicked[1])

    if input_scheme.on_release("mouse_left", keys):
        glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)


def start_game() -> None:
    """
    Fonction principale de ce script. Elle initialise la scène avec les objets et invoque l'application
    """
    input_scheme = InputScheme("./core/controller/controls.cfg")
    app = App(input_scheme, handle_inputs, WINDOW_HEIGHT, WINDOW_WIDTH, WINDOW_TITLE)

    scene = Scene(FOV_Y, ASPECT_RATIO, NEAR_PLANE_CLIPPING, FAR_PLANE_CLIPPING, DEFAULT_CAMERA_POSITION, DEFAULT_CAMERA_ANGLE)
    fluid = Fluid(30000, 0.1, [-2.0, -2.0, -5.0], [2.0, 2.0, 5.0])
    fluid.set_label("Fluide")
    scene.append_entity(fluid)
    
    app.set_scene(scene, render_to_frame_buffer=True, dimensions=(FLUID_RENDER_HEIGHT, FLUID_RENDER_WIDTH))
    app.start(profiling=False)

if __name__ == "__main__":
    start_game()


