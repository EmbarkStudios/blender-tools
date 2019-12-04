"""Operator for selecting Export Collection contents by name."""


from bpy.props import StringProperty
from bpy.types import Operator
from ..functions import get_export_collection_by_name


class EmbarkSelectExportCollection(Operator):  # pylint: disable=too-few-public-methods
    """Selects all the objects contained in the named Export Collection."""

    bl_idname = "object.embark_select_export_collection"
    bl_label = "Select Export Collection"
    bl_description = "Selects all the objects contained in this Export Collection"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        """Selects all the objects in the named Collection."""
        collection = get_export_collection_by_name(self.collection_name)
        if not collection:
            self.report({'ERROR'}, f"Failed to find an Export Collection named '{self.collection_name}'")
            return {'CANCELLED'}

        collection.select()

        self.report({'INFO'}, f"Selected contents of Export Collection '{self.collection_name}'")
        return {'FINISHED'}
