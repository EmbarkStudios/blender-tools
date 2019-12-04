"""Operator to remove objects from an Export Collection."""


from bpy.props import StringProperty
from bpy.types import Operator
from ..functions import get_export_collection_by_name


class EmbarkRemoveFromCollection(Operator):  # pylint: disable=too-few-public-methods
    """Deletes the named Export Collection, but leaves all contained objects in the scene."""

    bl_idname = "object.embark_remove_from_collection"
    bl_label = "Remove Selection from Export Collection"
    bl_description = "Removes the selected objects from this Export Collection"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        """Removes the selected objects from the named Collection."""
        collection = get_export_collection_by_name(self.collection_name)
        if not collection:
            self.report({'ERROR'}, f"Failed to find an Export Collection named '{self.collection_name}'")
            return {'CANCELLED'}

        num_removed = collection.remove_objects(context.selected_objects)

        self.report({'INFO'}, f"Removed {num_removed} object(s) from Export Collection '{self.collection_name}'")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """Only allows this operator to execute if there is a valid selection."""
        return context.selected_objects
