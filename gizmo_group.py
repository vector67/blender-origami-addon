import bmesh
from . import gizmos
from bpy.types import (
   GizmoGroup,
)
import numpy as np
import mathutils
import bpy

fold_point_gizmo_color = (0.9, 0.5, 0.5)
fold_point_gizmo_color_highlight = (1, 0.8, 0.8)

fold_point_create_fold_color = (0, 1, 0)
fold_point_create_fold_color_highlight = (0.5, 1, 0.5)
fold_point_cancel_fold_color = (0.8, 0, 0)
fold_point_cancel_fold_color_highlight = (1, 0.2, 0.2)

fold_point_gizmo_alpha = 1

same_vertex_distance = 0.001


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
    bl_idname = 'OBJECT_GGT_light_test'
    bl_label = 'Test Light Widget'
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

        mpr.target_set_handler('offset', get=move_get_cb, set=move_set_cb)

        mpr.color = color
        mpr.alpha = fold_point_gizmo_alpha

        mpr.color_highlight = highlight_color
        mpr.alpha_highlight = fold_point_gizmo_alpha

        mpr.use_draw_modal = True
        if not hasattr(self, 'gizmo_list'):
            self.gizmo_list = []
        mpr.type = 'fold_point'
        mpr.data = location
        self.gizmo_list.append(mpr)
        return mpr

    def create_crease_gizmo(self, bm, start_location, end_location):
        # TODO Insert reuse functionality

        mpr = self.gizmos.new(gizmos.CreaseLineGizmo.bl_idname)
        local_start_location = start_location
        local_end_location = end_location

        def move_get_cb_start():
            return local_start_location

        def move_set_cb_start(value):
            pass

        def move_get_cb_end():
            return local_end_location

        def move_set_cb_end(value):
            pass

        mpr.target_set_handler('start_pos', get=move_get_cb_start, set=move_set_cb_start)
        mpr.target_set_handler('end_pos', get=move_get_cb_end, set=move_set_cb_end)

        mpr.color = fold_point_gizmo_color
        mpr.alpha = fold_point_gizmo_alpha

        mpr.color_highlight = fold_point_gizmo_color_highlight
        mpr.alpha_highlight = fold_point_gizmo_alpha
        
        # mpr.use_select_background = True
        # mpr.use_draw_scale = True
        # use_draw_offset_scale = True
        # mpr.use_select_background = True
        # mpr.use_draw_modal = True
        mpr.use_event_handle_all = False
        if not hasattr(self, 'gizmo_list'):
            self.gizmo_list = []
        mpr.type = 'crease'
        mpr.data = [start_location, end_location]
        self.gizmo_list.append(mpr)
        return mpr
        # start_vertex = None
        # for vert in bm.verts:
        #     if start_location == vert.co:
        #         start_vertex = vert
        #         break
        # if start_vertex == None:
        #     raise 'terrible error message'
        # mpr = self.gizmos.new(CreaseLineGizmo.bl_idname)

    def setup(self, context):
        self.ui_state = 'NONE'

    def refresh(self, context):
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v for v in bm.verts if v.select]
        if len(selected) == 1:
            self.single_vertex_selected(ob, selected[0])
        elif self.ui_state == 'SHOW_FOLD_POINTS':
            self.ui_state = 'NONE'
            self.hide_all_gizmos()
        self.update_gizmos(context)

    def update_gizmos(self, context):

        target = context.active_object

        mat_target = target.matrix_world.normalized()
        print('refresh...')
        for mpr in self.gizmo_list:
            mpr.update(mat_target)

    def hide_all_gizmos(self):
        for gizmo in self.gizmo_list:
            gizmo.hide = True

    def single_vertex_selected(self, ob, selected):
        if hasattr(self, 'lock_state') and self.lock_state > 0:
            print('lock_state', self.lock_state)
            self.lock_state -= 1
            return
        print('single_vertex_selected')
        self.ui_state = 'SHOW_FOLD_POINTS'
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
            # print('creating fold point', fold_point['data']['location'])
            mpr.type = fold_point['type']
            mpr.data = fold_point['data']

    def gizmo_clicked(self, context, gizmo):
        print('gizmo_clicked, ', self.ui_state)
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v.select for v in bm.verts]
        if self.ui_state == 'SHOW_FOLD_POINTS':
            for other_gizmo in self.gizmo_list:
                if not other_gizmo == gizmo:
                    other_gizmo.hide = True
                else:
                    other_gizmo.color = fold_point_create_fold_color
                    other_gizmo.color_highlight = fold_point_create_fold_color_highlight
                    # print('going green at', other_gizmo.target_get_value('offset'))

            cancel_gizmo = self.create_or_reuse_fold_point_gizmo(
                                                                 np.array(ob.data.vertices)[selected][0].co,
                                                                 fold_point_cancel_fold_color,
                                                                 fold_point_cancel_fold_color_highlight)
            # print('cancel at', np.array(ob.data.vertices)[selected][0].co)
            cancel_gizmo.type = 'cancel'
            cancel_gizmo.data = {'vertex': np.array(ob.data.vertices)[selected][0]}
            # print('assigning', cancel_gizmo.data)
            # self.target_get_value('offset')
            crease_data = self.get_crease(context, gizmo.type, gizmo.data)
            # print(crease)
            # print('creating potential crease from:', crease[0], 'to', crease[1])
            crease_points = crease_data['crease_points']
            crease_gizmo = self.create_crease_gizmo(bm, crease_points[0], crease_points[1])
            crease_gizmo.data = crease_data
            self.ui_state = 'SHOW_POTENTIAL_CREASE'
            self.update_gizmos(context)
            # self.lock_state = 1
        elif self.ui_state == 'SHOW_POTENTIAL_CREASE':
            print('clicked in show_potential_crease state')
            if gizmo.type == 'cancel':
                self.single_vertex_selected(ob, gizmo.data['vertex'])
                self.update_gizmos(context)
                print('canceled potential crease state')
            elif gizmo.type == 'crease':
                # TODO: do fold based on the crease created
                print('gizmo data', gizmo.data)
                print('gizmo type', gizmo.type)
                self.create_crease(context, gizmo.data)
                self.ui_state = 'NONE'
                self.hide_all_gizmos()
                # print('do fold from', mathutils.Vector(gizmo.data), \
                # 'to', mathutils.Vector(gizmo.target_get_value('offset')))

    def get_crease(self, context, start_point_type, data):
        # print('\n\n\nDoing get crease:')
        fold_from_vertex_location = data['fold_from_vertex']
        fold_to_vertex_location = data['location']
        # print('from:', fold_from_vertex_location)
        # print('to:', fold_to_vertex_location)
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        original_verts = []
        for vert in bm.verts:
            original_verts.append(vert)
        # print('original len', len(original_verts))
        max_coords = [float('-inf'), float('-inf'), float('-inf')]
        min_coords = [float('inf'), float('inf'), float('inf')]
        min_max_coords = [min_coords, max_coords]
        for vert in bm.verts:
            for i in range(3):
                # print('vert', vert.co)
                # print('max_coords', max_coords)
                # print('min_coords', min_coords)
                if vert.co[i] > max_coords[i]:
                    max_coords[i] = vert.co[i]
                if vert.co[i] < min_coords[i]:
                    min_coords[i] = vert.co[i]
        midpoint = fold_from_vertex_location.lerp(fold_to_vertex_location, 0.5)
        n = (midpoint - fold_from_vertex_location).normalized()
        line_order1 = [0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0]
        line_order2 = [1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0]
        intersection_points = []
        # print('\n\n')
        for i in range(12):
            x1 = min_max_coords[line_order1[i]][0]
            x2 = min_max_coords[line_order2[i]][0]

            y1 = min_max_coords[line_order1[(i + 8) % 12]][1]
            y2 = min_max_coords[line_order2[(i + 8) % 12]][1]

            z1 = min_max_coords[line_order1[(i + 4) % 12]][2]
            z2 = min_max_coords[line_order2[(i + 4) % 12]][2]

            line_point1 = mathutils.Vector((x1, y1, z1))
            line_point2 = mathutils.Vector((x2, y2, z2))
            l_vec = line_point1 - line_point2
            denominator = l_vec.dot(n)
            if denominator == 0:
                pass  # no intersection
            else:
                numerator = (midpoint - line_point1).dot(n)
                if numerator == 0:
                    numerator = (midpoint - line_point2).dot(n)
                    if numerator == 0:
                        print('line from point (', x1, ',', y1, ',', z1, ') to (', x2, ',', y2, ',', z2, ')')
                        print('plane ', midpoint, n)
                        print('bad problems intersection of plane and box resulted in edge inside plane')
                        continue
                    else:
                        d = numerator / denominator
                        # print('d', d)
                        # print('line from point (', x1, ',', y1, ',', z1, ') to (', x2, ',', y2, ',', z2, ')')
                        # print('plane ', midpoint, n)
                        # print('intersection at', (line_point1 + l_vec * d))
                        if d > 0 and d <= 1 + same_vertex_distance:
                            intersection_points.append((line_point2 + l_vec * d))
                            # print('adding intersection between line and plane')
                else:
                    d = numerator / denominator
                    # print('d', d)
                    # print('line from point (', x1, ',', y1, ',', z1, ') to (', x2, ',', y2, ',', z2, ')')
                    # print('plane ', midpoint, n)
                    # print('intersection at', (line_point1 + l_vec * d))
                    if d < 0 and d >= -1 - same_vertex_distance:
                        intersection_points.append((line_point1 + l_vec * d))
                        # print('adding intersection between line and plane')
            # print('\n\n')

        # remove duplicate intersection points
        to_remove = []
        for i1 in range(len(intersection_points) - 1):
            for i2 in range(i1 + 1, len(intersection_points)):
                if (intersection_points[i1] - intersection_points[i2]).length < same_vertex_distance \
                        and i2 not in to_remove:
                    to_remove.append(i2)
        for i in sorted(to_remove, reverse=True):
            # print(i)
            del intersection_points[i]
        return {
            'crease_points': intersection_points,
            'folding_points': [fold_from_vertex_location, fold_to_vertex_location]
        }

    def create_crease(self, context, crease_data):
        intersection_points = crease_data['crease_points']
        fold_from_vertex_location = crease_data['folding_points'][0]
        print('INTERSECTION POINTS ----', intersection_points)
        obj = context.object
        if bpy.context.mode == 'EDIT_MESH':
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_object(obj, context)

        new_verts = []
        if len(intersection_points) == 2:
            v1 = fold_from_vertex_location - intersection_points[0]
            v2 = intersection_points[0] - intersection_points[1]
            plane_normal = v1.cross(v2).normalized()
            new_intersection_points = []
            # for intersection_point in intersection_points:
            new_intersection_points.append(intersection_points[0] + plane_normal*0.01)
            new_intersection_points.append(intersection_points[1] + plane_normal*0.01)
            new_intersection_points.append(intersection_points[1] - plane_normal*0.01)
            new_intersection_points.append(intersection_points[0] - plane_normal*0.01)
            intersection_points = new_intersection_points

        for i in range(len(intersection_points)):
            new_verts.append(bm.verts.new(intersection_points[i]))
            if i > 0:
                bm.edges.new([new_verts[i], new_verts[i - 1]])

        bm.edges.new([new_verts[0], new_verts[-1]])

        bm.verts.ensure_lookup_table()
        f1 = bm.faces.new(new_verts)
        print(bm.verts)

        if bpy.context.mode == 'EDIT_MESH':
            bmesh.update_edit_mesh(obj.data)
        else:
            bm.to_mesh(obj.data)

        obj.data.update()

        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.intersect(mode='SELECT', separate_mode='NONE')
        bm.verts.ensure_lookup_table()

        print('verts', bm.verts)
        counter = 0
        to_delete = []
        for vert in bm.verts:
            print(counter, vert.co)
            for intersection_point in intersection_points:
                if (vert.co - intersection_point).length < same_vertex_distance and vert not in to_delete:
                    # TODO don't delete vertices that were there beforehand
                    print('to_delet.append', vert.co)
                    to_delete.append(vert)
            counter += 1
        bmesh.ops.delete(bm, geom=to_delete)
        print('planning to delete', to_delete)
        # bpy.ops.mesh.select_all(action='SELECT')
        # bpy.ops.mesh.remove_doubles()
        bm.verts.ensure_lookup_table()

        bpy.ops.object.mode_set(mode='OBJECT')
        obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
