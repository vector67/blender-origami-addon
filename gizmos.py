import math

from bpy.types import (
   Gizmo,
)

from bpy.props import (
   FloatVectorProperty,
)
import mathutils


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

fold_point_icon_verts = []

for i in range(num_circle_divisions):
    start_angle = (2*i) / num_circle_divisions * math.pi
    end_angle = (2*i + 1) / num_circle_divisions * math.pi
    for j in range(num_segment_divisions):
        fraction_start = (j/num_segment_divisions)
        fraction_end = ((j+1)/num_segment_divisions)
        angle_start = ((1-fraction_start) * start_angle + fraction_start * end_angle)
        angle_end = ((1-fraction_end) * start_angle + fraction_end * end_angle)
        for k in range(num_torus_divisions):

            fold_point_icon_verts.append(get_xyz(0, k, angle_start, angle_end, major_radius, minor_radius))
            fold_point_icon_verts.append(get_xyz(1, k, angle_start, angle_end, major_radius, minor_radius))
            fold_point_icon_verts.append(get_xyz(2, k, angle_start, angle_end, major_radius, minor_radius))

            fold_point_icon_verts.append(get_xyz(0, k, angle_end, angle_start, major_radius, minor_radius))
            fold_point_icon_verts.append(get_xyz(-1, k, angle_end, angle_start, major_radius, minor_radius))
            fold_point_icon_verts.append(get_xyz(-2, k, angle_end, angle_start, major_radius, minor_radius))

crease_marker_width = 0.02
crease_marker_length = 1
crease_marker_divisions = 10
crease_shape_verts = []

add_marker = True
for i in range(crease_marker_divisions*2-1):

    x = crease_marker_width / 2
    z1 = (i*crease_marker_length) / (crease_marker_divisions*2-1)
    z2 = ((i+1)*crease_marker_length) / (crease_marker_divisions*2-1)
    if add_marker:
        crease_shape_verts.extend([
            (-x, 0, z1), (-x, 0, z2), (x, 0, z2),
            (x, 0, z2), (x, 0, z1), (-x, 0, z1)
        ])
    add_marker = not add_marker

class OrigamiFoldPointGizmo(Gizmo):
    bl_idname = 'VIEW3D_GT_fold_origami_model'
    bl_target_properties = (
        {'id': 'offset', 'type': 'FLOAT', 'array_length': 3},
    )

    plane_co: FloatVectorProperty(
        size=3,
        default=(0, 0, 0),
    )

    __slots__ = (
        'custom_shape',
        'type',
        'data'
    )

    def get_matrix_transform(self):
        return mathutils.Matrix.Translation(self.target_get_value('offset')) @ self.matrix_world

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape, matrix=self.get_matrix_transform())

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape, matrix=self.get_matrix_transform(), select_id=select_id)

    def select_refresh(self):
        pass

    def setup(self):
        if not hasattr(self, 'custom_shape'):
            self.custom_shape = self.new_custom_shape('TRIS', fold_point_icon_verts)

    def invoke(self, context, event):
        print('clicked')
        self.group.gizmo_clicked(context, self)
        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        context.area.header_text_set(None)
        print('exited')
        if cancel:
            self.target_set_value('offset', self.init_value)

    def modal(self, context, event, tweak):
        return {'RUNNING_MODAL'}

    def update(self, mat_target):
        self.matrix_basis = mat_target
        # pass


class CreaseLineGizmo(Gizmo):
    bl_idname = 'VIEW3D_GT_crease_line_gizmo'
    bl_target_properties = (
        {'id': 'start_pos', 'type': 'FLOAT', 'array_length': 3},
        {'id': 'end_pos', 'type': 'FLOAT', 'array_length': 3},    
    )

    __slots__ = (
        'custom_shape',
        'type',
        'data'
    )

    def get_matrix_transform(self):
        eye = self.target_get_value('start_pos')
        target = self.target_get_value('end_pos')
        difference_vector = mathutils.Vector(eye) - mathutils.Vector(target)
        z = difference_vector
        up = mathutils.Vector((0,0,1))
        # te = this.elements; //this.elements is a 4 x 4 matrix stored in a list.


        if z.length == 0:
            z.z = 1;

        x = up.cross(z).normalized();

        if x.length == 0:
            z.z += 0.0001;
            x = up.cross(z).normalized();
        y = z.cross(x)

        te = [[0 for x in range(4)] for y in range(4)]
        te[0][0] = -x.x; te[0][1] = -y.x; te[0][2] = -z.x; 
        te[1][0] = -x.y; te[1][1] = -y.y; te[1][2] = -z.y;
        te[2][0] = -x.z; te[2][1] = -y.z; te[2][2] = -z.z;
        te[3][3] = 1
        return mathutils.Matrix.Translation(mathutils.Vector(eye)) @ \
            mathutils.Matrix.Translation(self.matrix_world.to_translation()) @ mathutils.Matrix(te)
            

    def draw(self, context):
        self.draw_custom_shape(self.custom_shape, matrix=self.get_matrix_transform())

    def draw_select(self, context, select_id):
        self.draw_custom_shape(self.custom_shape, select_id=select_id, matrix=self.get_matrix_transform())

    def select_refresh(self):
        print('hey called')

    def setup(self):
        if not hasattr(self, 'custom_shape'):
            self.custom_shape = self.new_custom_shape('TRIS', crease_shape_verts)

    def invoke(self, context, event):
        print('clicked')
        self.group.gizmo_clicked(context, self)
        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        context.area.header_text_set(None)
        if cancel:
            self.target_set_value('start_pos', self.init_value)

    def modal(self, context, event, tweak):
        # delta = (event.mouse_y - self.init_mouse_y) / 10.0
        # if 'SNAP' in tweak:
        #     delta = round(delta)
        # if 'PRECISE' in tweak:
        #     delta /= 10.0
        # value = self.init_value - delta
        # self.target_set_value('offset', value)
        # context.area.header_text_set('My Gizmo: %.4f' % value)
        return {'RUNNING_MODAL'}

    def update(self, mat_target):
        self.matrix_offset = mat_target