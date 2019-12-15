"""Embark Studios Contextual Connect."""

import bmesh
import bpy


class ConnectContextual(bpy.types.Operator):
    """Use a contextually-appropriate action to connect mesh elements"""
    bl_idname = "mesh.connect_contextual"
    bl_label = "Connect Contextual"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        """Execute the Connect Contextual operator."""

        select_mode = context.tool_settings.mesh_select_mode
        mesh = context.active_object.data
        bm = bmesh.from_edit_mesh(mesh)
        result = None

        # Vertex mode
        if select_mode[0]:
            result = self._connect_verts(bm)
        # Edge mode
        elif select_mode[1]:
            result = self._connect_edges(bm)

        if not result:
            return {'CANCELLED'}

        # Select the new geometry
        bm.select_history.clear()
        bmesh.update_edit_mesh(mesh)
        if 'edges' in result and result['edges']:
            for edge in bm.edges:
                edge.select = edge in result['edges']
        elif 'faces' in result and result['faces']:
            for face in bm.faces:
                face.select = face in result['faces']
        elif 'geom_inner' in result and result['geom_inner']:
            for edge in bm.edges:
                edge.select = edge in result['geom_inner']

        return {'FINISHED'}

    def _connect_verts(self, bm):
        sel = [vert for vert in bm.verts if vert.select]
        if len(sel) > 1:
            # TODO: Consider bmesh.ops.triangulate for faces where all verts are selected
            result = bmesh.ops.connect_verts(bm, verts=sel)
            return result

        self.report({'WARNING'}, 'Select at least 2 vertices to connect!')
        return None

    @staticmethod
    def _get_valid_edge_selection(bm):
        sel_edges = [edge for edge in bm.edges if edge.select]
        if len(sel_edges) == 1:
            return sel_edges
        sel = []
        for edge in sel_edges:
            found = False
            for face in edge.link_faces:
                for face_edge in face.edges:
                    if face_edge != edge and face_edge in sel_edges:
                        found = True
                        break
                if found:
                    break
            if found:
                sel.append(edge)
        return sel

    @classmethod
    def _get_next_boundary_edge(cls, boundary, vert):
        for edge in vert.link_edges:
            if edge.is_boundary and edge not in boundary:
                boundary.append(edge)
                cls._get_next_boundary_edge(boundary, edge.other_vert(vert))

    @classmethod
    def _get_boundary_edges(cls, edge):
        boundary = [edge]
        for vert in edge.verts:
            cls._get_next_boundary_edge(boundary, vert)
        return boundary

    def _connect_edges(self, bm):
        sel = self._get_valid_edge_selection(bm)
        # If a single edge is selected, either fill it if it's a boundary edge, or otherwise spin it
        if len(sel) == 1:
            if sel[0].is_boundary:
                boundary = self._get_boundary_edges(sel[0])
                result = bmesh.ops.holes_fill(bm, edges=boundary, sides=len(boundary))
                return result
            result = bmesh.ops.rotate_edges(bm, edges=sel, use_ccw=False)
            return result

        if len(sel) > 1:
            result = bmesh.ops.subdivide_edges(bm, edges=sel, cuts=1)
            return result

        self.report({'WARNING'}, 'Select at least 2 valid edges to connect!')
        return None

    @classmethod
    def poll(cls, context):
        """Return True if the selection is valid for operator execution, otherwise False."""
        return (context.object is not None
                and context.object.select_get() is True
                and context.view_layer.objects.active is not None
                and context.view_layer.objects.active.type == 'MESH'
                and context.view_layer.objects.active.mode == 'EDIT')


def menu_draw(self, context):
    """Create the menu item."""
    self.layout.operator(ConnectContextual.bl_idname)


REGISTER_CLASSES = (
    ConnectContextual,
)
