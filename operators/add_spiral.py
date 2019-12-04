"""Operators for creating Spiral curve shapes."""

import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, IntProperty, StringProperty
from bpy_extras.object_utils import AddObjectHelper
from ..utils.functions import create_polar_coordinates, make_spline
from ..utils.ui import get_icon


SPIRAL_TYPE = "spiral"


class AddSpiralObject(Operator, AddObjectHelper):  # pylint: disable=too-few-public-methods
    """Create a new Spiral object."""

    bl_idname = "curve.add_spiral"
    bl_label = "Spiral"
    bl_options = {"REGISTER", "UNDO"}

    def _update(self, context):  # pylint: disable=no-self-use
        """Update the spline when a property changes."""
        obj = context.object
        if obj and obj.type in ["CURVE"]:
            coords = create_polar_coordinates(obj.radius, obj.height, obj.resolution, obj.scalar, obj.loops)
            make_spline(obj.data, coords, "POLY", True)
            # bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

    bpy.types.Object.radius = FloatProperty(
        name="Radius",
        description="Radius of the spiral",
        default=1.0,
        update=_update
    )

    bpy.types.Object.height = FloatProperty(
        name="Height",
        description="Height of the spiral",
        default=1.0,
        update=_update
    )

    bpy.types.Object.resolution = IntProperty(
        name="Resolution",
        description="Number of vertices in the spiral",
        default=32,
        min=3,
        update=_update
    )

    bpy.types.Object.scalar = FloatProperty(
        name="Scalar",
        description="Scalar value along the spiral",
        default=0.0,
        update=_update
    )

    bpy.types.Object.loops = IntProperty(
        name="Loops",
        description="Amount of loops in the spiral",
        default=2,
        min=1,
        update=_update
    )

    def execute(self, context):  # pylint: disable=no-self-use
        """Create the new Spiral object."""
        # Set up Curve Object
        curve_obj = bpy.data.curves.new('myCurve', "CURVE")
        curve_obj.dimensions = "3D"
        obj = bpy.data.objects.new("Spiral", curve_obj)
        bpy.context.collection.objects.link(obj)

        # Set init properties
        bpy.types.Object.my_type = StringProperty(options={"HIDDEN"})
        obj.my_type = SPIRAL_TYPE
        obj.resolution = 32
        obj.height = 1.0
        obj.radius = 1.0
        obj.scalar = 0.0
        obj.loops = 2

        start_loc = bpy.context.scene.cursor.location

        # Set up Curve Spline
        pos_list = create_polar_coordinates(1.0, 1.0, 50, 0.0, 2, start_loc)
        make_spline(curve_obj, pos_list, "POLY", False)
        # Select Curve
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

        return {'FINISHED'}


class SpiralPropertiesPanel(bpy.types.Panel):
    """Properties panel for Spiral objects."""

    bl_idname = "OBJECT_PT_Spiral_Properties"
    bl_label = "Spiral Properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    @classmethod
    def poll(cls, context):
        """Check if selected object is a Spiral type."""
        return context.object and context.object.get("my_type") is SPIRAL_TYPE

    def draw(self, context):
        """Draw the properties for the selected Spiral."""
        obj = context.object
        self.layout.prop(obj, "radius", text="Radius")
        self.layout.prop(obj, "height", text="Height")
        self.layout.prop(obj, "resolution", text="Resolution")
        self.layout.prop(obj, "scalar", text="Scalar")
        self.layout.prop(obj, "loops", text="Loops")


def menu_draw(self, context):
    """Draw the menu item for adding a new Spiral object."""
    self.layout.operator(AddSpiralObject.bl_idname, icon_value=get_icon('spring_icon'))


REGISTER_CLASSES = (
    AddSpiralObject,
    SpiralPropertiesPanel
)
