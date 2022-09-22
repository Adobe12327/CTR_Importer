import bpy
from . import CTR_Operator

bl_info = {
    "name": "CTR Importer",
    "author": "Adobe",
    "description": "시티레이서 임포터!",
    "blender": (2, 93, 0),
    "version": (1, 0, 0),
    "location": "",
    "warning": "",
    "category": "Import-Export"
}

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(CTR_Operator.ImportB3D.bl_idname, text="CTR 차량 (.b3d)")
    self.layout.operator(CTR_Operator.ImportO3D.bl_idname, text="CTR 오브젝트 (.o3d)")
    self.layout.operator(CTR_Operator.ImportM3D.bl_idname, text="CTR 맵 (.m3d)")

def menu_func_export(self, context):
    self.layout.operator(CTR_Operator.ExportB3D.bl_idname, text="CTR 차량 (.b3d)")
    self.layout.operator(CTR_Operator.ExportO3D.bl_idname, text="CTR 오브젝트 (.o3d)")

def register():
    bpy.types.Scene.ctr_texture_dir = bpy.props.StringProperty(name="텍스쳐 경로")
    bpy.utils.register_class(CTR_Operator.ImportB3D)
    bpy.utils.register_class(CTR_Operator.ImportO3D)
    bpy.utils.register_class(CTR_Operator.ImportM3D)
    bpy.utils.register_class(CTR_Operator.ExportB3D)
    bpy.utils.register_class(CTR_Operator.ExportO3D)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(CTR_Operator.ImportB3D)
    bpy.utils.unregister_class(CTR_Operator.ImportO3D)
    bpy.utils.unregister_class(CTR_Operator.ImportM3D)
    bpy.utils.unregister_class(CTR_Operator.ExportB3D)
    bpy.utils.unregister_class(CTR_Operator.ExportO3D)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    del bpy.types.Scene.ctr_texture_dir
