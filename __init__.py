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
