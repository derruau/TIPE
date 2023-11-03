import glfw


class InputScheme:
    """
    Une classe chargée de parser un fichier de configuration pour les contrôles du moteur de jeu.
    Elle donne aussi une couche d'abstraction pour savoir si une commande doit être déclenchée en fonction
    """
    def __init__(self, path: str) -> None:
        glfw.init()
        self.input_scheme = self.parse_input_scheme(path)

    def parse_input_scheme(self, path :str) -> dict[str: list[list[int]]]:
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
        for key_combo in self.input_scheme[action]:
            result:bool = True
            for key in key_combo:
                result = result and keys.setdefault(key, False)
            if result:
                return True
        return False
