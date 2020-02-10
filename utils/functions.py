"""General-use shared functions for the Embark Addon."""


from math import sin, cos, pi
from re import split
import bpy
from mathutils import Vector


TWO_PI = pi * 2


class SceneState():  # pylint: disable=too-few-public-methods
    """Class for storing and restoring scene selection state."""

    def __init__(self):
        """Store the main context's active object, edit object and selection."""
        self.active_object = bpy.context.view_layer.objects.active
        self.edit_object = bpy.context.edit_object
        if self.edit_object:
            bpy.ops.object.mode_set(mode='OBJECT')
        self.selected_objects = bpy.context.selected_objects

    def restore(self):
        """Reset the main context's active, edit and selected objects to those stored in this `SceneState` object."""
        bpy.ops.object.select_all(action='DESELECT')
        for obj in self.selected_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = self.active_object
        if self.edit_object:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.context.view_layer.objects.active = self.edit_object


def export_gltf(filepath):
    """Export a glTF with standardized settings."""
    return bpy.ops.export_scene.gltf(
        export_format='GLB',
        ui_tab='GENERAL',
        export_copyright="",
        export_image_format='PNG',
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
