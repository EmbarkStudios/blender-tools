"""UI panel for the Embark Exporter, attached to the 3D View."""


from bpy.props import BoolProperty, PointerProperty, EnumProperty
from bpy.types import Panel, Scene, PropertyGroup
from bpy.utils import register_class, unregister_class
from .constants import GROUPS_ICON, PROP_EXPANDED, PROP_EXPORT_NAME, PROP_EXPORT_PATH, PROP_EXPORT_TYPE
from .functions import get_export_collections, get_max_lod_count
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


class EmbarkExporterPanel(Panel):  # pylint: disable=too-few-public-methods
    """Tool panel for the Embark Exporter."""

    bl_idname = "EMBARK_PT_EmbarkExporter"
    bl_label = "Embark Exporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Embark"

    @classmethod
    def poll(cls, context):
        ''' Tests to pass for drawing panel '''
        if not context.active_object:
            return True
        if context.active_object.mode == 'OBJECT':
            return True
        return False

    def draw(self, context):
        """Draw the export settings panel."""
        props = context.scene.export_panel_properties
        row = self.layout.row()
        row.operator(EmbarkNewExportCollection.bl_idname, icon='COLLECTION_NEW')
        row.operator(EmbarkNewExportCollectionsPerObject.bl_idname, text="Per Object", icon=GROUPS_ICON)

        all_collections = get_export_collections()
        if not all_collections:
            self.layout.label(text="No Export Collections in scene!")
            return

        row = self.layout.row(align=True)
        row.label(text="Display LOD")
        row.prop(props, "visible_lod", text="")

        row = self.layout.row(align=True)
        row.label(text="Show")
        row.prop(props, "show_mesh", text="Mesh", toggle=True)
        row.prop(props, "show_collision", text="Collision", toggle=True)
        row.prop(props, "show_sockets", text="Sockets", toggle=True)

        sel_collections = get_export_collections(only_selected=True)
        self.layout.prop(props, "show_only_selected")
        self.layout.label(text=f"{len(all_collections)} Export Collections in scene, {len(sel_collections)} selected")
        show_collections = sel_collections if props.show_only_selected else all_collections
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


def get_lod_enums(self, context):  # pylint: disable=unused-argument
    """ Generates the EnumProperty items for the visible_lod property. """
    # Get highest LOD count in any ExportCollection
    max_lod_num = get_max_lod_count()

    # Create EnumProperty Items
    items = []
    for i in range(0, max_lod_num):
        item = (f"LOD{i}", f"LOD{i}", "", i)
        items.append(item)

    items.append(("All", "All", "", len(items)))

    return items


def switch_shown_lod(self, context):
    """ Globally changes the visible LOD level. """
    collections = get_export_collections()
    for col in collections:
        col.set_visible_lod(self.visible_lod)


def toggle_show_mesh(self, context):
    """ Globally show/hide meshes in ExportCollections. """
    collections = get_export_collections()
    for col in collections:
        col.show_mesh_objects(self.show_mesh)


def toggle_show_collision(self, context):
    """ Globally show/hide collision collection in ExportCollections. """
    collections = get_export_collections()
    for col in collections:
        col.show_top_level_collection("Collision", self.show_collision)


def toggle_show_sockets(self, context):
    """ Globally show/hide sockets in ExportCollections. """
    collections = get_export_collections()
    for col in collections:
        col.show_socket_objects(self.show_sockets)


class EmbarkExporterPanelProperties(PropertyGroup):
    """ PropertyGroup for the EmbarkExporterPanel. """

    show_only_selected: BoolProperty(
        name="Show Only Selected Export Collections",
        description="Only show Export Collections in the Export Panel that contain objects in the active selection",
        default=False,
    )

    visible_lod: EnumProperty(
        items=get_lod_enums,
        name="Display LOD",
        default=0,
        update=switch_shown_lod,
    )

    show_mesh: BoolProperty(
        name="Show Mesh",
        description="Toggles the visibility of Meshes in the Export Collections.",
        default=True,
        update=toggle_show_mesh,
    )

    show_collision: BoolProperty(
        name="Show Collision",
        description="Toggles the visibility of Collision in the Export Collections.",
        default=True,
        update=toggle_show_collision,
    )

    show_sockets: BoolProperty(
        name="Show Sockets",
        description="Toggles the visibility of Sockets in the Export Collections.",
        default=True,
        update=toggle_show_sockets,
    )


def register():
    """ Register classes and data. """
    register_class(EmbarkExporterPanel)
    register_class(EmbarkExporterPanelProperties)

    Scene.export_panel_properties = PointerProperty(type=EmbarkExporterPanelProperties)


def unregister():
    """ Unregister classes and data. """
    unregister_class(EmbarkExporterPanel)
    unregister_class(EmbarkExporterPanelProperties)

    del Scene.export_panel_properties
