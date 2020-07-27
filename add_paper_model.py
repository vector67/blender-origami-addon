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
num_torus_divisions = 15

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
            

class FoldOrigamiModel(Gizmo):
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
        "init_mouse_y",
        "init_value",
        "rotation"
    )

    def _update_offset_matrix(self):
        pass
        # offset behind the light
        # self.matrix_offset.col[3][2] = self.target_get_value("offset") / -10.0

    def get_matrix_transform(self):
        # self.rotation += 1
        # self.rotation = self.rotation % 360
        return mathutils.Matrix.Translation(self.target_get_value('offset')) @ self.matrix_world @ mathutils.Matrix.Rotation(math.radians(self.rotation), 4, 'Z')

    def draw(self, context):
        self._update_offset_matrix()
        self.draw_custom_shape(self.custom_shape, matrix = self.get_matrix_transform())

    def draw_select(self, context, select_id):
        self._update_offset_matrix()
        # print(self.bl_target_properties)
        self.draw_custom_shape(self.custom_shape, matrix = self.get_matrix_transform(), select_id=select_id)

    def select_refresh(self):
        print('hey called')

    def setup(self):
        if not hasattr(self, "rotation"):
            self.rotation = 0
        if not hasattr(self, "custom_shape"):
            self.custom_shape = self.new_custom_shape('TRIS', custom_shape_verts)

    def invoke(self, context, event):
        self.init_mouse_y = event.mouse_y
        self.init_value = self.target_get_value("offset")
        print('clicked')
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
        if isinstance(op, FoldOrigamiModel):
            return op
        return None

    @classmethod
    def poll(cls, context):
        if context.mode == 'EDIT_MESH':
            ob = context.object
            return 'VERT' in bmesh.from_edit_mesh(ob.data).select_mode \
                and (ob and 'origami_model' in ob and ob['origami_model'])
        return False

    def create_gizmo(self, location):
        mpr = self.gizmos.new(FoldOrigamiModel.bl_idname)
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
        self.gizmo_list.append(mpr)
        return mpr

    def setup(self, context):
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v.select for v in bm.verts]
        if np.sum(selected) == 1:
            location = np.array(ob.data.vertices)[selected][0].co
            print('creating gizmo at ', location)
            self.create_gizmo(location)

    def calculate_fold_points(self, ob, selected):
        fold_points = []
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v for v in bm.verts if v.select][0]

        neighbouring_vertex_edge = []
        for edge in bm.edges:
            other = edge.other_vert(selected)
            if not other == None:
                fold_points.append(other.co)
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
                fold_points.append(new_point)
        # print('edge_to_neighbour_edge', edge_to_neighbour_edge)

        return fold_points
    def refresh(self, context):
        ob = context.object
        bm = bmesh.from_edit_mesh(ob.data)
        selected = [v.select for v in bm.verts]
        if np.sum(selected) == 1:
            fold_points = self.calculate_fold_points(ob, selected)
        
            location = np.array(ob.data.vertices)[selected][0].co
            print('creating gizmo at ', location)
            if hasattr(self, 'gizmo_list'):
                if len(self.gizmo_list) > 0:
                    for gizmo in self.gizmo_list:
                        gizmo.hide = True
            for fold_point in fold_points:
                #TODO: don't just keep creating new gizmos, find a way to re-use old gizmos.
                self.create_gizmo(fold_point)


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
