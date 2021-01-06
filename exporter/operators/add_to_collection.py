"""Operator to add objects to an Export Collection."""


from bpy.props import StringProperty
from bpy.types import Operator
from ..functions import get_export_collection_by_name


class EmbarkAddToCollection(Operator):  # pylint: disable=too-few-public-methods
    """Adds the selected objects to the named Export Collection."""

    bl_idname = "object.embark_add_to_collection"
    bl_label = "Add Selection to Export Collection"
    bl_description = "Adds the selected objects to this Export Collection"
    bl_options = {'REGISTER', 'UNDO'}

    collection_name: StringProperty(options={'HIDDEN'})

    def execute(self, context):
        """Adds the selected objects to the named Collection."""
        collection = get_export_collection_by_name(self.collection_name)
        if not collection:
            self.report({'ERROR'}, f"Failed to find an Export Collection named '{self.collection_name}'")
            return {'CANCELLED'}

        collection.update_collection_hierarchy()
        num_added = collection.add_objects(context.selected_objects)

        self.report({'INFO'}, f"Added {num_added} object(s) to Export Collection '{self.collection_name}'")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """Only allows this operator to execute if there is a valid selection."""
        return context.selected_objects
