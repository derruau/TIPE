import glfw


class InputScheme:
    """
    Une classe chargée de parser un fichier de configuration pour les contrôles du moteur de jeu.
    Elle donne aussi une couche d'abstraction pour savoir si une commande doit être déclenchée en fonction
    """
    __slots__ = ("input_scheme", "pressed_last_frame", "temp")

    def __init__(self, path: str) -> None:
        """
        Initialise la classe.
        """
        glfw.init()
        self.input_scheme = self.parse_input_scheme(path)
        self.pressed_last_frame: dict[str: bool] = {}
        self.temp: dict[str: bool] = {}

    def parse_input_scheme(self, path :str) -> dict[str: list[list[int]]]:
        """
        Parse le fichier d'input, du même format que controls.cfg
        """
        line_number:int = 0
        input_scheme:dict[str: list[list[int]]] = {}
        with open(path, "r") as f:
            line:str = f.readline()
            while line:
                if line.startswith("#") or (not line.strip()):
                    line_number += 1
                    line = f.readline()
                    continue

                line = line.strip()
                words:list[str] = line.split(" ")
                if len(words) != 2:
                    raise Exception(f"Erreur dans le fichier de configuration à la ligne {line_number}")
                
                keys:str = words[0]
                keys = keys.split("/")
                current_combo:list[int] = []
                for key in keys:
                    current_combo.append(key)

                if bool(input_scheme.get(words[1], False)):
                    input_scheme[words[1]].append(current_combo)
                else:
                    input_scheme[words[1]] = [current_combo]
                
                line_number += 1
                line = f.readline()
        return input_scheme

    def should_action_happen(self, action: str, keys: dict[int: bool]) -> bool:
        """
        On passe une action définit dans le fichier de configuration, et la liste des touches.
        La fonction nous renvoit si la combinaison de clés à laquelle est associée l'action doit se produire.
        """
        for key_combo in self.input_scheme[action]:
            result:bool = True
            for key in key_combo:
                result = result and keys.setdefault(key, False)
            if result:
                return True
        return False

    def begin_input_frame(self):
        self.temp = {}

    def end_input_frame(self):
        for key, value in self.temp.items():
            self.pressed_last_frame[key] = value 

    def on_press(self, action: str, keys: dict[int: bool]) -> bool:
        """
        Ne s'active qu'une seule fois lorsqu'on commence à appuyer sur un bouton
        """
        r = not(self.pressed_last_frame.get(action, False)) and keys.get(action, False)
        self.temp[action] = keys.get(action, False)
        return r
    
    def on_release(self, action: str, keys: dict[int: bool]) -> bool:
        """
        Ne s'active qu'une seule fois lorsqu'on relache un bouton.
        """
        r = self.pressed_last_frame.get(action, False) and not(keys.get(action, False))
        self.temp[action] = keys.get(action, False)
        return r
        # if not (action in keys):
        #     return False
        # if action in self.pressed_last_frame:
        #     if self.pressed_last_frame[action] == True:
        #         if not keys[action]:
        #             self.pressed_last_frame[action] = False
        #             return True
        # return False
