"""UI panel for the Embark Exporter, attached to the 3D View."""


from bpy.props import BoolProperty
from bpy.types import Panel, Scene
from .constants import GROUPS_ICON, PROP_EXPANDED, PROP_EXPORT_NAME, PROP_EXPORT_PATH, PROP_EXPORT_TYPE
from .functions import get_export_collections
from .operators import (
    EmbarkAddToCollection,
    EmbarkDeleteExportCollection,
    EmbarkExportAll,
    EmbarkExportBySelection,
    EmbarkExportCollection,
    EmbarkNewExportCollection,
    EmbarkNewExportCollectionsPerObject,
    EmbarkRemoveFromCollection,
    EmbarkSelectExportCollection,
)


# Add panel properties to Scene
Scene.export_panel_show_only_selected = BoolProperty(
    name="Show Only Selected Export Collections",
    description="Only show Export Collections in the Embark Export Panel that contain objects in the active selection",
    default=False,
)


class EmbarkExporterPanel(Panel):  # pylint: disable=too-few-public-methods
    """Tool panel for the Embark Exporter."""

    bl_idname = "EMBARK_PT_EmbarkExporter"
    bl_label = "Embark Exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Embark"

    def draw(self, context):
        """Draw the export settings panel."""
        row = self.layout.row()
        row.operator(EmbarkNewExportCollection.bl_idname, icon='COLLECTION_NEW')
        row.operator(EmbarkNewExportCollectionsPerObject.bl_idname, text="Per Object", icon=GROUPS_ICON)

        all_collections = get_export_collections()
        if not all_collections:
            self.layout.label(text="No Export Collections in scene!")
            return

        self.layout.prop(context.scene, "export_panel_show_only_selected")

        sel_collections = get_export_collections(only_selected=True)
        self.layout.label(text=f"{len(all_collections)} Export Collections in scene, {len(sel_collections)} selected")
        show_collections = sel_collections if context.scene.export_panel_show_only_selected else all_collections
        for collection in show_collections:
            is_selected = collection in sel_collections
            self._draw_collection_layout(collection, is_selected)

        row = self.layout.row()
        row.operator(EmbarkExportBySelection.bl_idname, text="Export by Selection", icon='EXPORT')
        row.operator(EmbarkExportAll.bl_idname, text="Export All", icon='EXPORT')

    def _draw_collection_layout(self, collection, is_selected):
        """Draw a layout displaying properties and operators for `collection`."""
        box = self.layout.box()
        expand = collection.export_panel_expanded or is_selected
        expand_icon = 'DOWNARROW_HLT' if expand else 'RIGHTARROW'
        box.prop(collection, PROP_EXPANDED, text=collection.name, icon=expand_icon, emboss=is_selected)
        if expand:
            box.prop(collection, PROP_EXPORT_NAME)
            box.prop(collection, PROP_EXPORT_TYPE)
            box.prop(collection, PROP_EXPORT_PATH)
            row = box.row()
            select = row.operator(EmbarkSelectExportCollection.bl_idname, text="", icon='GROUP', emboss=False)
            add = row.operator(EmbarkAddToCollection.bl_idname, text="", icon='ADD', emboss=False)
            remove = row.operator(EmbarkRemoveFromCollection.bl_idname, text="", icon='REMOVE', emboss=False)
            export = row.operator(EmbarkExportCollection.bl_idname, text="Export", icon='EXPORT')
            delete = row.operator(EmbarkDeleteExportCollection.bl_idname, text="", icon='TRASH', emboss=False)
            for operator in [select, add, remove, export, delete]:
                operator.collection_name = collection.name
