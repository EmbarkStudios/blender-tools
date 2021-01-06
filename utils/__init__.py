"""Useful utilities and constants for the addon."""


from importlib import reload
from inspect import isclass
from os.path import basename, dirname, normpath
import sys
import bpy


# This is the addon's directory name, by default "embark_blender_tools", but anyone can change the folder name...
# We use dirname() twice to go up two levels in the file system and then basename to get the folder name.
# Thanks to https://github.com/LuxCoreRender/BlendLuxCore/ for the example of solving the same issue!
ADDON_NAME = basename(dirname(dirname(__file__)))


def get_current_version():
    """Returns the current version of the loaded addon."""
    mod = sys.modules[ADDON_NAME]
    current_version = mod.bl_info.get("version", (0, 0, 1))
    return '.'.join([str(num) for num in current_version])


def get_preferences():
    """Returns the addon's Preferences object."""
    return bpy.context.preferences.addons[ADDON_NAME].preferences


def get_source_path():
    """Returns the Embark Addon's Project source path."""
    return normpath(get_preferences().source_path)


def reload_addon():
    """Reloads the Embark Addon and all of its modules."""
    _addon_name = ADDON_NAME

    pref_items = get_preferences().items()
    bpy.ops.preferences.addon_disable(module=_addon_name)

    # reloadable = [mod for mod in sys.modules.values() if getattr(mod, '__name__', "").startswith(_addon_name)]
    # for module in reloadable:
    #    try:
    #        print(f"\tReloading {module.__name__}...")
    #        reload(module)
    #    except Exception as ex:  # pylint: disable=broad-except
    #        print(f"Error: Failed to reload module '{module.__name__}', reason: {ex}")

    bpy.ops.preferences.addon_enable(module=_addon_name)

    # Reset the previous preference items onto the reloaded preferences
    get_preferences().set_items(pref_items)


def register_recursive(objects):
    """Registers classes with Blender recursively from modules."""
    for obj in objects:
        if isclass(obj):
            bpy.utils.register_class(obj)
        elif hasattr(obj, "register"):
            obj.register()
        elif hasattr(obj, "REGISTER_CLASSES"):
            register_recursive(obj.REGISTER_CLASSES)
        else:
            print(f"Warning: Failed to find anything to register for '{obj}'")


def unregister_recursive(objects):
    """Unregisters classes from Blender recursively from modules."""
    for obj in reversed(objects):
        if isclass(obj):
            bpy.utils.unregister_class(obj)
        elif hasattr(obj, "unregister"):
            obj.unregister()
        elif hasattr(obj, "REGISTER_CLASSES"):
            unregister_recursive(obj.REGISTER_CLASSES)
        else:
            print(f"Warning: Failed to find anything to unregister for '{obj}'")
