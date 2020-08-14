import bpy
import bmesh
from bpy_extras import object_utils
from bpy.props import (
   StringProperty,
   FloatVectorProperty,
)
from bpy.types import (
   Operator,
   Gizmo,
   GizmoGroup,
)
from pprint import pprint
import math
import mathutils
import numpy as np

def get_x(angle, radius):
    return math.sin(angle) * radius
def get_y(angle, radius):
    return math.cos(angle) * radius
def get_xyz_from_theta_rho_radii(theta, rho, small_radius, big_radius):
    y1 = math.cos(rho) * small_radius
    z = math.sin(rho) * small_radius

    new_radius = math.sqrt((big_radius - y1)**2 + z**2)

    x = math.sin(theta) * new_radius
    y = math.cos(theta) * new_radius

    return (x, y, z)
def get_xyz(vertex_ind, k, angle_start, angle_end, major_radius, minor_radius):
    torus_start_slice_center = (get_x(angle_start, major_radius), get_y(angle_start, major_radius), 0)
    if vertex_ind == 0:
        rho = 2*k / num_torus_divisions * math.pi
        return get_xyz_from_theta_rho_radii(angle_start, rho, minor_radius, major_radius)
    
    if vertex_ind > 0:
        rho = 2*(k + 1) / num_torus_divisions * math.pi
    else:
        rho = 2*(k - 1) / num_torus_divisions * math.pi

    if vertex_ind == 1 or vertex_ind == -1:
        return get_xyz_from_theta_rho_radii(angle_start, rho, minor_radius, major_radius)
    
    return get_xyz_from_theta_rho_radii(angle_end, rho, minor_radius, major_radius)

num_circle_divisions = 8
num_segment_divisions = 2
num_torus_divisions = 5

major_radius = 0.3
minor_radius = 0.03
# major_radius = 3
# minor_radius = 0.3

custom_shape_verts = []

for i in range(num_circle_divisions):
    start_angle = (2*i) / num_circle_divisions * math.pi
    end_angle = (2*i + 1) / num_circle_divisions * math.pi
    for j in range(num_segment_divisions):
        fraction_start = (j/num_segment_divisions)
        fraction_end = ((j+1)/num_segment_divisions)
        angle_start = ((1-fraction_start) * start_angle + fraction_start * end_angle)
        angle_end = ((1-fraction_end) * start_angle + fraction_end * end_angle)
        for k in range(num_torus_divisions):

            custom_shape_verts.append(get_xyz(0, k, angle_start, angle_end, major_radius, minor_radius))
            custom_shape_verts.append(get_xyz(1, k, angle_start, angle_end, major_radius, minor_radius))
            custom_shape_verts.append(get_xyz(2, k, angle_start, angle_end, major_radius, minor_radius))

            custom_shape_verts.append(get_xyz(0, k, angle_end, angle_start, major_radius, minor_radius))
            custom_shape_verts.append(get_xyz(-1, k, angle_end, angle_start, major_radius, minor_radius))
            custom_shape_verts.append(get_xyz(-2, k, angle_end, angle_start, major_radius, minor_radius))

crease_shape_verts = [
    (0,0,0), (0,1,0), (0.1,1,0), 
    (0.1,1,0), (0.1,0,0), (0,0,0)
]

