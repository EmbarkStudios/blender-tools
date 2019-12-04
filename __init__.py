"""A Blender add-on containing workflow tools for game development, created by Embark Studios.

  Add-on repository: https://github.com/EmbarkStudios/blender-tools
  Embark Studios: https://www.embark-studios.com
"""


from . import exporter, operators
from .utils import menus, preferences, ui, register_recursive, unregister_recursive


bl_info = {
    "name": "Embark Addon",
    "description": "A suite of tools geared towards game development, created by Embark Studios",
    "author": "Embark Studios",
    "version": (1, 5, 1),
    "blender": (2, 80, 0),
    "location": "",
    "warning": "",
    "wiki_url": "https://github.com/EmbarkStudios/blender-tools/",
    "tracker_url": "https://github.com/EmbarkStudios/blender-tools/issues/new/choose",
    "support": "COMMUNITY",
    "category": "Generic"
}


REGISTER_CLASSES = (
    preferences,
    ui,
    exporter,
    operators,
    menus,
)


def register():
    """Register all of the Embark Addon classes."""
    register_recursive(REGISTER_CLASSES)


def unregister():
    """Unregister all of the Embark Addon classes."""
    unregister_recursive(REGISTER_CLASSES)
