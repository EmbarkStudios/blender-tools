"""Shared utility functions for exporting."""


from os import path
import bpy
from . import constants
from .export_collection import ExportCollection
from ..utils.functions import SceneState, create_sub_collection, create_space_name, get_all_col_names
from ..utils.path_manager import get_source_path, is_source_path_valid, validate_path


def check_path(operator):
    """Verifies that the scene path is under the Embark Addon's Project source folder."""
    if not is_source_path_valid():
        operator.report({'WARNING'}, "Please set up the 'Project source folder' in the Embark Addon preferences!")
        return False

    scene_path = bpy.path.abspath("//")
    if not validate_path(scene_path):
        operator.report({'ERROR'}, f"Please save your .blend file under {get_source_path()}")
        return False

    operator.directory = scene_path

    return True


def create_export_collection(export_name, export_path, export_type, apply_transform, objects):
    """Create a new Export Collection.

    :param export_name: Name of the Export Collection
    :param objects: List of objects to link to this Collection
    :return: The resulting Export Collection object
    """
    state = SceneState()
    bpy.ops.object.mode_set(mode='OBJECT')
    source_path = get_source_path()

    if constants.EXPORT_COLLECTION_NAME in bpy.context.scene.collection.children:
        exp_col = bpy.data.collections[constants.EXPORT_COLLECTION_NAME]
    else:
        exp_col = bpy.data.collections.new(constants.EXPORT_COLLECTION_NAME)
        bpy.context.scene.collection.children.link(exp_col)

    # Add Export Collection
    new_col = bpy.data.collections.new("TEMP_EXPORT_COLLECTION")
    exp_col.children.link(new_col)

    collection = ExportCollection(new_col)
    collection.export_name = export_name
    collection.export_path = path.relpath(export_path, source_path)
    collection.export_type = export_type
    collection.apply_transform = apply_transform

    collection['Mesh'] = create_sub_collection(collection, create_space_name('Mesh', get_all_col_names()))
    collection['Mesh']['LODS'] = {}
    collection['Collision'] = create_sub_collection(collection, create_space_name('Collision', get_all_col_names()))
    collection['Work'] = create_sub_collection(collection, create_space_name('Work', get_all_col_names()))

    for _ in range(0, 3):
        collection.add_lod_level()

    collection.add_objects(objects)

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=objects[0].location)
    export_origin = bpy.context.active_object
    export_origin.is_export_origin = True
    collection.objects.link(export_origin)  # pylint: disable=no-member

    # Remove this Empty from the active layer, it will be linked to this by default
    bpy.context.view_layer.active_layer_collection.collection.objects.unlink(export_origin)

    collection['Origin'] = export_origin
    collection.update_instance_offset()

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
        return [ExportCollection(coll) for coll in collections[0].children if ExportCollection(coll).is_selected]

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
        collection.update_collection_hierarchy()
        if collection.export() == {'FINISHED'}:
            num_exported += 1
    return len(collections), num_exported


def get_max_lod_count():
    """ Returns the maximum number of LODS found in an ExportCollection. """
    collections = get_export_collections()
    max_lod_num = 0
    for col in collections:
        mesh_col = col.get("Mesh")
        if mesh_col:
            num_lods = len(mesh_col["LODS"])
            max_lod_num = num_lods if num_lods > max_lod_num else max_lod_num
    return max_lod_num
