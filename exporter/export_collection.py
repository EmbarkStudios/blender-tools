"""Module for handling operations on Export Collections."""


from os import makedirs, path
from math import pi
from re import split
import itertools
import fnmatch
import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Collection, Object
from . import constants
from ..utils.path_manager import make_project_path_absolute, validate_path
from ..utils.functions import (
    get_export_extension,
    get_export_method,
    export_fbx_apply_transform,
    remove_numeric_suffix,
    SceneState,
    unlink_collection,
    create_space_name,
    create_sub_collection,
    get_all_col_names,
    get_global_work_collection,
    get_all_children,
    get_scene_scale_modifier,
    show_objects,
    show_collections,
    is_socket,
)


def get_export_filename(export_name, export_type, include_extension=True):
    """Gets a preview of the export filename based on `export_name` and `export_type`."""
    export_name = validate_export_name(export_name)
    extension = ("." + get_export_extension(export_type).lower()) if include_extension else ""
    return f"{export_type}_{export_name}{extension}"


def validate_export_name(export_name):
    """Validate `export_name` and return the fixed up result."""
    # Use scene name if the export name was empty
    if not export_name:
        export_name = path.splitext(path.basename(bpy.data.filepath))[0]

    # Replace special characters with underscores
    tokens = split(r'[_\\.;|,\s]', export_name)
    new_tokens = []
    for token in tokens:
        if token:
            new_token = token[0].upper()
            if len(token) > 1:
                new_token += token[1:]
            new_tokens.append(new_token)
    export_name = "_".join(new_tokens)
    if not new_tokens:
        new_tokens.append(path.splitext(path.basename(bpy.data.filepath))[0])

    # Strip type prefix if someone typed it in manually
    prefixes = [export_type[0] for export_type in constants.EXPORT_TYPES]
    if new_tokens[0].upper() in prefixes:
        if len(new_tokens) == 1:
            export_name = path.splitext(path.basename(bpy.data.filepath))[0]
        else:
            export_name = "_".join(new_tokens[1:])

    return export_name


def _export_name_changed(self, context):
    ExportCollection(self).rename()


def _export_path_changed(self, context):
    validated_path = validate_path(self.export_path)
    # Only change the path if it was valid and had actually changed
    if validated_path:
        if validated_path != self.export_path:
            self.export_path = validated_path
    else:
        print(f"Warning: Export path '{self.export_path}' is not relative to Project source folder!")


def _export_type_changed(self, context):
    ExportCollection(self).rename()


# Add export properties to Collection
Collection.export_name = StringProperty(
    name="Name",
    description="Base name of the Export Collection, will be used as part of the output file name",
    default="",
    update=_export_name_changed,
)
Collection.export_path = StringProperty(
    name="Path",
    description="Path of the Export Collection, relative to the Project source folder from the Addon preferences",
    subtype='DIR_PATH',
    default="",
    update=_export_path_changed,
)
Collection.export_type = EnumProperty(
    name="Type",
    description="The type of content this Export Collection contains, used to determine file type and settings",
    items=constants.EXPORT_TYPES,
    default=constants.STATIC_MESH_TYPE,
    update=_export_type_changed,
)
Collection.export_panel_expanded = BoolProperty(
    name="Expanded in Export Panel",
    description="If True, this collection will be expanded in the Embark Export Panel",
    default=False,
)
Collection.apply_transform = BoolProperty(
    name='Apply Transform',
    description='Applies transform to work with UE4s "Transform Vertex to Absolute" import setting.',
    default=False,
)

# Add export origin property to Object for use on Empty
Object.is_export_origin = BoolProperty(name="Is Export Origin", default=False)


