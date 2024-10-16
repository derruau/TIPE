"""
App est le fichier maître du moteur de jeu, c'est par lui que tout commence
"""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.view.scene import Scene
    from core.controller.controls import InputScheme
    from fluid_simulation.fluid import Fluid

from OpenGL.GL import *
import glfw
import imgui
from numpy import array, float32
from imgui.integrations.glfw import GlfwRenderer
from core.view.rendering_engine import RenderingEngine
from fluid_simulation.fluid import SimParams

PROFILING_PATH = "./profiling/"
MAX_PROFILED_FRAMES_PER_SESSION = 1000

PARAMETERS_MENU_WIDTH = 500

class App:
    __slots__ = ("window", "last_time", "frames_rendered", "keys", "handle_inputs", "input_scheme", "scene", "rendering_engine", "delta", "last_frame", "impl", "width", "height")

    def __init__(
            self, 
            input_scheme: InputScheme, 
            handle_inputs: callable,
            window_height: int,
            window_width: int,
            window_title = str
            ) -> None:
        """
        Création d'une fenêtre et lancement du moteur de jeu. \\
        scène: passer la scène que l'application doit afficher. \\
        input_scheme: l'objet contenant le schéma des inputs \\
        handle_inputs: une fonction ayant la signature ```handle_keys(window, keys: dict[int: bool], scene: Scene): None``` qui s'occupe de voir comment
        """
        self._init_glfw()

        self._init_window(input_scheme, handle_inputs, window_height, window_width, window_title)

        self._init_OpenGL()


    def _init_glfw(self) -> None:
        """
        Initialisation de glfw, ainsi que certaines variables de la classe.
        Cette fonction ne spawn pas la fenêtre!!
        """
        self.last_time = 0
        self.last_frame = 0
        self.delta = 0
        self.frames_rendered = 0
        if not glfw.init():
            raise RuntimeError("Impossible d'initialiser GLFW.")
        
        glfw.set_error_callback(self.error_callback)
        

    def _init_window(
            self, 
            input_scheme: InputScheme, 
            handle_inputs: callable,
            window_height: int,
            window_width: int,
            window_title
            ) -> None:
        """
        Initialise la fenêtre et la config pour les inputs.
        """
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.OPENGL_PROFILE,glfw.OPENGL_CORE_PROFILE)
        self.window = glfw.create_window(window_width, window_height, window_title, None, None)

        if not self.window:
            raise RuntimeError("Impossible de créer la fenêtre.")
        
        glfw.make_context_current(self.window)
        self.keys:dict[int: bool] = {}
        self.input_scheme = input_scheme
        self.handle_inputs = handle_inputs
        glfw.set_key_callback(self.window, self.keys_callback)
        glfw.set_mouse_button_callback(self.window, self.mouse_callback)
        glfw.swap_interval(1)
        #glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_HIDDEN)

        #Initilalisation de ImGUI
        imgui.create_context()
        self.impl = GlfwRenderer(self.window, attach_callbacks=True)

    def _init_OpenGL(self):
        """
        Initialisation d'OpenGL, c'est ici qu'on set la couleur de background.
        """
        glClearColor(0.1, 0.2, 0.2, 1)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        print("Version d'OpenGL:", glGetString(GL_VERSION).decode())

    def error_callback(self, error: int, description: str):
        """
        La fonction qui print les erreurs de GLFW
        """
        print(f"Code erreur GLFW {error}: {description}")

    def keys_callback(self, window, key: int, scancode: int, action: int, mods: int):
        """
        S'occupe de construire le dictionnaire self.keys qui contient les clés
        sur lesquelles on appuie à une frame donnée.

        Bug: GLFW a un bug avec le nom des clés, alors cette fonction est très mal implémentée.
        """
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

    def mouse_callback(self, window, button: int, action: int, mods: int):
        btn = "mouse_left" if button == 0 else "mouse_right"
        match action:
            case glfw.PRESS:
                self.keys[btn] = True
            case glfw.RELEASE:
                self.keys[btn] = False

    def calculate_fps(self):
        """
        Calcule  et actualise le nombre de FPS toute les secondes.
        """
        current_time = glfw.get_time()
        delta_t = current_time - self.last_time
        self.delta = current_time - self.last_frame
        if delta_t >=1:
            framerate = max(1, int(self.frames_rendered / delta_t))
            glfw.set_window_title(self.window, f"Tourne avec {framerate}fps")
            self.last_time = current_time
            self.frames_rendered = -1

        self.frames_rendered += 1
        self.last_frame = current_time

    def set_scene(self, scene: Scene, render_to_frame_buffer: bool= False, dimensions: tuple[int, int] = (0, 0)) -> None:
        self.scene = scene
        self.rendering_engine = RenderingEngine(self.scene, render_to_frame_buffer, dimensions)

    def render_process(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        io = imgui.get_io()
        glfw.poll_events()
        self.impl.process_inputs()

        # start new frame context
        imgui.new_frame()
        
        size = glfw.get_window_size(self.window)
        imgui.set_next_window_size(PARAMETERS_MENU_WIDTH, size[1])
        imgui.set_next_window_position(size[0] - PARAMETERS_MENU_WIDTH, 0)
        imgui.begin("Paramètres",
                     True,
                     flags=imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE,
        )
        fluid: Fluid = self.scene.get_entities_from_label("Fluide")[0]
        
        disable_simulation_clicked, fluid.disable_simulation = imgui.checkbox("Désactiver la simulation", fluid.disable_simulation)
        if disable_simulation_clicked:
            fluid.set_simulation_param(SimParams.DISABLE_SIMULATION, fluid.disable_simulation)

        if imgui.button("Avancer d'une frame"):
            fluid.set_simulation_param(SimParams.DISABLE_SIMULATION, True)
            fluid.update(self.delta, force_update=True)

        if imgui.button("Reset la simulation"):
            fluid.set_simulation_param(SimParams.DISABLE_SIMULATION, True)
            fluid.reset_simulation(fluid.particle_count)

        if fluid.disable_simulation:
            particle_count_changed, fluid.particle_count = imgui.input_int("Nombre de particules", fluid.particle_count)
            if particle_count_changed:
                fluid.reset_simulation(fluid.particle_count)

        particle_size_changed, fluid.particle_size = imgui.slider_float(
            "Taille des particules", fluid.particle_size,
            min_value=0.0, max_value=1.0,
            format="%.2f"
        )
        if particle_size_changed:
            fluid.set_simulation_param(SimParams.PARTICLE_SIZE, fluid.particle_size)

        smoothing_radius_changed, fluid.smoothing_radius = imgui.slider_float(
            "Rayon d'influence des particules", fluid.smoothing_radius,
            min_value=0.0, max_value=2.0,
            format="%.2f"
        )
        if smoothing_radius_changed:
            fluid.set_simulation_param(SimParams.SMOOTHING_RADIUS, fluid.smoothing_radius)

        target_density_changed, fluid.target_density = imgui.slider_float(
            "Densitée Désirée", fluid.target_density,
            min_value=0.0, max_value=100.0,
            format="%.2f"
        )
        if target_density_changed:
            fluid.set_simulation_param(SimParams.TARGET_DENSITY, fluid.target_density)

        pressure_cst_changed, fluid.pressure_cst = imgui.slider_float(
            "Constante des pressions", fluid.pressure_cst,
            min_value=-100.0, max_value=1000.0,
            format="%.2f"
        )
        if pressure_cst_changed:
            fluid.set_simulation_param(SimParams.PRESSURE_CST, fluid.pressure_cst)

        gravity_changed, fluid.gravity = imgui.slider_float(
            "Gravitée", fluid.gravity,
            min_value=-100.0, max_value=100.0,
            format="%.2f"
        )
        if gravity_changed:
            fluid.set_simulation_param(SimParams.GRAVITY, fluid.gravity)

        collision_factor_changed, fluid.collision_damping_factor = imgui.slider_float(
            "Facteur de collisions", fluid.collision_damping_factor,
            min_value=0.0, max_value=1.0,
            format="%.2f"
        )
        if collision_factor_changed:
            fluid.set_simulation_param(SimParams.COLLISION_DAMPING_FACTOR, fluid.collision_damping_factor)

        viscosity_strength_changed, fluid.viscosity_strength = imgui.slider_float(
            "Viscositée", fluid.viscosity_strength,
            min_value=0.0, max_value=1.0,
            format="%.3f"
        )
        if viscosity_strength_changed:
            fluid.set_simulation_param(SimParams.VISCOSITY_STRENGTH, fluid.viscosity_strength)

        scale_changed, fluid.scale = imgui.slider_float3(
            "Taille de la simulation", *fluid.scale,
            min_value=0.0, max_value=5.0,
            format="%.1f"
        )
        if scale_changed:
            fluid.particle_area.set_scale((2*array(fluid.scale)).tolist())
            fluid.set_simulation_param(SimParams.SIMULATION_CORNER_1, array(fluid.scale, dtype=float32))
            fluid.set_simulation_param(SimParams.SIMULATION_CORNER_2, -1*array(fluid.scale, dtype=float32))

        imgui.end()


        imgui.set_next_window_size(size[0] - PARAMETERS_MENU_WIDTH, size[1])
        imgui.set_next_window_position(0, 0)
        imgui.begin("Rendu",
                     True,
                     flags=imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE,
        )
        if imgui.is_window_hovered():
            self.input_scheme.begin_input_frame()
            self.handle_inputs(self.window, self.keys, self.scene, self.input_scheme)
            self.input_scheme.end_input_frame()

        window_content_size = imgui.get_window_size()
        aspect_ratio = self.height / self.width
        center_pos = imgui.Vec2(0, (window_content_size.y - window_content_size.x*aspect_ratio) * 0.5)
        imgui.set_cursor_pos(center_pos)
        imgui.image(self.rendering_engine.frame_buffer_texture, window_content_size.x, window_content_size.x*aspect_ratio, uv0=(1, 1), uv1=(0,0))
        imgui.end()

        imgui.render()
        imgui.end_frame()
        self.impl.render(imgui.get_draw_data())


        self.rendering_engine.render(self.delta)

        glFinish()
        glfw.swap_buffers(self.window)
        self.calculate_fps()


    def start(self, profiling: bool=False):
        """
        La boucle principale du jeu. Elle invoque le rendering engine et events claviers et calcule les FPS
        """
        if profiling:
            import cProfile
            import pstats
            from pathlib import Path
            from os import listdir

            Path(PROFILING_PATH).mkdir(parents=True, exist_ok=True)
            profile_id = len(listdir(PROFILING_PATH))
            profile_directory = PROFILING_PATH + f"profile-{profile_id:0>4}/"
            Path(profile_directory).mkdir(parents=True, exist_ok=True)

        self.width, self.height = glfw.get_window_size(self.window)
        glfw.set_cursor_pos(self.window, self.width / 2, self.height / 2)
        while not glfw.window_should_close(self.window):
            if profiling:
                with cProfile.Profile() as profile:
                    self.render_process()
                results = pstats.Stats(profile)
                results.sort_stats(pstats.SortKey.TIME)
                if self.frames_rendered < MAX_PROFILED_FRAMES_PER_SESSION:
                    results.dump_stats(profile_directory + f"frame-{self.frames_rendered}.profile")
            else:
                self.render_process()
        self.quit()

    def quit(self):
        """
        Quitte le jeu, à invoquer avant de quitter l'appli.
        """
        glfw.destroy_window(self.window)
        glfw.terminate()
        self.rendering_engine.destroy()
        self.scene.destroy_scene()
