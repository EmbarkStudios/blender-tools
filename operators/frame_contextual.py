"""Frame selected or everything depending on context."""
# TODO: This should probably be made as a core change to Blender


import bpy


class FrameContextual(bpy.types.Operator):  # pylint: disable=too-few-public-methods
    """Operator that frames the selected objects, or the entire scene if nothing is selected"""

    bl_idname = "view3d.frame_contextual"
    bl_label = "Frame Contextual"

    def execute(self, context):  # pylint: disable=no-self-use
        """Execute the Frame Contextual operator."""
        sel = context.selected_objects
        if sel:
            bpy.ops.view3d.view_selected(use_all_regions=False)
        else:
            bpy.ops.view3d.view_all(center=False)
        return {'FINISHED'}


def menu_draw(self, context):
    """Create the menu item."""
    self.layout.operator(FrameContextual.bl_idname)


REGISTER_CLASSES = (
    FrameContextual,
)
