"""Operator to export all Export Collections in the scene."""

from bpy.types import Operator
from ..functions import get_export_collections, export_collections
from ...utils.path_manager import is_source_path_valid


class EmbarkExportAll(Operator):
    """Exports all Export Collections in the current scene."""

    bl_idname = "screen.embark_export_all"
    bl_label = "Export All Collections"
    bl_description = "Exports all Export Collections in the current scene"

    def execute(self, context):
        """Exports all Export Collections in the scene."""
        if not is_source_path_valid(show_warning=True):
            return {'CANCELLED'}

        total, succeeded = export_collections()
        count = f"{succeeded}/{total}"
        if succeeded == total:
            self.report({'INFO'}, f"Successfully exported {count} Export Collections")
        elif succeeded > 0:
            self.report({'ERROR'}, f"Only exported {count} Export Collections! See System Console for details.")
        else:
            self.report({'ERROR'}, "Failed to export any Export Collections! See System Console for details.")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        """Returns True if there are any Export Collections in the scene, otherwise False."""
        return get_export_collections()


def menu_draw(self, context):
    """Draw the operator as a menu item."""
    self.layout.operator(EmbarkExportAll.bl_idname, icon='EXPORT')
