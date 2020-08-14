import bmesh
from . import gizmos
from bpy.types import (
   GizmoGroup,
)
import numpy as np
import mathutils

fold_point_gizmo_color = (0.9, 0.5, 0.5)
fold_point_gizmo_color_highlight = (1, 0.8, 0.8)

fold_point_create_fold_color = (0, 1, 0)
fold_point_create_fold_color_highlight = (0.5, 1, 0.5)
fold_point_cancel_fold_color = (0.8, 0, 0)
fold_point_cancel_fold_color_highlight = (1, 0.2, 0.2)

fold_point_gizmo_alpha = 1


def calculate_fold_points(ob, selected):
    fold_points = []
    bm = bmesh.from_edit_mesh(ob.data)
    selected = [v for v in bm.verts if v.select][0]

    neighbouring_vertex_edge = []
    for edge in bm.edges:
        other = edge.other_vert(selected)
        if other is not None:
            fold_points.append({
                'type': 'fold_point_half_fold',
                'data': {
                    'location': other.co,
                    'fold_from_vertex': selected.co,
                }
            })
            neighbouring_vertex_edge.append((edge, other))

    edge_to_neighbour_edge = {}
    # TODO: add some way of adding together continuous edges into one edge so
    # that you can fold across vertices in the way which break up
    # straight edges.
    for edge in bm.edges:
        for e, vert in neighbouring_vertex_edge:
            if edge.other_vert(vert) is not None and not edge == e:
                if (e, vert) not in edge_to_neighbour_edge:
                    edge_to_neighbour_edge[(e, vert)] = []
                edge_to_neighbour_edge[(e, vert)].append(edge)
    for inner_edge, vertex in edge_to_neighbour_edge:
        inner_edge_length = (inner_edge.verts[0].co - inner_edge.verts[1].co).length
        for outer_edge in edge_to_neighbour_edge[(inner_edge, vertex)]:
            other_vertex = outer_edge.other_vert(vertex)
            u = (other_vertex.co - vertex.co)
            u.normalize()
            new_point = vertex.co + u*inner_edge_length
            fold_points.append({
                'type': 'fold_point_edge_edge',
                'data': {
                    'location': new_point,
                    'fold_from_vertex': selected.co,
                }
            })
    return fold_points


class FoldOrigamiModelGizmoGroup(GizmoGroup):
    bl_idname = "OBJECT_GGT_light_test"
    bl_label = "Test Light Widget"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'SHOW_MODAL_ALL', 'PERSISTENT'}

    @staticmethod
    def my_target_operator(context):
        wm = context.window_manager
        op = wm.operators[-1] if wm.operators else None
        if isinstance(op, gizmos.OrigamiFoldPointGizmo):
            return op
        return None

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            ob = context.object
            return 'VERT' in bmesh.from_edit_mesh(ob.data).select_mode \
                and (ob and 'origami_model' in ob and ob['origami_model'])
        return False

    def create_or_reuse_fold_point_gizmo(self, location, color, highlight_color):
        # TODO Insert reuse functionality

        mpr = self.gizmos.new(gizmos.OrigamiFoldPointGizmo.bl_idname)
        local_location = location

        def move_get_cb():
            return local_location

        def move_set_cb(value):
            pass

        mpr.target_set_handler("offset", get=move_get_cb, set=move_set_cb)

        mpr.color = color
        mpr.alpha = fold_point_gizmo_alpha

        mpr.color_highlight = highlight_color
        mpr.alpha_highlight = fold_point_gizmo_alpha

        mpr.use_draw_modal = True
        if not hasattr(self, 'gizmo_list'):
            self.gizmo_list = []
        mpr.type = "fold_point"
        mpr.data = location
        self.gizmo_list.append(mpr)
        return mpr

    def create_crease_gizmo(self, bm, start_location, end_vertex):
        pass
        # start_vertex = None
        # for vert in bm.verts:
        #     if start_location == vert.co:
        #         start_vertex = vert
        #         break
        # if start_vertex == None:
        #     raise "terrible error message"
        # mpr = self.gizmos.new(CreaseLineGizmo.bl_idname)

    def setup(self, context):
        self.ui_state = "NONE"

    def refresh(self, context):
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v for v in bm.verts if v.select]
        if len(selected) == 1:
            self.single_vertex_selected(ob, selected[0])
        elif self.ui_state == "SHOW_FOLD_POINTS":
            self.ui_state = "NONE"
            self.hide_all_gizmos()

    def hide_all_gizmos(self):
        for gizmo in self.gizmo_list:
            gizmo.hide = True

    def single_vertex_selected(self, ob, selected):
        self.ui_state = "SHOW_FOLD_POINTS"
        fold_points = calculate_fold_points(ob, selected)

        location = selected.co
        print('creating gizmo at ', location)
        if hasattr(self, 'gizmo_list') and len(self.gizmo_list) > 0:
            self.hide_all_gizmos()

        for fold_point in fold_points:
            mpr = self.create_or_reuse_fold_point_gizmo(
                                                        fold_point['data']['location'],
                                                        fold_point_gizmo_color,
                                                        fold_point_gizmo_color_highlight)
            mpr.type = fold_point['type']
            mpr.data = fold_point['data']

    def gizmo_clicked(self, context, gizmo):
        print('gizmo_clicked, ', self.ui_state)
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v.select for v in bm.verts]
        gizmo_location = gizmo.target_get_value('offset')
        if self.ui_state == "SHOW_FOLD_POINTS":
            for other_gizmo in self.gizmo_list:
                if not other_gizmo == gizmo:
                    other_gizmo.hide = True
                else:
                    other_gizmo.color = fold_point_create_fold_color
                    other_gizmo.color_highlight = fold_point_create_fold_color_highlight

            cancel_gizmo = self.create_or_reuse_fold_point_gizmo(
                                                                 np.array(ob.data.vertices)[selected][0].co,
                                                                 fold_point_cancel_fold_color,
                                                                 fold_point_cancel_fold_color_highlight)
            cancel_gizmo.type = 'cancel'
            cancel_gizmo.data = {'vertex': np.array(ob.data.vertices)[selected][0]}
            print('assigning', cancel_gizmo.data)
            # self.target_get_value('offset')
            # crease = selfget_crease(gizmo.type, gizmo.data)
            print('creating potential crease from:', gizmo.type, gizmo.data)
            self.create_crease_gizmo(bm, mathutils.Vector(gizmo_location), np.array(ob.data.vertices)[selected][0])
            self.ui_state = "SHOW_POTENTIAL_CREASE"
        elif self.ui_state == "SHOW_POTENTIAL_CREASE":
            print('clicked in show_potential_crease state')
            if gizmo.type == "cancel":
                self.single_vertex_selected(ob, gizmo.data['vertex'])
                print('canceled potential crease state')
            else:
                # TODO: do fold based on the crease created
                print('gizmo data', gizmo.data)
                print('gizmo type', gizmo.type)
                # print('do fold from', mathutils.Vector(gizmo.data), \
                # 'to', mathutils.Vector(gizmo.target_get_value("offset")))

    def get_crease(self, start_point_type, data):
        pass
        # fold_from_vertex_location = data['fold_from_vertex']
        # fold_to_vertex_location = data['location']
