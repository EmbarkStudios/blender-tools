"""General-use shared functions for the Embark Addon."""


from math import sin, cos, pi
from re import split
from fnmatch import fnmatch
import bpy
from mathutils import Vector
from ..exporter import constants
from . import get_preferences


TWO_PI = pi * 2
SOCKET_PREFIX = "SOCKET_"


class SceneState():  # pylint: disable=too-few-public-methods
    """Class for storing and restoring scene selection state and objects/collection properties."""

    def __init__(self, objects=None, collections=None):
        """Store the main context's active object, edit object and selection."""
        self.active_object = bpy.context.view_layer.objects.active
        self.edit_object = bpy.context.edit_object
        self.selected_objects = bpy.context.selected_objects
        self.edit_select_mode = None
        if self.edit_object:
            self.edit_select_mode = tuple(bpy.context.tool_settings.mesh_select_mode)

        self.objects = []
        if objects:
            for obj in objects:
                obj_entry = {"Object": obj,
                             "Selected": obj.select_get(),
                             "Hidden": obj.hide_get()
                             }
                self.objects.append(obj_entry)

        self.collections = []
        if collections:
            for col in collections:
                col_entry = {"Collection": col,
                             "Hidden": col.hide_viewport
                             }
                self.collections.append(col_entry)

    def restore(self):
        """Reset the main context's active, edit and selected objects to those stored in this `SceneState` object."""
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode='OBJECT')

        if self.collections:
            for col_entry in self.collections:
                col = col_entry["Collection"]
                col.hide_viewport = col_entry["Hidden"]

        bpy.ops.object.select_all(action='DESELECT')
        if self.objects:
            for obj_entry in self.objects:
                obj = obj_entry["Object"]
                obj.hide_set(obj_entry["Hidden"])
                obj.select_set(obj_entry["Selected"])
        bpy.context.view_layer.objects.active = self.active_object

        if self.edit_object:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.context.view_layer.objects.active = self.edit_object
            bpy.context.tool_settings.mesh_select_mode = self.edit_select_mode


def get_export_extension(export_type):
    """Returns a string with the file extension for the provided export type."""
    pref_extension = get_preferences().export_file_type
    extensions = {
        constants.STATIC_MESH_TYPE: pref_extension,
        constants.SKELETAL_MESH_TYPE: pref_extension,
        constants.MID_POLY_TYPE: 'OBJ',
        constants.HIGH_POLY_TYPE: 'OBJ',
    }
    return extensions.get(export_type, pref_extension)


def get_export_method(export_type):
    """Returns a function for exporting the provided export type."""
    extension = get_export_extension(export_type)
    methods = {
        'FBX': export_fbx,
        'GLTF': lambda filepath: export_gltf(filepath, 'GLTF_SEPARATE'),
        'GLB': lambda filepath: export_gltf(filepath, 'GLB'),
        'OBJ': export_obj,
    }
    return methods.get(extension, export_fbx)


def get_export_filter_glob():
    """Returns a function for exporting the provided export type."""
    pref_extension = get_preferences().export_file_type
    globs = {
        'FBX': '*.fbx;*.obj',
        'GLTF': '*.gltf;*.obj',
        'GLB': '*.glb;*.obj',
    }
    return globs.get(pref_extension, '*')


def export_gltf(filepath, export_format):
    """Export a glTF with standardized settings."""
    return bpy.ops.export_scene.gltf(
        export_format=export_format,
        export_copyright="",
        export_texcoords=True,
        export_normals=True,
        export_draco_mesh_compression_enable=False,
        export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14,
        export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12,
        export_tangents=False,
        export_materials=True,
        export_colors=True,
        export_cameras=False,
        export_selected=True,
        export_extras=False,
        export_yup=True,
        export_apply=True,
        export_animations=True,
        export_frame_range=True,
        export_frame_step=1,
        export_force_sampling=True,
        export_nla_strips=True,
        export_current_frame=False,
        export_skins=True,
        export_all_influences=False,
        export_morph=True,
        export_morph_normal=True,
        export_morph_tangent=False,
        export_lights=False,
        export_displacement=False,
        will_save_settings=False,
        filepath=filepath,
        check_existing=False,
        filter_glob="*.glb;*.gltf",
    )


def export_fbx(filepath):
    """Export an FBX with standardized settings."""
    return bpy.ops.export_scene.fbx(
        filepath=filepath,
        check_existing=False,
        use_selection=True,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE',
        bake_space_transform=True,
        object_types={'EMPTY', 'MESH', 'OTHER'},
        use_armature_deform_only=True,
        mesh_smooth_type='FACE',
        add_leaf_bones=False,
        embed_textures=False,
        axis_forward='-Z',
        axis_up='Y',
    )


def export_fbx_apply_transform(filepath):
    """Export an FBX to work with UE4's Transform Vertex to Absolute import setting."""
    return bpy.ops.export_scene.fbx(
        filepath=filepath,
        check_existing=False,
        use_selection=True,  # TODO: Consider use_active_collection, so we don't have to mess with selection?
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_NONE',
        bake_space_transform=True,
        object_types={'EMPTY', 'MESH', 'OTHER'},
        use_mesh_modifiers=True,
        use_armature_deform_only=True,
        mesh_smooth_type='FACE',
        add_leaf_bones=False,
        embed_textures=False,
        axis_forward='Y',
        axis_up='Z',
    )


