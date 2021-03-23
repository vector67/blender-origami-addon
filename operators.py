import bmesh
import bpy
from bpy.types import (
   Operator)
from bpy_extras import object_utils
from bpy.props import (
   StringProperty)


def new_origami_page(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'

    layout.separator()
    layout.operator("mesh.origami_model",
                    text="Origami", icon="MESH_PLANE")  # TODO fix icon to something that makes more sense with origami


class AddOrigamiModel(Operator, object_utils.AddObjectHelper):
    """Object Cursor Array"""
    bl_idname = "mesh.origami_model"
    bl_description = "Construct an origami model"
    bl_label = "Add Origami Model"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    paper_size: StringProperty(name="Paper size",
                               default="a4",
                               description="Paper size name")

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, 'paper_size')

    def execute(self, context):
        if bpy.context.mode == "OBJECT":
            # TODO this function needs to actually react to the settings and create a physically accurate model
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

            bm.to_mesh(mesh)
            mesh.update()
            res = object_utils.object_data_add(context, mesh, operator=self)
            res['origami_model'] = True
        return {'FINISHED'}
