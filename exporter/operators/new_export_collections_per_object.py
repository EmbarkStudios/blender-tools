"""Exporter operators and UI types."""

from os import path
import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import Operator
from .. import constants
from ..export_collection import get_export_filename
from ..functions import check_path, create_export_collection
from ...utils.functions import remove_numeric_suffix


class EmbarkNewExportCollectionsPerObject(Operator):
    """Creates a new Export Collection for each of the currently-selected objects."""

    bl_idname = "object.embark_new_export_collections_per_object"
    bl_label = "New Export Collection per Object"
    bl_description = "Creates a new Export Collection for each of the currently-selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    _max_previews = 10
    _name_previews = []
    _scene_name = ""

    def _scene_name_changed(self, context):
        if not self.use_scene_name and not self.use_object_name:
            self.use_object_name = True

    def _object_name_changed(self, context):
        if not self.use_object_name:
            self.use_scene_name = True
            self.use_numeric_suffix = True

    def _numeric_suffix_changed(self, context):
        if not self.use_numeric_suffix:
            self.use_object_name = True

    directory: StringProperty(subtype='DIR_PATH')
    export_immediately: BoolProperty(
        name="Export Immediately",
        description="Export this collection immediately",
        default=True,
    )
    export_type: EnumProperty(name="Type", items=constants.EXPORT_TYPES, default=constants.STATIC_MESH_TYPE)
    filter_glob: StringProperty(default="*.fbx;*.obj")
    use_scene_name: BoolProperty(
        name="Use Scene Name",
        description="Include the Blender scene's name as the first part of the export file name",
        default=False,
        update=_scene_name_changed,
    )
    use_object_name: BoolProperty(
        name="Use Object Name",
        description="Include the object's name in the export file name",
        default=True,
        update=_object_name_changed,
    )
    use_object_origin: BoolProperty(
        name="Use Object Origin",
        description="Use each object's origin as the origin of the FBX, instead of the scene origin",
        default=True
    )
    use_numeric_suffix: BoolProperty(
        name="Use Numeric Suffix",
        description="Include a numeric suffix at the end of the export file name",
        default=False,
        update=_numeric_suffix_changed,
    )
    show_valid_objects: BoolProperty(
        name="Valid Objects",
        description="Show a preview of the objects that will be exported",
        default=True,
    )
    show_invalid_objects: BoolProperty(
        name="Invalid Objects",
        description="Show a list of the objects that will not be exported",
        default=False,
    )

    def draw(self, context):
        """Draws the Operator properties."""
        self.layout.prop(self, constants.PROP_EXPORT_TYPE, expand=True)
        self.layout.label(text=f"Exports in {constants.EXPORT_FILE_TYPES[self.export_type]} format")
        self.layout.prop(self, "use_object_origin")
        self.layout.prop(self, "export_immediately")

        self.layout.label(text="Name Options:")
        self.layout.prop(self, "use_scene_name")
        self.layout.prop(self, "use_object_name")
        self.layout.prop(self, "use_numeric_suffix")

        duplicate_names = []
        num_sel = len(bpy.context.selected_objects)
        self._name_previews = []
        invalid_objs = []
        for obj in bpy.context.selected_objects:
            if obj.type != "MESH":
                invalid_objs.append(obj)
                continue
            export_name = self._get_export_name(obj)
            if export_name in self._name_previews and export_name not in duplicate_names:
                duplicate_names.append(export_name)
            self._name_previews.append(export_name)

        self.layout.label(text=f"Operation will create {num_sel - len(invalid_objs)} Export Collections:")
        if duplicate_names:
            self.layout.label(text="WARNING: Duplicate names detected!", icon='ERROR')

        self._draw_export_previews(duplicate_names)
        if invalid_objs:
            self._draw_invalid_objs(invalid_objs)

    def execute(self, context):
        """Creates a new Export Collection from the selection, optionally exporting it if requested."""
        collections = []
        self._name_previews = []
        for obj in bpy.context.selected_objects:
            if obj.type != "MESH":
                continue
            export_name = self._get_export_name(obj)
            self._name_previews.append(export_name)
            collection = create_export_collection(export_name, self.directory, self.export_type, [obj])
            self.report({'INFO'}, f"Successfully created '{collection.name}'")
            collections.append(collection)

        if self.export_immediately:
            for collection in collections:
                if collection.export() == {'FINISHED'}:
                    self.report({'INFO'}, f"Successfully exported '{collection.name}'")
                else:
                    self.report({'ERROR'}, f"Failed to export '{collection.name}'! See System Console.")

        return {'FINISHED'}

    def invoke(self, context, event):
        """Invokes a file browser with this Operator's properties."""
        if not check_path(self):
            return {'CANCELLED'}
        self._scene_name = path.splitext(path.basename(bpy.data.filepath))[0]
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        """Only allows this operator to execute if there is a valid selection."""
        return context.selected_objects

    def _get_export_name(self, obj):
        """Returns the export name with parts based on the options."""
        name_parts = []
        if self.use_scene_name:
            name_parts.append(self._scene_name)
        if self.use_object_name:
            name_parts.append(remove_numeric_suffix(obj.name))
        if self.use_numeric_suffix:
            base_name = "_".join(name_parts)
            i = 1
            test_name = "{}_{:02d}".format(base_name, i)
            # TODO: Check export folder for existing names, and export collections already in scene
            while test_name in self._name_previews:
                i += 1
                test_name = "{}_{:02d}".format(base_name, i)
            name_parts.append("{:02d}".format(i))
        return "_".join(name_parts)

    def _draw_export_previews(self, duplicate_names):
        """Draws a panel showing preview names of valid exports."""
        box = self.layout.box()
        expand_icon = 'DOWNARROW_HLT' if self.show_valid_objects else 'RIGHTARROW'
        box.prop(self, "show_valid_objects", icon=expand_icon, emboss=False)
        if not self.show_valid_objects:
            return

        displayed_names = []
        for export_name in self._name_previews:
            icon = 'NONE' if export_name not in duplicate_names else 'ERROR'
            box.label(text=get_export_filename(export_name, self.export_type), icon=icon)
            displayed_names.append(export_name)
            if len(displayed_names) >= self._max_previews:
                box.label(text=f"...and {len(self._name_previews) - len(displayed_names)} more")
                break

    def _draw_invalid_objs(self, invalid_objs):
        """Draws a panel showing names and types of invalid objects."""
        self.layout.label(text=f"{len(invalid_objs)} object(s) not valid for export:", icon='ERROR')
        box = self.layout.box()
        expand_icon = 'DOWNARROW_HLT' if self.show_invalid_objects else 'RIGHTARROW'
        box.prop(self, "show_invalid_objects", icon=expand_icon, emboss=False)
        if self.show_invalid_objects:
            for obj in invalid_objs:
                box.label(text=f"{obj.name} ({obj.type})")


def menu_draw(self, context):
    """Draw the operator as a menu item."""
    self.layout.operator(EmbarkNewExportCollectionsPerObject.bl_idname, icon=constants.GROUPS_ICON)
