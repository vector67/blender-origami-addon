bl_info = {
    "name": "Origami folding tools",
    "author": "Jeffrey Russell",
    "version": (0, 0, 1),
    "blender": (2, 83, 0),
    "location": "View3D > Add",
    "description": "Test test thing",
    "category": "Object",
}

if "bpy" in locals():
    import importlib
    importlib.reload(operators)
    importlib.reload(gizmos)
    importlib.reload(gizmo_group)
else:
    from . import operators
    from . import gizmos
    from . import gizmo_group

import bpy


classes = [
    operators.AddOrigamiModel,
    gizmos.OrigamiFoldPointGizmo,
    gizmos.CreaseLineGizmo,
    gizmo_group.FoldOrigamiModelGizmoGroup
]
def register():
    print('loading origami plugin')
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.VIEW3D_MT_add.append(operators.new_origami_page)
    print('successfully loaded origami plugin')
 
def unregister():
    print('unloading origami plugin')

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    # bpy.utils.unregister_class(ObjectCursorArray)

# import bpy


# class ObjectCursorArray(bpy.types.Operator):
#     """Object Cursor Array"""
#     bl_idname = "object.cursor_array"
#     bl_label = "Cursor Array"
#     bl_options = {'REGISTER', 'UNDO'}

#     def execute(self, context):
#         scene = context.scene
#         cursor = scene.cursor.location
#         obj = context.active_object

#         total = 10

#         for i in range(total):
#             obj_new = obj.copy()
#             scene.collection.objects.link(obj_new)

#             factor = i / total
#             obj_new.location = (obj.location * factor) + (cursor * (1.0 - factor))

#         return {'FINISHED'}

# def menu_func(self, context):
#     self.layout.operator(ObjectCursorArray.bl_idname)

# def register():
#     print('hello loading')
#     bpy.utils.register_class(ObjectCursorArray)
#     bpy.types.VIEW3D_MT_object.append(menu_func)


# def unregister():
#     print("good bye")
#     bpy.utils.unregister_class(ObjectCursorArray)


# def register():
#     print("Hello World")
# def unregister():
#     print("Goodbye World")