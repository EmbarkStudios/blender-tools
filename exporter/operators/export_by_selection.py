"""Operator to export Export Collections based on the object selection."""


from bpy.types import Operator
from ..functions import get_export_collections, export_collections


class EmbarkExportBySelection(Operator):
    """Export the Export Collection(s) which contain the selected objects."""

    bl_idname = "object.embark_export_by_selection"
    bl_label = "Export Collection(s) by Selection"
    bl_description = "Exports the Export Collection(s) which contain the selected objects"

    def execute(self, context):
        """Export any Export Collections containing the current object selection."""
        total, succeeded = export_collections(only_selected=True)
        count = f"{succeeded}/{total}"
        if succeeded == total:
            self.report({'INFO'}, f"Successfully exported {count} Export Collections containing selected objects")
        elif succeeded > 0:
            self.report({'ERROR'}, f"Only exported {count} Export Collections! See System Console for details.")
        else:
            self.report({'ERROR'}, "Failed to export any Export Collections! See System Console for details.")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """Return True if the selection is valid for operator execution, otherwise False."""
        return get_export_collections(only_selected=True)


def menu_draw(self, context):
    """Draw the operator as a menu item."""
    self.layout.operator(EmbarkExportBySelection.bl_idname, icon='EXPORT')