class ExportCollection(Collection):
    """Wrapper around Collection data type for some convenience functions."""

    export_name = ""
    export_path = ""
    export_type = ""
    name = ""
    apply_transform = False
    objects = []
    tmp_objects = []
    instance_offset = []
    lod_group = None

    def __init__(self, collection):
        if not isinstance(collection, Collection):
            raise TypeError("Not a Collection type")

    def add_objects(self, objects):
        """Adds `objects` to this Export Collection."""
        num_added = 0

        for obj in objects:
            # Skip adding export origin as mesh
            if obj.is_export_origin:
                continue
            # Unlink from current collection
            if obj.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(obj)
            for coll in bpy.data.collections:
                if obj.name in coll.objects:
                    coll.objects.unlink(obj)

            # Check if mesh is prefixed with collision name
            if obj.name.split('_')[0] in ['UBX', 'UCP', 'USP', 'UCX']:
                if obj.name not in self['Collision'].objects:
                    self['Collision'].objects.link(obj)
                    num_added += 1

            elif obj.name not in self['Mesh']['LODS']['LOD0'].objects:
                self['Mesh']['LODS']['LOD0'].objects.link(obj)  # pylint: disable=no-member
                num_added += 1

        return num_added

    def delete(self):
        """Deletes this Export Collection from the scene."""
        # Move ExportCollections objects into global work collection
        global_work_collection = get_global_work_collection()
        for obj in self.export_objects:
            if obj.name not in global_work_collection.objects:
                global_work_collection.objects.link(obj)
        unlink_collection(bpy.context.scene.collection, self)

        # Also remove the top-level export collection container if it's empty
        if constants.EXPORT_COLLECTION_NAME in bpy.context.scene.collection.children:
            exp_col = bpy.data.collections[constants.EXPORT_COLLECTION_NAME]
            if not exp_col.children:
                unlink_collection(bpy.context.scene.collection, exp_col)

    def export(self):
        """Exports this Export Collection based on its stored properties."""
        export_path = self.get_full_export_path()
        collections_to_export = [self["Mesh"], self["Collision"]] + list(self["Mesh"].children)
        if not export_path:
            return {'CANCELLED'}

        origin_objects = self.origin_objects
        if not origin_objects:
            print(f"Error: No Origin object found for Export Collection '{self.name}'")
            return {'CANCELLED'}

        state = SceneState(objects=self.export_objects, collections=collections_to_export)
        show_objects(True, self.export_objects)
        show_collections(True, collections_to_export)
        self._pre_export(origin_objects)

        # Create target folder if it doesn't exist
        target_folder = path.dirname(export_path)
        if not path.isdir(target_folder):
            makedirs(target_folder)
            print(f"Created new folder: {target_folder}")

        # Export the contents of the Collection as appropriate
        export_method = get_export_method(self.export_type)

        # TODO: Consider moving this into get_export_method
        if get_export_extension(self.export_type) is 'FBX' and self.apply_transform:
            export_method = export_fbx_apply_transform

        result = {'CANCELLED'}
        try:
            result = export_method(export_path)
        except:  # pylint: disable=bare-except
            print(f"Error occurred while trying to export '{self.name}'. See System Console for details.")

        self._post_export(origin_objects)
        state.restore()

        if result == {'FINISHED'}:
            print(f"Exported Collection '{self.name}' to: {export_path}")

        return result

    def _pre_export(self, origin_objects):
        """Transform the objects based on the origin."""
        self._setup_lod_export()

        for obj in origin_objects:
            self.objects.unlink(obj)  # pylint: disable=no-member

        self._name_collision_objects()
        bpy.ops.object.select_all(action='DESELECT')

        inverse_origin_matrix = origin_objects[0].matrix_world.copy()
        inverse_origin_matrix.invert_safe()
        for obj in self.top_level_objects:
            obj.matrix_world = inverse_origin_matrix @ obj.matrix_world

        for obj in self.export_objects:
            obj.select_set(True)
            trimmed_name = remove_numeric_suffix(obj.name)
            if obj.name != trimmed_name:
                obj.name = trimmed_name
            if not self.apply_transform:
                # Scale down and rotate socket, if transforms are not to be applied.
                if fnmatch.fnmatchcase(obj.name, "SOCKET*"):
                    if not obj.parent:
                        obj.matrix_world = inverse_origin_matrix @ obj.matrix_world
                    obj.delta_scale /= get_scene_scale_modifier()
                    obj.rotation_euler[0] += pi / 2

    def _setup_lod_export(self):
        """ Merges, flattens and parents all LOD collections to a LodGroup Empty."""
        # Create Lod group Empty
        lod_group = bpy.data.objects.new(f"{self.export_name}_LodGroup", None)
        self.objects.link(lod_group)  # pylint: disable=no-member
        lod_group.matrix_world = self.origin_objects[0].matrix_world.copy()
        lod_group["fbx_type"] = "LodGroup"
        self.tmp_objects.append(lod_group)
        self.lod_group = lod_group

        # Iterate over lod collections
        for lod in self["Mesh"]["LODS"].items():
            key = lod[0]
            col = lod[1]

            base_objs = []
            if col.objects:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in col.objects:
                    if obj.type in ['MESH', 'CURVE']:
                        if not obj.parent:
                            obj.select_set(True)
                            base_objs.append(obj)

                # Create Lod Object
                lod_obj = bpy.data.objects.new(f"{self.export_name}_{key}", None)
                col.objects.link(lod_obj)
                lod_obj.matrix_world = self.origin_objects[0].matrix_world.copy()
                lod_obj.select_set(True)
                bpy.context.view_layer.objects.active = lod_obj

                bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)

                for obj in base_objs:
                    obj.select_set(False)

                # Parent Lod Object to Lod group Empty
                lod_group.select_set(True)
                bpy.context.view_layer.objects.active = lod_group
                bpy.ops.object.parent_set(type="OBJECT", keep_transform=True)

                self.tmp_objects.append(lod_obj)

    def _name_collision_objects(self):
        """ Names all the collision objects correctly. """
        count = 0
        # find first best MESH/CURVE object under LOD0 Empty
        lod_name = ""
        for obj in self.all_objects[f"{self.export_name}_LOD0"].children:
            if obj.type in ["MESH", "CURVE"]:
                lod_name = obj.name
                break

        for obj in self["Collision"].objects:
            collision_type = "UCX" if obj.name[0:3] not in ["UBX", "UCP", "USP"] else obj.name[0:3]
            obj.name = f"{collision_type}_{lod_name}_" + "%003d" % count
            count += 1

    def _post_export(self, origin_objects):
        """Reset object transforms, removes temporary export objects, and clears data."""
        origin_matrix = origin_objects[0].matrix_world.copy()
        for obj in self.top_level_objects:
            obj.matrix_world = origin_matrix @ obj.matrix_world

        for obj in origin_objects:
            self.objects.link(obj)  # pylint: disable=no-member

        bpy.ops.object.delete({"selected_objects": self.tmp_objects})
        self.tmp_objects.clear()
        self.lod_group = None

        for obj in self.export_objects:
            if not self.apply_transform:
                # Scale up and rotate back socket, if transforms are not to be applied.
                if fnmatch.fnmatchcase(obj.name, "SOCKET*"):
                    if not obj.parent:
                        obj.matrix_world = origin_matrix @ obj.matrix_world
                    obj.delta_scale *= get_scene_scale_modifier()
                    obj.rotation_euler[0] -= pi / 2

    def get_full_export_path(self):
        """Returns the absolute export path as a string."""

        folder = make_project_path_absolute(self.export_path)
        if folder:
            file_name = get_export_filename(self.export_name, self.export_type)
            return path.join(folder, file_name)
        else:
            print(f"Error: Invalid export path '{self.export_path}'")
            return None

    def remove_objects(self, objects):
        """Removes `objects` from this Export Collection."""
        scene_state = SceneState()
        bpy.ops.object.select_all(action='DESELECT')
        num_removed = 0
        global_work_collection = get_global_work_collection()

        lod_cols = [lod for lod in self['Mesh']['LODS'].values()]
        collision_col = self['Collision']
        work_col = self['Work']

        for obj in objects:
            objs = [obj]

            for col in itertools.chain(lod_cols, [collision_col, work_col]):
                if obj.name in col.objects:
                    # Unparenting
                    if obj.parent:
                        obj.select_set(True)
                        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                        obj.select_set(False)

                    # Select all child objects for removal from collection
                    if obj.children:
                        objs = get_all_children(obj, objs)

                    for ulink_obj in objs:
                        # Make sure the object doesn't get unlinked from the scene entirely
                        if ulink_obj.name not in global_work_collection.objects:
                            global_work_collection.objects.link(ulink_obj)
                        if ulink_obj.name in col.objects:
                            col.objects.unlink(ulink_obj)  # pylint: disable=no-member
                            num_removed += 1
        scene_state.restore()
        return num_removed

    def rename(self):
        """Renames the Export Collection and fixes up the origin object name."""
        valid_name = validate_export_name(self.export_name)
        if self.export_name != valid_name:
            self.export_name = valid_name
        self.name = f"{get_export_filename(self.export_name, self.export_type, include_extension=False)}"

        origin_objects = self.origin_objects
        if origin_objects:
            origin_objects[0].name = f".{self.name}.ORIGIN"

    def select(self):
        """Selects the contents of this Export Collection."""
        bpy.ops.object.select_all(action='DESELECT')
        for obj in self.export_objects + self.origin_objects:
            obj.select_set(True)

        # Set the active object to something in the new selection, if it wasn't already
        active_obj = getattr(bpy.context.view_layer.objects.active, "name", "")
        if self.objects and (not active_obj or active_obj not in self.objects):
            bpy.context.view_layer.objects.active = self.objects[0]

    def add_lod_level(self):
        ''' Adds a LOD level to the mesh collection. '''
        num_lods = len(self['Mesh']['LODS'])
        lod_name = f'LOD{num_lods}'
        lod_collection = create_sub_collection(self['Mesh'], create_space_name(lod_name, get_all_col_names()))
        self['Mesh']['LODS'].update({lod_name: lod_collection})

    def get_all_lod_objects(self):
        ''' Returns all objects in LOD collections. '''
        objects = []
        for lod in self['Mesh']['LODS'].values():
            for obj in lod.objects:
                objects.append(obj)
        return objects

    def update_instance_offset(self):
        """Update the Instance Offset to match the Export Collection's origin object."""
        self.instance_offset = self.origin_objects[0].location

    def _update_mesh_collection(self):
        """ Checks if ExportCollection has a Mesh collection, if not it creates one. """
        if not self.get("Mesh"):
            # Try to find and assign manually created Mesh Collection
            for col in self.children:
                if fnmatch.fnmatch(col.name, "Mesh*"):
                    self["Mesh"] = col
                    self["Mesh"]['LODS'] = {}
                    if self["Mesh"].children:
                        for lod in sorted(self["Mesh"].children, key=lambda lod: lod.name):
                            num_lods = len(self['Mesh']['LODS'])
                            lod_name = f'LOD{num_lods}'
                            lod.name = lod_name
                            self['Mesh']['LODS'].update({lod_name: lod})
                    else:
                        for _ in range(0, 3):
                            self.add_lod_level()
                    break

            # Create new Mesh Collection
            if not self.get("Mesh"):
                self["Mesh"] = create_sub_collection(self, create_space_name("Mesh", get_all_col_names()))
                self["Mesh"]['LODS'] = {}
                for _ in range(0, 3):
                    self.add_lod_level()

    def _update_collision_collection(self):
        """ Checks if ExportCollection has a Collision collection, if not it creates one. """
        if not self.get("Collision"):
            # Try to find and assign manually created Collision Collection
            for col in self.children:
                if fnmatch.fnmatch(col.name, "Collision*"):
                    self["Collision"] = col
                    break
            if not self.get("Collision"):
                self['Collision'] = create_sub_collection(self, create_space_name('Collision', get_all_col_names()))

    def _update_work_collection(self):
        """ Checks if ExportCollection has a Work collection, if not it creates one. """
        if not self.get("Work"):
            # Try to find and assign manually created Work Collection
            for col in self.children:
                if fnmatch.fnmatch(col.name, "Work*"):
                    self["Work"] = col
                    break
            if not self.get("Work"):
                self['Work'] = create_sub_collection(self, create_space_name('Work', get_all_col_names()))

    def update_collection_hierarchy(self):
        """ Checks if ExportCollections hierarchy is set up correctly, If not it updates/creates the correct hierarchy.
            This is for easily being able to do changes to the hierarchy without invalidating any users
            old scenes ExportCollections. """
        self._update_mesh_collection()
        self._update_collision_collection()
        self._update_work_collection()

        # Move objects from top level and mesh collection to proper locations
        self.add_objects(list(self.objects) + list(self["Mesh"].objects))

    def set_visible_lod(self, lodnum):
        """ Sets the visible lod collection and hides the others. """
        mesh_col = self.get("Mesh")
        if mesh_col:
            if lodnum == "All":
                for lod in mesh_col["LODS"].values():
                    lod.hide_viewport = False
            else:
                vis_lod = mesh_col["LODS"].get(lodnum)
                if not vis_lod:
                    vis_lod = sorted(mesh_col["LODS"].items())[-1]

                for lod in mesh_col["LODS"].values():
                    if lod is vis_lod:
                        lod.hide_viewport = False
                    else:
                        lod.hide_viewport = True

    def show_top_level_collection(self, colname, show):
        """ Hides or Shows a top level child collection. """
        col = self.get(colname)
        if col and isinstance(col, Collection):
            col.hide_viewport = not show

    def show_mesh_objects(self, show):
        """ Shows or Hides mesh objects inside the Mesh Collection. """
        mesh_col = self.get("Mesh")
        show_objects(show, [obj for obj in mesh_col.all_objects if obj.type == "MESH"])

    def show_socket_objects(self, show):
        """ Shows or Hides socket objects inside the Mesh Collection. """
        mesh_col = self.get("Mesh")
        show_objects(show, [obj for obj in mesh_col.all_objects if is_socket(obj)])

    @property
    def export_objects(self):
        ''' Returns a list of all objects that should be exported. '''
        export_objects = []
        # LOD objects
        export_objects.extend(self["Mesh"].all_objects)
        # Collision objects
        export_objects.extend(self["Collision"].all_objects)
        # Lod Group empty
        if self.lod_group:
            export_objects.append(self.lod_group)

        return export_objects

    @property
    def top_level_objects(self):
        """Returns a list of objects that are at the top level of this Export Collection."""
        top_level_objects = []

        # Lodgroup top level object
        if self.lod_group:
            top_level_objects.append(self.lod_group)
        # Collision top level objects
        top_level_objects.extend([obj for obj in self['Collision'].all_objects if not obj.parent])
        # Work top level objects
        top_level_objects.extend([obj for obj in self['Work'].all_objects if not obj.parent])

        return top_level_objects

    @property
    def origin_objects(self):
        """Returns a list of origin objects in this Export Collection."""
        origin_objects = []
        for obj in self.objects:
            if getattr(obj, "is_export_origin", None):
                if origin_objects:
                    print(f"Warning: Found extra Origin object '{obj.name}' in Export Collection '{self.name}'")
                origin_objects.append(obj)
        return origin_objects

    @property
    def is_selected(self):
        ''' Returns if True/False depending if any object in the Export Collection is selected. '''
        for obj in self.all_objects:
            if obj.select_get():
                return True
        return False