class OrigamiFoldPointGizmo(Gizmo):
    bl_idname = "VIEW3D_GT_fold_origami_model"
    bl_target_properties = (
        {"id": "offset", "type": 'FLOAT', "array_length": 3},
    )


    plane_co: FloatVectorProperty(
        size=3,
        default=(0, 0, 0),
    )

    __slots__ = (
        "custom_shape",
        "type",
        "data"
    )

    def get_matrix_transform(self):
        return mathutils.Matrix.Translation(self.target_get_value('offset')) @ self.matrix_world

    def draw(self, context):
        # self.draw_select(self, context, None)
        self.draw_custom_shape(self.custom_shape, matrix = self.get_matrix_transform())

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape, matrix = self.get_matrix_transform(), select_id=select_id)

    def select_refresh(self):
        print('hey called')

    def setup(self):
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('TRIS', custom_shape_verts)

    def invoke(self, context, event):
        print('clicked')
        self.group.gizmo_clicked(context, self)
        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        context.area.header_text_set(None)
        print('exited')
        if cancel:
            self.target_set_value("offset", self.init_value)

    def modal(self, context, event, tweak):
        # delta = (event.mouse_y - self.init_mouse_y) / 10.0
        # if 'SNAP' in tweak:
        #     delta = round(delta)
        # if 'PRECISE' in tweak:
        #     delta /= 10.0
        # value = self.init_value - delta
        # self.target_set_value("offset", value)
        # context.area.header_text_set("My Gizmo: %.4f" % value)
        return {'RUNNING_MODAL'}

class CreaseLineGizmo(Gizmo):
    bl_idname = "VIEW3D_GT_crease_line_gizmo"
    bl_target_properties = (
        {"id": "start_pos", "type": 'FLOAT', "array_length": 3},
        {"id": "end_pos", "type": 'FLOAT', "array_length": 3},
    )

    __slots__ = (
        "custom_shape",
    )

    def get_matrix_transform(self):
        return mathutils.Matrix.Translation(self.target_get_value('start_pos')) @ self.matrix_world @ mathutils.Matrix.Rotation(math.radians(self.rotation), 4, 'Z')

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape, matrix = self.get_matrix_transform())

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape, matrix = self.get_matrix_transform(), select_id=select_id)

    def select_refresh(self):
        print('hey called')

    def setup(self):
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('TRIS', crease_shape_verts)

    def invoke(self, context, event):
        self.init_mouse_y = event.mouse_y
        self.init_value = self.target_get_value("offset")
        print('clicked')
        self.group.gizmo_clicked(context, self)
        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        context.area.header_text_set(None)
        print('exited')
        if cancel:
            self.target_set_value("offset", self.init_value)

    def modal(self, context, event, tweak):
        # delta = (event.mouse_y - self.init_mouse_y) / 10.0
        # if 'SNAP' in tweak:
        #     delta = round(delta)
        # if 'PRECISE' in tweak:
        #     delta /= 10.0
        # value = self.init_value - delta
        # self.target_set_value("offset", value)
        # context.area.header_text_set("My Gizmo: %.4f" % value)
        return {'RUNNING_MODAL'}


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
        if isinstance(op, OrigamiFoldPointGizmo):
            return op
        return None

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            ob = context.object
            return 'VERT' in bmesh.from_edit_mesh(ob.data).select_mode \
                and (ob and 'origami_model' in ob and ob['origami_model'])
        return False

    def create_fold_point_gizmo(self, location):
        mpr = self.gizmos.new(OrigamiFoldPointGizmo.bl_idname)
        local_location = location
        def move_get_cb():
            return local_location

        def move_set_cb(value):
            pass

        mpr.target_set_handler("offset", get=move_get_cb, set=move_set_cb)

        mpr.color = 0.9, 0.5, 0.5
        mpr.alpha = 1

        mpr.color_highlight = 1, 0.8, 0.8
        mpr.alpha_highlight = 1

        mpr.use_draw_modal = True
        if not hasattr(self, 'gizmo_list'):
            self.gizmo_list = []
        mpr.type = "fold_point"
        mpr.data = location
        self.gizmo_list.append(mpr)
        return mpr

    def create_crease_gizmo(self, bm, start_location, end_vertex):
        start_vertex = None
        # for vert in bm.verts:
        #     if start_location == vert.co:
        #         start_vertex = vert
        #         break
        # if start_vertex == None:
        #     raise "terrible error message"
        # mpr = self.gizmos.new(CreaseLineGizmo.bl_idname)

    def setup(self, context):
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v.select for v in bm.verts]
        if np.sum(selected) == 1:
            location = np.array(ob.data.vertices)[selected][0].co
            print('creating gizmo at ', location)
            self.create_fold_point_gizmo(location)
        self.ui_state = "NONE"

    def calculate_fold_points(self, ob, selected):
        fold_points = []
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v for v in bm.verts if v.select][0]

        neighbouring_vertex_edge = []
        for edge in bm.edges:
            other = edge.other_vert(selected)
            if not other == None:
                fold_points.append({
                    'type': 'fold_point_half_fold', 
                    'data': {
                        'location': other.co,
                        'fold_from_vertex': selected.co,
                    }
                })
                neighbouring_vertex_edge.append((edge, other))

        edge_to_neighbour_edge = {}
        #TODO: add some way of adding together continuous edges into one edge so that you can fold across vertices in the way which break up straight edges.
        for edge in bm.edges:
            for e, vert in neighbouring_vertex_edge:
                if not edge.other_vert(vert) == None and not edge == e:
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
        # print('edge_to_neighbour_edge', edge_to_neighbour_edge)

        return fold_points
    def refresh(self, context):
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v for v in bm.verts if v.select]
        if len(selected) == 1:
            self.single_vertex_selected(ob, selected[0])
        elif self.ui_state == "SHOW_FOLD_POINTS":
            self.ui_state = "NONE"
            for gizmo in self.gizmo_list:
                gizmo.hide = True

    def single_vertex_selected(self, ob, selected):
        self.ui_state = "SHOW_FOLD_POINTS"
        fold_points = self.calculate_fold_points(ob, selected)
    
        location = selected.co
        print('creating gizmo at ', location)
        if hasattr(self, 'gizmo_list'):
            if len(self.gizmo_list) > 0:
                for gizmo in self.gizmo_list:
                    gizmo.hide = True
        for fold_point in fold_points:
            #TODO: don't just keep creating new gizmos, find a way to re-use old gizmos.
            mpr = self.create_fold_point_gizmo(fold_point['data']['location'])
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

            cancel_gizmo = self.create_fold_point_gizmo(np.array(ob.data.vertices)[selected][0].co)
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
                #TODO: do fold based on the crease created
                print('gizmo data', gizmo.data)
                print('gizmo type', gizmo.type)
                # print('do fold from', mathutils.Vector(gizmo.data), 'to', mathutils.Vector(gizmo.target_get_value("offset")))
    def get_crease(self, start_point_type, data):
        fold_from_vertex_location = data['fold_from_vertex']
        fold_to_vertex_location = data['location']
        

