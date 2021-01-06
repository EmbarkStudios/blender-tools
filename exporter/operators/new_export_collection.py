"""Operator to create a new Export Collection containing the selected objects."""


from os import path
import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator
from .. import constants
from ...utils.functions import get_export_extension, get_export_filter_glob
from ..export_collection import get_export_filename
from ..functions import check_path, create_export_collection


class EmbarkNewExportCollection(Operator):
    """Creates a new Export Collection containing the currently-selected objects."""

    bl_idname = "screen.embark_new_export_collection"
    bl_label = "New Export Collection"
    bl_description = "Creates a new Export Collection containing the currently-selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def _export_type_changed(self, context):
        """Updates the file browser type filter and file extension when the Export Type is changed."""
        # BUG: Dynamically changing the file browser properties appears to not be currently supported in Blender :(
        self.filter_glob = get_export_filter_glob()
        self.filename = get_export_filename(self.export_name, self.export_type)

    directory: StringProperty()
    export_immediately: BoolProperty(
        name="Export Immediately",
        description="Export this collection immediately",
        default=True,
    )
    apply_transform: BoolProperty(
        name='Apply Transform',
        description='Applies transform to work with UE4s "Transform Vertex to Absolute" import setting.',
        default=False,
    )
    export_type: EnumProperty(name="Type", items=constants.EXPORT_TYPES, default=constants.STATIC_MESH_TYPE)
    filename: StringProperty()
    filter_glob: StringProperty(default="*.fbx;*.obj")
    export_name: StringProperty(options={'HIDDEN'})

    def draw(self, context):
        """Draws the Operator properties."""
        self.layout.prop(self, constants.PROP_EXPORT_TYPE, expand=True)
        self.layout.label(text=f"Exports in {get_export_extension(self.export_type)} format")
        self.layout.prop(self, "export_immediately")

        if get_export_extension(self.export_type) == 'FBX':
            self.layout.prop(self, "apply_transform")

    def execute(self, context):
        """Creates a new Export Collection from the selection, optionally exporting it if requested."""
        export_name = path.splitext(self.filename)[0]
        objects = bpy.context.selected_objects

        # Set the active object as the first in the list, this will be used for origin setting
        active_object = bpy.context.active_object
        if active_object:
            if active_object in objects:
                objects.remove(active_object)
            objects.insert(0, active_object)

        collection = create_export_collection(export_name, self.directory,
                                              self.export_type, self.apply_transform, objects)
        if self.export_immediately:
            if collection.export() == {'FINISHED'}:
                self.report({'INFO'}, f"Successfully created & exported '{collection.name}'")
            else:
                self.report({'WARNING'}, f"Created '{collection.name}', but export failed! See System Console.")
        else:
            self.report({'INFO'}, f"Created new Export Collection: '{collection.name}'")
        return {'FINISHED'}

    def invoke(self, context, event):
        """Invokes a file browser with this Operator's properties."""
        if not check_path(self):
            return {'CANCELLED'}
        if bpy.context.active_object:
            export_name = bpy.context.active_object.name
        else:
            export_name = path.splitext(path.basename(bpy.data.filepath))[0]
        self.filename = get_export_filename(export_name, self.export_type)
        self.filter_glob = get_export_filter_glob()
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        """Only allows this operator to execute if there is a valid selection."""
        return context.selected_objects


def menu_draw(self, context):
    """Draw the operator as a menu item."""
    self.layout.operator(EmbarkNewExportCollection.bl_idname, icon='COLLECTION_NEW')
