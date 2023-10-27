"""
Une mesh (ou filet en français) est une collection de points qui définissent une forme.
Elle est associée à une entitée qui donne sa position et son orientation dans le monde.
"""
from core.view.rendering_engine import Vertices
from OpenGL.GL import *
import ctypes

def load_mesh(filename: str) -> Vertices:
    """
    Convertit un fichier au format .obj en une liste de points utilisable par le moteur graphique
    """
    if not filename.endswith(".obj"):
        raise Exception("Seul les fichiers au format .obj sont acceptés!")
    
    def append_face_data_to_vertices(face: list[str], v: list[list[float]], vt: list[list[float]], vn: list[list[float]], vertices: list[float]) -> None:
        """
        Prend en entrée une face (polygone convexe quelconque) et la décompose en triangles.
        L'argument face est sous cette forme: ['f', 'v_id/vt_id/vn_id', 'v_id/vt_id/vn_id', ... , 'v_id/vt_id/vn_id']
        et les ID sont indexés à partir de 1.

        Ainsi pour décomposer en triangles, on prend tout les triangles formés par
        (face[1], face[2 + i], face[3 + i]) pour tout i dans [|0, len(face) - 3|]
        """

        nb_triangles = len(face) - 3
        for i in range(nb_triangles):
            to_vertex(face[1], v, vt, vn, vertices)
            to_vertex(face[2 + i], v, vt, vn, vertices)
            to_vertex(face[3 + i], v, vt, vn, vertices)
        return

    def to_vertex(point: str, v: list[list[float]], vt: list[list[float]], vn: list[list[float]], vertices: list[float]) -> None:
        """
        Prend en entrée un point d'une face (voir append_face_data_to_vertices()) pour le transformer au format valable de vertices.
        L'argument point est au format 'v_id/vt_id/vn_id' et les ID sont indexés à partir de 1.
        """
        v_vt_vn = point.split("/")

        for e in v[int(v_vt_vn[0]) - 1]:
            vertices.append(e)
        for e in vt[int(v_vt_vn[1]) - 1]:
            vertices.append(e)
        for e in vn[int(v_vt_vn[2]) - 1]:
            vertices.append(e)

        return

    vertices: list[float] = []
    v: list[list[float]] = []
    vt: list[list[float]] = []
    vn: list[list[float]] = []
    
    with open(filename, "r") as file:
        line:str = file.readline()
        while line:
            words: list[str] = line.split(" ")
            match words[0]:
                case "v":
                    v.append( [float(words[1]), float(words[2]), float(words[3])] )
                case "vt":
                    vt.append( [float(words[1]), float(words[2])] )
                case "vn":
                    vn.append( [float(words[1]), float(words[2]), float(words[3])] )
                case "f":
                    append_face_data_to_vertices(words, v, vt, vn, vertices)
            line = file.readline()

    return Vertices(vertices)


class Mesh:
    """
    Une mesh (ou filet en français) est une collection de points qui définissent une forme.
    Pour instancier une mesh, il faut passer en argument le chemin d'un fichier .obj (très important) qu'on souhaite dessiner
    \n\n
    Remarque: ne pas instancier trop de mesh en même temps, car cette implémentation n'est pas très performante.
    En effet, à chaque fois qu'on veut dessiner une de ces mesh, il faut appeler les méthodes prepare_to_draw() et draw(), ce qui prends beaucoup de temps
    Dans le cas où on devrait avoir beaucoup de mesh en même temps, il faut privilégier une méthode avec moins de draw calls!!
    """

    __slots__ = ("vertex_count", "vao", "vbo")

    def __init__(self, filename: str) -> None:
        vertices = load_mesh(filename)
        self.vertex_count = len(vertices.get()) // 8

        # vao = Vertex Array Object => contient de vbo et ses attribus défini ci-dessous
        self.vao = glGenVertexArrays(1) 
        glBindVertexArray(self.vao)

        # vbo = Vertex Object Buffer
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.get().nbytes, vertices.get(), GL_STATIC_DRAW)

        # Attribu de position (x, y, z)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(0))

        # Attribu de Texture (s, t)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(12))

        # Attribu de normale (n_x, n_y, n_z)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 32, ctypes.c_void_p(20))


    def prepare_to_draw(self) -> None:
        """
        Lie le vao afin qu'il puisse être dessiné à l'écran
        """
        glBindVertexArray(self.vao)


    def draw(self) -> None:
        """
        Dessine la mesh à l'écran. 
        TOUJOURS appeler prepare_to_draw() avant cette fonction!!
        """
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)


    def destroy(self) -> None:
        """
        Libère la mémoire utilisée par le VBO et le VAO.
        """
        glDeleteVertexArrays(1, (self.vao,))
        glDeleteBuffers(1, (self.vbo,))

    