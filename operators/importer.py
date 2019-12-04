"""Importer operator for faster and more consistent studio import workflow."""


import os
import bpy
from bpy.props import BoolProperty, CollectionProperty, StringProperty
from ..utils.functions import remove_mats


class EmbarkImport(bpy.types.Operator):
    """Quick import for various file formats, with studio preset settings."""

    bl_idname = "screen.embark_import"
    bl_label = "Import"
    bl_description = "Import any file or files"
    bl_space_type = "TOPBAR_MT_file"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "UNDO"}

    supported_formats = "*.fbx;*.obj;*.ply"
    supported_formats += ";" + supported_formats.upper()

    # Properties used by the file browser
    filepath: StringProperty(
        name="File Path",
        description="File filepath used for importing the FBX/OBJ file",
        maxlen=1024,
        default='',
        options={'HIDDEN'},
    )
    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={'HIDDEN'})
    directory: StringProperty(maxlen=1024, default="", subtype='FILE_PATH', options={'HIDDEN'})
    filter_folder: BoolProperty(name="Filter Folders", description="", default=True, options={'HIDDEN'})
    filter_glob: StringProperty(default=supported_formats, options={'HIDDEN'})

    # TODO: Different import settings for different classes
    # dcc : bpy.props.EnumProperty(items= (('0', '!Blender', 'The zeroth item'),
    #                                    ('1', '!Zbrush', 'The first item'),
    #                                    ('2', '!Maya', 'The second item'),
    #                                    ('3', '!Unreal', 'The third item')),
    #                                    name = "import_preset")
    combined: bpy.props.BoolProperty(name="mesh_combine", description="Merge all objects on import", default=False)
    remove_materials: bpy.props.BoolProperty(
        name="Remove materials",
        description="Removes all materials from imported files, keeps material groups",
        default=True
    )

    def draw(self, context):
        """Draw the Import operator."""
        # self.layout.prop(self, "dcc",text="Import Preset")
        self.layout.prop(self, "remove_materials", text="Remove Materials")
        self.layout.prop(self, "combined", text="Combine Meshes")

    def execute(self, context):
        """Execute the Import operator."""
        # List used for combine
        imported_objects = []

        # Check for filetype
        filepaths = [os.path.join(self.directory, file.name) for file in self.files] if self.files else [self.filepath]
        for filepath in filepaths:
            index = 0
            if self._import_file(filepath):
                # Add to object list
                for obj in context.selected_objects:
                    if obj.type == "MESH":
                        imported_objects.append(obj)

                # Remove Materials
                if self.remove_materials:
                    remove_mats(context.selected_objects, False)

        # Check if Combined
        if self.combined:
            bpy.ops.object.select_all(action='DESELECT')
            for index, obj in enumerate(imported_objects):
                scene_obj = bpy.context.scene.objects[obj.name]
                if index == 0:
                    bpy.context.view_layer.objects.active = scene_obj
                scene_obj.select_set(True)
            bpy.ops.object.join()
        else:
            for obj in imported_objects:
                bpy.data.objects[obj.name].select_set(True)

        return {"FINISHED"}

    @staticmethod
    def _import_file(filepath):
        """Imports the file at `filepath` if the file was a supported type and returns True, otherwise returns False"""
        filepath_lc = filepath.lower()
        if filepath_lc.endswith('.fbx'):
            bpy.ops.import_scene.fbx(filepath=filepath)
            return True
        if filepath_lc.endswith('.obj'):
            bpy.ops.import_scene.obj(filepath=filepath)
            return True
        if filepath_lc.endswith('.ply'):
            bpy.ops.import_mesh.ply(filepath=filepath)
            return True
        return False

    def invoke(self, context, event):
        """Open a file browser"""
        bpy.context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_draw(self, context):
    """Draw the menu item for Embark Import."""
    self.layout.operator(EmbarkImport.bl_idname, icon='IMPORT')


REGISTER_CLASSES = (
    EmbarkImport,
)
