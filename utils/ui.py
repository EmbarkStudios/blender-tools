"""UI functionality for the Embark Addon, including menus and icon management."""


from os import listdir, path
from bpy.types import Menu
from bpy.utils import previews, register_class, unregister_class


__icon_manager__ = None


class IconManager():  # pylint: disable=too-few-public-methods
    """Singleton class for handling icons in the Blender previews system."""
    icons = None
    _supported_formats = ('.png')

    def __init__(self):
        self.icons = previews.new()

        icons_dir = path.normpath(path.join(path.dirname(__file__), "../icons"))
        for icon_file in sorted(listdir(icons_dir)):
            name_tokens = path.splitext(icon_file)
            filepath = path.join(icons_dir, icon_file)
            if name_tokens[1] in self._supported_formats:
                self.icons.load(name_tokens[0], filepath, 'IMAGE')
            else:
                print(f"Error: Unsupported icon format '{name_tokens[1]}': {filepath}")

    def unregister(self):
        """Remove the Embark Addon's icon previews from Blender."""
        previews.remove(self.icons)
        self.icons = None


def get_icon(name):
    """Get an internal Blender icon ID from an icon name."""
    try:
        return __icon_manager__.icons[name].icon_id
    except KeyError:
        print(f"Error: Failed to find icon named '{name}'!")
        return None


class EmbarkMenu(Menu):  # pylint: disable=too-few-public-methods
    """A menu for any registered functionality that should be accessible in any context."""
    bl_idname = "TOPBAR_MT_Embark"
    bl_label = " Embark"

    def draw(self, context):
        """Draw the menu."""


def menu_draw(self, context):
    """Draw the addon menus."""
    self.layout.menu(EmbarkMenu.bl_idname, text=EmbarkMenu.bl_label, icon_value=get_icon('embark_logo'))


__classes__ = (
    EmbarkMenu,
)


def register():
    """Load the icons, register the menus and add them to the Blender UI."""
    global __icon_manager__  # pylint: disable=global-statement
    if __icon_manager__ is None:
        __icon_manager__ = IconManager()

    for cls in __classes__:
        register_class(cls)


def unregister():
    """Remove the menus and Load the icons, register the menus and add them to the Blender UI."""
    for cls in reversed(__classes__):
        unregister_class(cls)

    global __icon_manager__  # pylint: disable=global-statement
    __icon_manager__.unregister()
    __icon_manager__ = None
