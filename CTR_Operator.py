import os
import struct
import addon_utils
import bpy
from . import b3dimporter
from . import o3dimporter
from . import m3dimporter
fp = ''

class TexDialog_m3d(bpy.types.Operator):
    bl_idname = "ctr.txdialog_m3d"
    bl_label = "텍스쳐 경로"
    text: bpy.props.StringProperty(name='경로', default="")

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        row = self.layout
        row.prop(self, "text", text="경로")

    def execute(self, context):
        self.text += "\\res\\Circuit"
        m3dimporter.read_m3d(fp, self.text)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class TexDialog_b3d(bpy.types.Operator):
    bl_idname = "ctr.txdialog_b3d"
    bl_label = "텍스쳐 경로"
    text: bpy.props.StringProperty(name='경로', default="")

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        row = self.layout
        row.prop(self, "text", text="경로")

    def execute(self, context):
        self.text += "\\res\\PartTex"
        b3dimporter.read_b3d(fp, self.text)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class TexDialog_o3d(bpy.types.Operator):
    bl_idname = "ctr.txdialog_o3d"
    bl_label = "텍스쳐 경로"
    text: bpy.props.StringProperty(name='경로', default="")

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        row = self.layout
        row.prop(self, "text", text="경로")

    def execute(self, context):
        self.text += "\\res\\PartTex"
        o3dimporter.read_o3d(fp, self.text)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

def read_b3d(self, context, filepath):
    global fp
    fp = filepath
    filearr = []
    fip = ''
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == "CTR Importer":
            fip = mod.__file__
            fip = fip.replace('__init__.py', '')
        else:
            pass
    try: 
        os.makedirs(fip + "\\textures")
    except:
        pass
    bpy.ops.ctr.txdialog_b3d('INVOKE_DEFAULT')

    return {'FINISHED'}

def read_o3d(self, context, filepath):
    global fp
    fp = filepath
    fip = ''
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == "CTR Importer":
            fip = mod.__file__
            fip = fip.replace('__init__.py', '')
        else:
            pass
    try: 
        os.makedirs(fip + "\\textures")
    except:
        pass
    
    bpy.ops.ctr.txdialog_o3d('INVOKE_DEFAULT')

    return {'FINISHED'}

def read_m3d(self, context, filepath):
    global fp
    fp = filepath
    fip = ''
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == "CTR Importer":
            fip = mod.__file__
            fip = fip.replace('__init__.py', '')
        else:
            pass
    try: 
        os.makedirs(fip + "\\textures")
    except:
        pass

    bpy.ops.ctr.txdialog_m3d('INVOKE_DEFAULT')

    return {'FINISHED'}

def export_ctrm(self, context, filepath):
    ff = open(filepath, 'wb')
    obj = bpy.context.selected_objects[0]
    vertices = obj.data.vertices
    uv_layers = obj.data.uv_layers
    uvs = {}
    for face in obj.data.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            uv_coords = obj.data.uv_layers.active.data[loop_idx].uv
            uvs[vert_idx] = uv_coords

    final = b''
    final += len(obj.data.vertices).to_bytes(4, 'little')
    final += (len(obj.data.polygons)*3).to_bytes(4, 'little')
    final += b'\x01\x00\x00\x00'
    final += b'\x00\x00\x00\x00'
    for i in range(0, len(vertices), 1):
        uv = []
        try:
            uv = uvs[i]
        except:
            uv = [0.1,0.1]
        final += struct.pack('f', vertices[i].co[0])
        final += struct.pack('f', vertices[i].co[1])
        final += struct.pack('f', vertices[i].co[2])
        final += struct.pack('f', uv[0])
        final += struct.pack('f', uv[1])
        final += struct.pack('f', vertices[i].normal[0])
        final += struct.pack('f', vertices[i].normal[1])
        final += struct.pack('f', vertices[i].normal[2])
    final += b'\x04\x00\x00\x00'
    final += (len(obj.data.polygons)*3).to_bytes(4, 'little')
    for face in obj.data.polygons:
        for vert_ixd in face.vertices:
            final += vert_ixd.to_bytes(4, 'little')

    ff.write(final)
    ff.close()

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator


class ImportB3D(Operator, ImportHelper):
    """CTR Vehicle Import"""
    bl_idname = "import_b3d.import"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import B3D"

    # ImportHelper mixin class uses this
    filename_ext = ".b3d"

    filter_glob: StringProperty(
        default="*.b3d",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return read_b3d(self, context, self.filepath)

class ImportO3D(Operator, ImportHelper):
    """CTR Model Import"""
    bl_idname = "import_o3d.import"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import O3D"

    # ImportHelper mixin class uses this
    filename_ext = ".o3d"

    filter_glob: StringProperty(
        default="*.o3d",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return read_o3d(self, context, self.filepath)

class ImportM3D(Operator, ImportHelper):
    """CTR Map Import"""
    bl_idname = "import_m3d.import"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import M3D"

    # ImportHelper mixin class uses this
    filename_ext = ".m3d"

    filter_glob: StringProperty(
        default="*.m3d",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return read_m3d(self, context, self.filepath)

class ExportCTRM(Operator, ImportHelper):
    """CTR Model Export"""
    bl_idname = "export_ctrm.import"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export CTRM"

    # ImportHelper mixin class uses this
    filename_ext = ".ctrm"

    filter_glob: StringProperty(
        default="*.ctrm",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return export_ctrm(self, context, self.filepath)