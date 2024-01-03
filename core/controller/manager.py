from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.models.material import MaterialManager
    from core.models.mesh import MeshManager
    from core.models.shader import ShaderManager

class Manager:
    """
    La classe Manager est le chef de toutes les autres classes *Manager. C'est celle-ci qu'on passe en argument de la classe scène Scene.
    """
    def __init__(
            self,
            shader_manager: ShaderManager,
            material_manager: MaterialManager,
            mesh_manager: MeshManager
            ) -> None:
        """
        Initialise la classe Manager.
        """
        self.shader_manager = shader_manager
        self.material_manager = material_manager
        self.mesh_manager = mesh_manager

    def init_managers(self) -> None:
        """
        Initialise toutes les ressources de tout les *managers.
        """
        for shader in self.shader_manager.get_shaders().values():
            shader.init_shader()
        for mesh in self.mesh_manager.get_meshes().values():
            mesh.init_mesh()
        for id, material in self.material_manager.get_materials().items():
            material.init_material(id)

    def clean_unused_resources(self) -> None:
        """
        Détruit de la mémoire toutes les resources non utilisées par le PC.
        """
        self.shader_manager.clean()
        self.material_manager.clean()
        self.mesh_manager.clean()

    def destroy(self) -> None:
        """
        Détruit de la mémoire tout les
        """
        self.shader_manager.destroy()
        self.material_manager.destroy()
        self.mesh_manager.destroy()
