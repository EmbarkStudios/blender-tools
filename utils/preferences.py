"""Blender add-on preferences for the Embark Addon."""


from os import environ, path
from bpy.props import BoolProperty, StringProperty
from bpy.types import AddonPreferences
from . import ADDON_NAME

BLENDER_TOOLS_SOURCE_PATH = "BLENDER_TOOLS_SOURCE_PATH"


def _get_default_source_location():
    if BLENDER_TOOLS_SOURCE_PATH in environ:
        return environ[BLENDER_TOOLS_SOURCE_PATH]
    return ""


class EmbarkAddonPreferences(AddonPreferences):  # pylint: disable=too-few-public-methods
    """Preferences class for the Embark Addon."""

    bl_idname = ADDON_NAME
    bl_label = "Source Location"
    bl_region_type = 'UI'
    bl_category = 'Embark'

    stored_source_path: StringProperty(options={'HIDDEN'})

    def _source_path_changed(self, context):
        """Called when the source_path property is changed."""
        if not self.source_path:
            self.stored_source_path = self.source_path
        elif path.exists(self.source_path):
            self.stored_source_path = self.source_path
        else:
            print(f"Error: Path does not exist: '{self.source_path}'")
            if self.stored_source_path and path.exists(self.stored_source_path):
                self.source_path = self.stored_source_path

    auto_update: BoolProperty(
        name="Automatically check for updates",
        description="If enabled, the addon will check for updates on each session launch (may add loading time)",
        default=True,
    )
    use_gltf: BoolProperty(
        name="Use glTF",
        description="If enabled, the addon will use glTF when exporting meshes",
        default=False,
    )
    source_path: StringProperty(
        name="Project source folder",
        description="Location of raw source files for your project, used as a root for scene & import/export paths",
        default=_get_default_source_location(),
        subtype='DIR_PATH',
        update=_source_path_changed,
    )

    def draw(self, context):
        """Draws the preferences."""
        self.layout.prop(self, 'auto_update', expand=True)
        self.layout.prop(self, 'use_gltf', expand=True)
        self.layout.prop(self, 'source_path', expand=True)

    def set_items(self, items):
        """Sets custom properties back on this item."""
        for item in items:
            prop_val = getattr(self, item[0], None)
            if prop_val is not None:
                setattr(self, item[0], item[1])


REGISTER_CLASSES = (
    EmbarkAddonPreferences,
)
