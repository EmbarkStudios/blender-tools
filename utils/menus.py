"""Menus"""


import bpy
from .ui import menu_draw
from .. import exporter, operators


SEPARATOR = 'SEPARATOR'


def _draw_separator(self, context):
    """Just draw a separator."""
    self.layout.row().separator()


class MenuBuilder():
    """Helper class for building and updating menus consistently."""

    _items = ()

    def __init__(self, menu):
        self._menu = menu

    def add_items(self, *args):
        """Add the arguments as operators."""
        self._items = args

    def register(self):
        """Register the items with the menu."""
        for item in self._items:
            if item is SEPARATOR:
                self._menu.append(_draw_separator)
            elif getattr(item, 'menu_draw', None) is not None:
                self._menu.append(item.menu_draw)
            else:
                print(f"Warning: {item} has been added to a menu, but has no 'menu_draw' method!")

    def unregister(self):
        """Unregister the operators from the menu."""
        for item in reversed(self._items):
            if item is SEPARATOR:
                self._menu.remove(_draw_separator)
            else:
                self._menu.remove(item.menu_draw)

        self._items = ()


__registered_menus__ = []


def register():
    """Register all of the Embark Addon classes and build the menus."""

    bpy.types.TOPBAR_MT_editor_menus.append(menu_draw)

    # TODO: Consider converting the menus into JSON / XML definitions, and build from data

    embark_menu = MenuBuilder(bpy.types.TOPBAR_MT_Embark)
    embark_menu.add_items(
        operators.importer,
        SEPARATOR,
        exporter.operators.new_export_collection,
        exporter.operators.new_export_collections_per_object,
        exporter.operators.export_by_selection,
        exporter.operators.export_all,
        SEPARATOR,
        operators.connect_contextual,
        operators.add_spiral,
        SEPARATOR,
        operators.update,
        SEPARATOR,
        operators.documentation,
    )

    # Blender default Curve Add menu
    curve_menu = MenuBuilder(bpy.types.VIEW3D_MT_curve_add)
    curve_menu.add_items(
        SEPARATOR,
        operators.add_spiral,
    )

    # Blender default Edit Mesh menu
    edit_mesh_menu = MenuBuilder(bpy.types.VIEW3D_MT_edit_mesh)
    edit_mesh_menu.add_items(
        SEPARATOR,
        operators.connect_contextual,
    )

    # Blender default View menu
    view_menu = MenuBuilder(bpy.types.VIEW3D_MT_view)
    view_menu.add_items(
        SEPARATOR,
        operators.frame_contextual,
    )

    classes = (
        embark_menu,
        curve_menu,
        edit_mesh_menu,
        view_menu,
    )

    for cls in classes:
        cls.register()
        __registered_menus__.append(cls)


def unregister():
    """Unregister all of the Embark Addon classes and clean up."""
    for cls in reversed(__registered_menus__):
        cls.unregister()

    bpy.types.TOPBAR_MT_editor_menus.remove(menu_draw)
