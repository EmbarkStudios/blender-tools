"""Operators for help and documentation about the Embark Addon."""


import webbrowser
import bpy


class EmbarkAddonDocumentation(bpy.types.Operator):  # pylint: disable=too-few-public-methods
    """Open the addon's online documentation in a web browser."""

    bl_label = "Documentation"
    bl_idname = "screen.embark_documentation"
    bl_description = "Open help documentation for the Embark Addon"

    _help_url = "https://github.com/EmbarkStudios/blender-tools/"

    def execute(self, context):
        """Open the default web browser to the help URL."""
        webbrowser.open(self._help_url)
        return {'FINISHED'}


def menu_draw(self, context):
    """Create the menu item."""
    self.layout.operator(EmbarkAddonDocumentation.bl_idname, icon="URL")


REGISTER_CLASSES = (
    EmbarkAddonDocumentation,
)
