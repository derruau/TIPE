"""
On appelle material une image projetée sur un triangle qui compose une mesh
"""
from OpenGL.GL import *
from PIL import Image

class Material:
    def __init__(self, material_path: str) -> None:

        # Dans le vocabulaire OpenGL, une texture est un conteneur qui contient 1 ou plusieurs images au même format
        self.texture = glGenTextures(1)
        # GL_TEXTURE_2D est une collection d'images à 2 dimensions
        # C'est à dire qu'elles ont une hauteur et une largeur non nulle, mais une profondeur nulle
        glBindTexture(GL_TEXTURE_2D, self.texture)

        # Répéter la texture sur l'axe s (axe des abscisses) si la face est trop grande
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        # Répéter la texture sur l'axe t (axe des ordonnées) si la face est trop grande
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # Paramètres esthétiques pour que la texture ait un meilleur rendu 
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameter(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        with Image.open(material_path, mode = "r") as image:
            image_width, image_height = image.size
            image = image.convert("RGBA")
            image_data = bytes(image.tobytes())
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image_width, image_height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
        glGenerateMipmap(GL_TEXTURE_2D)

    def use(self) -> None:
        """
        Permet de dire à OpenGL quelle texture utiliser lorsqu'il dessine une mesh
        À utiliser avant mesh.prepare_to_draw()
        """
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    
    def destroy(self) -> None:
        """
        Libère la mémoire utilisée par la texture
        """
        glDeleteTextures(1, (self.texture,))


