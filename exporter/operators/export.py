"""Operator to export an Export Collection by name."""


from bpy.props import StringProperty
from bpy.types import Operator
from ..functions import get_export_collection_by_name


class EmbarkExportCollection(Operator):  # pylint: disable=too-few-public-methods
    """Exports a named Export Collection."""

    bl_idname = "object.embark_export_collection"
    bl_label = "Export Collection"
    bl_description = "Exports this Export Collection"

    collection_name: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        """Export all Export Collections in the scene."""
        collection = get_export_collection_by_name(self.collection_name)
        if not collection:
            self.report({'ERROR'}, f"Failed to find an Export Collection named '{self.collection_name}'")
            return {'CANCELLED'}

        result = collection.export()
        if result == {'FINISHED'}:
            self.report({'INFO'}, f"Successfully exported '{self.collection_name}'!")
        else:
            self.report({'ERROR'}, f"Failed to export '{self.collection_name}'! See System Console for details.")
        return result