class AddOrigamiModel(Operator, object_utils.AddObjectHelper):
    """Object Cursor Array"""
    bl_idname = "mesh.origami_model"
    bl_description = "Construct a step origami model"
    bl_label = "Add Origami Model"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    paper_size : StringProperty(name = "Paper size",
                                default = "a4",
                                description = "Paper size name")

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, 'paper_size')

    def execute(self, context):
        if bpy.context.mode == "OBJECT":

            all_verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]

            mesh = bpy.data.meshes.new("Origami")
            bm = bmesh.new()

            for v_co in all_verts:
                bm.verts.new(v_co)

            def add_faces(n, block_vert_sets):
                for bvs in block_vert_sets:
                    for i in range(self.num_sides - 1):
                        bm.faces.new([bvs[i], bvs[i + n], bvs[i + n + 1], bvs[i + 1]])
                    bm.faces.new([bvs[n - 1], bvs[(n * 2) - 1], bvs[n], bvs[0]])

            bm.faces.new(bm.verts)
            # bm.faces.new(reversed(bm.verts[-self.num_sides:]))  # otherwise normal faces intern... T44619.

            bm.to_mesh(mesh)
            mesh.update()
            res = object_utils.object_data_add(context, mesh, operator=self)
            res['origami_model'] = True
        return {'FINISHED'}
