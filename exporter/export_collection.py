"""Module for handling operations on Export Collections."""


from os import makedirs, path
from re import split
import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Collection, Object
from . import constants
from ..utils import get_source_path
from ..utils.functions import export_fbx, export_obj, remove_numeric_suffix, SceneState, unlink_collection


RELATIVE_ROOT = ".\\"


def get_export_filename(export_name, export_type, include_extension=True):
    """Gets a preview of the export filename based on `export_name` and `export_type`."""
    export_name = validate_export_name(export_name)
    extension = f".{constants.EXPORT_FILE_TYPES[export_type].lower()}" if include_extension else ""
    if export_type in [constants.MID_POLY_TYPE, constants.HIGH_POLY_TYPE]:
        return f"{export_name}_{export_type}{extension}"
    return f"{export_type}_{export_name}{extension}"


def validate_export_name(export_name):
    """Validate `export_name` and return the fixed up result."""
    # Use scene name if the export name was empty
    if not export_name:
        export_name = path.splitext(path.basename(bpy.data.filepath))[0]

    # Replace special characters with underscores
    tokens = split(r'[_\-\.;|,\s]', export_name)
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
    if new_tokens[0].upper() in constants.EXPORT_FILE_TYPES.keys():
        if len(new_tokens) == 1:
            export_name = path.splitext(path.basename(bpy.data.filepath))[0]
        else:
            export_name = "_".join(new_tokens[1:])

    return export_name


def _validate_path(export_path):
    """Verifies that the export path is under the Embark Addon's project source path."""
    source_path = get_source_path()
    if not source_path:
        print(f"Warning: Source path was not defined!")
        return RELATIVE_ROOT

    if not export_path:
        return RELATIVE_ROOT

    source_path = path.normpath(source_path)
    if not path.isabs(export_path):
        export_path = path.join(source_path, export_path)

    export_path = path.normpath(export_path)
    if export_path.lower().startswith(source_path.lower()):
        relpath = path.relpath(export_path, source_path)
        return f"{RELATIVE_ROOT}{relpath}" if relpath != "." else RELATIVE_ROOT
    print(f"Warning: Export path must be relative to: {source_path}")
    return RELATIVE_ROOT


def _export_name_changed(self, context):
    ExportCollection(self).rename()


def _export_path_changed(self, context):
    if not self.export_path.startswith(RELATIVE_ROOT):
        validated_path = _validate_path(self.export_path)
        self.export_path = validated_path


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


# Add export origin property to Object for use on Empty
Object.is_export_origin = BoolProperty(name="Is Export Origin", default=False)


class ExportCollection(Collection):
    """Wrapper around Collection data type for some convenience functions."""

    export_name = ""
    export_path = ""
    export_type = ""
    name = ""
    objects = []

    def __init__(self, collection):
        if not isinstance(collection, Collection):
            raise TypeError("Not a Collection type")

    def add_objects(self, objects):
        """Adds `objects` to this Export Collection."""
        num_added = 0
        for obj in objects:
            if obj.name not in self.objects:
                self.objects.link(obj)  # pylint: disable=no-member
                num_added += 1
        return num_added

    def delete(self):
        """Deletes this Export Collection from the scene."""
        unlink_collection(bpy.context.scene.collection, self)

        # Also remove the top-level export collection container if it's empty
        if constants.EXPORT_COLLECTION_NAME in bpy.context.scene.collection.children:
            exp_col = bpy.data.collections[constants.EXPORT_COLLECTION_NAME]
            if not exp_col.children:
                unlink_collection(bpy.context.scene.collection, exp_col)

    def export(self):
        """Exports this Export Collection based on its stored properties."""
        export_path = self.get_full_export_path()
        if not export_path:
            return {'CANCELLED'}

        origin_objects = self.origin_objects
        if not origin_objects:
            print(f"Error: No Origin object found for Export Collection '{self.name}'")
            return {'CANCELLED'}

        state = SceneState()
        self._pre_export(origin_objects)

        # Create target folder if it doesn't exist
        target_folder = path.dirname(export_path)
        if not path.isdir(target_folder):
            makedirs(target_folder)
            print(f"Created new folder: {target_folder}")

        # Export the contents of the Collection as appropriate
        export_method = export_fbx
        if self.export_type in [constants.MID_POLY_TYPE, constants.HIGH_POLY_TYPE]:
            export_method = export_obj

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
        for obj in origin_objects:
            self.objects.unlink(obj)  # pylint: disable=no-member

        bpy.ops.object.select_all(action='DESELECT')

        inverse_origin_matrix = origin_objects[0].matrix_world.copy()
        inverse_origin_matrix.invert_safe()
        for obj in self.top_level_objects:
            obj.matrix_world = inverse_origin_matrix @ obj.matrix_world

        for obj in self.objects:
            obj.select_set(True)
            trimmed_name = remove_numeric_suffix(obj.name)
            if obj.name != trimmed_name:
                obj.name = trimmed_name

    def _post_export(self, origin_objects):
        """Reset object transforms."""
        origin_matrix = origin_objects[0].matrix_world.copy()
        for obj in self.top_level_objects:
            obj.matrix_world = origin_matrix @ obj.matrix_world

        for obj in origin_objects:
            self.objects.link(obj)  # pylint: disable=no-member

    def get_full_export_path(self, only_folder=False):
        """Returns the absolute export path as a string.

        :param only_folder: If `True`, the file name will not be included in the result.
        """
        source_path = get_source_path()
        if not source_path:
            print("Error: Please set up the 'Project source folder' in the Embark Addon preferences!")
            return ""

        folder = path.normpath(path.join(source_path, self.export_path))
        if only_folder:
            return folder
        file_name = get_export_filename(self.export_name, self.export_type)
        return path.join(folder, file_name)

    def remove_objects(self, objects):
        """Removes `objects` from this Export Collection."""
        num_removed = 0
        for obj in objects:
            if obj.name in self.objects:
                # Make sure the object doesn't get unlinked from the scene entirely
                if obj.name not in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.link(obj)
                self.objects.unlink(obj)  # pylint: disable=no-member
                num_removed += 1
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
        if bpy.context.edit_object:
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        for obj in self.objects:
            obj.select_set(True)

        # Set the active object to something in the new selection, if it wasn't already
        active_obj = getattr(bpy.context.view_layer.objects.active, "name", "")
        if self.objects and (not active_obj or active_obj not in self.objects):
            bpy.context.view_layer.objects.active = self.objects[0]

    @property
    def top_level_objects(self):
        """Returns a list of objects that are at the top level of this Export Collection."""
        return [obj for obj in self.objects if not obj.parent or obj.parent.name not in self.objects]

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
