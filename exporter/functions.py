"""Shared utility functions for exporting."""


from os import path
import bpy
from . import constants
from .export_collection import ExportCollection
from ..utils import get_source_path
from ..utils.functions import SceneState


def check_path(operator):
    """Verifies that the scene path is under the Embark Addon's project source path."""
    source_path = get_source_path()
    if not source_path:
        operator.report({'ERROR'}, "Please set up the 'Project source folder' in the Embark Addon preferences!")
        return False

    source_path = path.normpath(source_path)
    scene_path = bpy.path.abspath("//")
    if not scene_path or not scene_path.lower().startswith(source_path.lower()):
        operator.report({'ERROR'}, f"Please save your .blend file under {source_path}")
        return False

    operator.directory = scene_path

    return True


def create_export_collection(export_name, export_path, export_type, objects):
    """Create a new Export Collection.

    :param export_name: Name of the Export Collection
    :param objects: List of objects to link to this Collection
    :return: The resulting Export Collection object
    """
    state = SceneState()

    if constants.EXPORT_COLLECTION_NAME in bpy.context.scene.collection.children:
        exp_col = bpy.data.collections[constants.EXPORT_COLLECTION_NAME]
    else:
        exp_col = bpy.data.collections.new(constants.EXPORT_COLLECTION_NAME)
        bpy.context.scene.collection.children.link(exp_col)

    new_col = bpy.data.collections.new("TEMP_EXPORT_COLLECTION")
    exp_col.children.link(new_col)

    for obj in objects:
        new_col.objects.link(obj)

    source_path = get_source_path()

    collection = ExportCollection(new_col)
    collection.export_name = export_name
    collection.export_path = path.relpath(export_path, source_path)
    collection.export_type = export_type

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=objects[0].location)
    export_origin = bpy.context.active_object
    export_origin.is_export_origin = True
    collection.objects.link(export_origin)  # pylint: disable=no-member

    # Remove this Empty from the active layer, it will be linked to this by default
    bpy.context.view_layer.active_layer_collection.collection.objects.unlink(export_origin)

    collection.rename()

    state.restore()

    return collection


def get_export_collections(only_selected=False):
    """Returns a list of Export Collections in the current scene.

    :param only_selected: If `True`, only return selected Export Collections, defaults to `False`
    :return: List of :class:`ExportCollection` objects
    """
    collections = [coll for coll in bpy.data.collections if coll.name == constants.EXPORT_COLLECTION_NAME]
    if not collections:
        return []

    if only_selected:
        sel_objs = bpy.context.selected_objects
        sel_collections = []
        for obj in sel_objs:
            collections_with_obj = [coll for coll in collections[0].children if obj.name in coll.objects]
            for collection in collections_with_obj:
                if collection not in sel_collections:
                    sel_collections.append(ExportCollection(collection))
        return sel_collections

    return [ExportCollection(collection) for collection in collections[0].children]


def get_export_collection_by_name(collection_name):
    """Returns an Export Collection object matching `collection_name`, or `None` if not found."""
    collections = get_export_collections()
    result = None
    for collection in collections:
        if collection.name == collection_name:
            result = collection
            break
    return result


def export_collections(only_selected=False):
    """Export all or selected Export Collections in this scene.

    :param only_selected: If `True`, only exports Export Collections that are selected, defaults to `False`
    :return: Tuple containing the total number of collections to export, and the number that succeeded
    """
    collections = get_export_collections(only_selected=only_selected)
    num_exported = 0
    for collection in collections:
        if collection.export() == {'FINISHED'}:
            num_exported += 1
    return len(collections), num_exported
