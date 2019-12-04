"""Operator to delete an Export Collection by name."""


from bpy.props import StringProperty
from bpy.types import Operator
from ..functions import get_export_collection_by_name


class EmbarkDeleteExportCollection(Operator):  # pylint: disable=too-few-public-methods
    """Deletes the named Export Collection, but leaves all contained objects in the scene."""

    bl_idname = "object.embark_delete_export_collection"
    bl_label = "Delete Export Collection"
    bl_description = "Deletes this Export Collection, but leaves all contained objects in the scene"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        """Deletes the named Collection."""
        collection = get_export_collection_by_name(self.collection_name)
        if not collection:
            self.report({'ERROR'}, f"Failed to find an Export Collection named '{self.collection_name}'")
            return {'CANCELLED'}

        collection.delete()

        self.report({'INFO'}, f"Deleted Export Collection '{self.collection_name}'")
        return {'FINISHED'}
