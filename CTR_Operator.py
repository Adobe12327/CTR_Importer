import os
import struct
import addon_utils
import bpy
from . import b3dimporter
from . import o3dimporter
from . import m3dimporter

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
    bl_options = {'REGISTER', 'UNDO'}

    # ImportHelper mixin class uses this
    filename_ext = ".b3d"

    filter_glob: StringProperty(
        default="*.b3d",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "ctr_texture_dir")

    def execute(self, context):
        path_add =  "\\res\\PartTex"
        b3dimporter.read_b3d(self.properties.filepath, context.scene.ctr_texture_dir, path_add)
        return {'FINISHED'}

class ImportO3D(Operator, ImportHelper):
    """CTR Model Import"""
    bl_idname = "import_o3d.import"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import O3D"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # ImportHelper mixin class uses this
    filename_ext = ".o3d"

    filter_glob: StringProperty(
        default="*.o3d",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "ctr_texture_dir")

    def execute(self, context):
        path_add =  "\\res\\PartTex"
        o3dimporter.read_o3d(self.properties.filepath, context.scene.ctr_texture_dir, path_add)
        return {'FINISHED'}

class ImportM3D(Operator, ImportHelper):
    """CTR Map Import"""
    bl_idname = "import_m3d.import"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import M3D"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # ImportHelper mixin class uses this
    filename_ext = ".m3d"

    filter_glob: StringProperty(
        default="*.m3d",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "ctr_texture_dir")

    def execute(self, context):
        path_add =  "\\res\\Circuit"
        m3dimporter.read_m3d(self.properties.filepath, context.scene.ctr_texture_dir, path_add)
        return {'FINISHED'}

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
