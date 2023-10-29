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
        self.shader_manager = shader_manager
        self.material_manager = material_manager
        self.mesh_manager = mesh_manager

    def init_managers(self) -> None:
        for shader in self.shader_manager.get_shaders().values():
            shader.init_shader()
        for mesh in self.mesh_manager.get_meshes().values():
            mesh.init_mesh()
        for material in self.material_manager.get_materials().values():
            material.init_material()

    def clean_unused_resources(self) -> None:
        """
        Détruit de la mémoire toutes les resources non utilisées par le PC.
        """
        self.shader_manager.clean()
        self.material_manager.clean()
        self.mesh_manager.clean()

    def destroy(self) -> None:
        self.shader_manager.destroy()
        self.material_manager.destroy()
        self.mesh_manager.destroy()