def export_obj(filepath):
    """Export an OBJ with standardized settings."""
    return bpy.ops.export_scene.obj(
        filepath=filepath,
        check_existing=False,
        use_selection=True,
        global_scale=1.0,
        use_triangles=True,
        axis_forward='-Z',
        axis_up='Y',
    )


def remove_numeric_suffix(name):
    """Returns a string with any Blender numeric suffix, in the form .000, removed from `name`."""
    pattern = r"(\.[0-9]{3})$"
    return split(pattern, name)[0]


def remove_mats(objectlist, remove_groups):
    """remove materials from list of objects"""
    for obj in objectlist:
        if remove_groups:
            pass
            # TODO: remove material groups
        if obj.type == "MESH" and obj.data.materials:
            for mat in obj.data.materials:
                if mat is not None:
                    bpy.data.materials.remove(mat)


def unlink_collection(parent_collection, collection):
    """Unlinks `collection` from `parent_collection` and all of its child collections."""
    for child_collection in parent_collection.children:
        unlink_collection(child_collection, collection)
    if collection.name in parent_collection.children.keys():
        parent_collection.children.unlink(collection)
    for coll in bpy.data.collections:
        if not coll.users:
            bpy.data.collections.remove(coll)


def create_polar_coordinates(radius, height, resolution, radius_mult, length, start_location=(0.0, 0.0, 0.0)):
    """Creates a list of polar coordinates with different shapes depending on input"""

    # Empty list to store cordinates in
    pos_list = []

    # Some math stuff for polar coordinates
    size = TWO_PI * length

    adaptive_resolution = resolution * length
    radius_step = (TWO_PI / adaptive_resolution) * radius_mult

    # Step variables
    step_angle = size / adaptive_resolution
    step = 0
    z_step = 0

    # While step is smaller than total size
    while step <= size + 0.000001:
        x = start_location[0] + cos(step) * radius
        y = start_location[1] + sin(step) * radius
        z = start_location[2] + z_step

        pos_list.append(Vector((x, y, z)))

        step += step_angle
        z_step += height / adaptive_resolution

        radius += radius_step

    return pos_list


def make_spline(obj, pos_list, spline_type, del_old=False):
    """Creates a spline for a curve or updates it"""
    # If delete already existing spline
    if del_old and obj.splines:
        spline = obj.splines[0]
        obj.splines.remove(spline)

    polyline = obj.splines.new(spline_type)
    polyline.points.add(len(pos_list) - 1)
    for counter, pos in enumerate(pos_list):
        polyline.points[counter].co = (pos[0], pos[1], pos[2], 1)


def get_all_children(obj, children):
    ''' Recursively gets all children under a object. '''
    if obj.children:
        for child in obj.children:
            if child not in children:
                children.append(child)
                if child.children:
                    children.extend(get_all_children(child, children))
    return children


def message_box(message='', title='', icon='INFO'):
    ''' Creates a message box '''

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def create_space_name(name, iterable):
    ''' Checks for a name in a iterable, if that string is found it
    adds a space to the end of that name and tries again.

    :param name: name you want to check.
    :return: name with extra spaces at end.
    '''

    if name in [n for n in iterable]:
        name += ' '
        name = create_space_name(name, iterable)
    return name


def create_sub_collection(collection, name):
    ''' Creates a sub collection to a existing collection.

    :param collection: The collection to create a sub collection for.
    :return: The sub collection created
    '''
    sub_col = bpy.data.collections.new(name)
    collection.children.link(sub_col)
    return sub_col


def get_all_col_names():
    ''' Returns a list of all collection names. '''
    return [c.name for c in bpy.data.collections]


def get_global_work_collection():
    ''' Returns the "Work" collection if it exists, otherwise it is created and returned.'''
    for coll in bpy.context.scene.collection.children:
        if fnmatch(coll.name, 'Work Global*'):
            return coll

    # Check for old naming convention
    for coll in bpy.context.scene.collection.children:
        if fnmatch(coll.name, 'Work*'):
            return coll

    new_global_work_col = bpy.data.collections.new(create_space_name('Work Global', get_all_col_names()))
    bpy.context.scene.collection.children.link(new_global_work_col)
    return new_global_work_col


def show_objects(show: bool, objects):
    ''' Toggles the visibility of objects. '''
    if not hasattr(objects, '__iter__'):
        objects = [objects]

    for obj in objects:
        obj.hide_set(not show)


def show_collections(show: bool, collections):
    ''' Toggles the visibility of collections. '''
    if not hasattr(collections, '__iter__'):
        collections = [collections]

    for col in collections:
        col.hide_viewport = not show


def is_socket(obj):
    """Returns true if the given object is a Socket, otherwise false."""
    return obj.type == 'EMPTY' and obj.name.startswith(SOCKET_PREFIX)


def get_scene_scale_modifier():
    """ Returns a scaling factor to match Unreal units based on the Blender scene units. """
    return bpy.context.scene.unit_settings.scale_length * 100.0
