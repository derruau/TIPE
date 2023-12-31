"""
Une mesh (ou filet en français) est une collection de points qui définissent une forme.
Elle est associée à une entitée qui donne sa position et son orientation dans le monde.
"""
from core.view.rendering_engine import Vertices
from OpenGL.GL import *
import ctypes

MAX_CONCURENT_MESHES = 128

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

    __slots__ = ("vertex_count", "vao", "vbo", "filename", "_used_by", "_keep_in_memory")

    def __init__(self, filename: str, keep_in_memory: bool) -> None:
        self._used_by = 0
        self._keep_in_memory = keep_in_memory
        self.filename = filename

        # Définis dans self.init_material()
        self.vertex_count = None
        self.vao = None
        self.vbo = None

    def init_mesh(self):
        vertices = load_mesh(self.filename)
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

class MeshManager:
    __slots__ = ("available_mesh_id", "meshes")


    def __init__(self) -> None:
        # Chaque nombre représente le nombre de mesh qui ont cette ID qui actuellement en cours d'utilisation
        self.available_mesh_id = {id: True for id in range(MAX_CONCURENT_MESHES)}
        self.meshes: dict[int: Mesh] = {}

    def get_available_id(self) -> int:
        """
        Parcours la liste des ID disponible et renvoie la première disponible
        """
        for k,v in self.available_mesh_id.items():
            if v == True:
                return k
        return -1
    
    def is_id_valid(self, id: int) -> bool:
        """
        Renvoie si l'ID fournie est valide dans le sens où elle n'est pas illégale, pas dans le sens où elle est disponible
        """
        return id >= 0
    
    def is_id_in_use(self, id: int) -> bool:
        """
        Renvoie si l'ID fournie est utilisée par un shader
        """
        return not self.available_mesh_id[id]

    def get_meshes(self) -> dict[int: Mesh]:
        """
        Renvoie le dictionnaire contenant toutes les mesh, la clé est l'ID de la mesh et la valeur le en lui même
        """
        return self.meshes
    
    def append_mesh(self, mesh: Mesh) -> int:
        """
        Méthode à utiliser si on veut ajouter une mesh à la scène
        """
        id = self.get_available_id()
        if not self.is_id_valid(id):
            return -1
        
        self.available_mesh_id[id] = False
        self.meshes[id] = mesh
        return id

    def remove_mesh(self, id: int) -> bool:
        """
        Méthode à utiliser si on veut supprimer un mesh du Manager
        """
        if not self.is_id_in_use(id):
            # Le material n'existe pas
            return False

        mesh: Mesh = self.meshes[id]

        
        del mesh
        self.available_mesh_id[id] = True
        return True

    def clean(self, force: bool = False) -> None:
        """
        Supprime de la mémoire les mesh qui ne sont plus utilisés par une entitée ET qui ont le paramètre _keep_in_memory = False

        Où sinon si force = True, toutes les mesh sont supprimés de la mémoire, même si _keep_in_memory = True
        """
        for id, available in self.available_mesh_id.items():
            if available:
                continue
            mesh: Mesh = self.get_meshes()[id]
            if ((mesh._used_by == 0) and (mesh._keep_in_memory == False)) or force:
                mesh.destroy()
                self.remove_mesh(id)

    def destroy(self) -> bool:
        """
        Méthode à utiliser si on veut supprimer le manager en entier ainsi que toutes les mesh qui lui sont associés
        """
        self.clean(True)

    def add_mesh_use(self, mesh_id: int) -> None:
        """
        Préviens le Manager qu'une entité utilise le mesh d'ID mesh_id
        """
        mesh:Mesh = self.get_meshes()[mesh_id]
        mesh._used_by += 1

    def remove_mesh_use(self, mesh_id: int) -> None:
        """
        Préviens le Manager qu'une entité n'utilise plus le mesh d'ID mesh_id
        """
        mesh: Mesh = self.get_meshes()[mesh_id]
        mesh._used_by -= 1
