from io import BufferedWriter
import os
import random
import struct
import addon_utils
import bpy
from . import b3dimporter
from . import o3dimporter
from . import m3dimporter
from .utils import C_SubMesh, C_Mesh, _S_Default_Car
from .EncodeTable import g_chEncodeCode1
import mathutils

def Encode(nCodeNum, bytes):
    result = b''
    for byte in bytes:
        result += g_chEncodeCode1[nCodeNum][byte].to_bytes(1, 'little')
    return result

def Encode_Old(data):
    content = bytearray(data)
    for i in range(len(content)):
        content[i] = __ROL__(content[i] ^ 0x9E, 1)
    return content

def __ROL__(num, count, bits=8): 
    return ((num << count) | (num >> (bits - count))) & ((0b1<<bits) - 1)

def read_submesh(Material, submesh):
    newsubmesh = C_SubMesh()
    newsubmesh.m_SubMeshName = submesh.name.split('.')[0]
    materialname = submesh.active_material.name
    if not materialname in Material:
        Material.append(materialname)
    newsubmesh.m_MaterialID = Material.index(materialname)
    newsubmesh.m_nVertexNum = len(submesh.data.vertices)
    newsubmesh.m_nFaceNum = len(submesh.data.polygons)*3
    for i in range(len(submesh.data.vertices)):
        newsubmesh.m_VertexList.append(submesh.data.vertices[i].co)
        newsubmesh.m_VertexNList.append(submesh.data.vertices[i].normal)
    newsubmesh.m_nVertexNum = len(newsubmesh.m_VertexList)
    uvs = {}
    polygons = []
    for face in submesh.data.polygons:
        polygons.append([face.vertices[0], face.vertices[1], face.vertices[2]])
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            uv_coords = submesh.data.uv_layers.active.data[loop_idx].uv
            uvs[vert_idx] = uv_coords
    newsubmesh.m_nStripNum = 1
    for i in range(newsubmesh.m_nVertexNum):
        newsubmesh.m_UVVertexList.append(uvs[i])
    newsubmesh.m_nFaceNum = len(polygons)*3
    newsubmesh.m_StripIndex = polygons
    return newsubmesh

def write_submesh(submesh:C_SubMesh):
    final = b''
    final += len(submesh.m_SubMeshName).to_bytes(4, "little")
    final += submesh.m_SubMeshName.encode("ANSI")
    final += submesh.m_MaterialID.to_bytes(4, "little")
    final += submesh.m_nVertexNum.to_bytes(4, "little")
    final += submesh.m_nFaceNum.to_bytes(4, "little")
    final += submesh.m_nStripNum.to_bytes(4, "little")
    final += submesh.m_nLightNum.to_bytes(4, "little")
    for i in range(submesh.m_nVertexNum):
        final += struct.pack("f", submesh.m_VertexList[i][0])
        final += struct.pack("f", submesh.m_VertexList[i][1])
        final += struct.pack("f", submesh.m_VertexList[i][2])
        final += struct.pack("f", submesh.m_UVVertexList[i][0])
        final += struct.pack("f", submesh.m_UVVertexList[i][1])
        final += struct.pack("f", submesh.m_VertexNList[i][0])
        final += struct.pack("f", submesh.m_VertexNList[i][1])
        final += struct.pack("f", submesh.m_VertexNList[i][2])
    final += (4).to_bytes(4, "little")
    final += submesh.m_nFaceNum.to_bytes(4, "little")
    for face in submesh.m_StripIndex:
        for vert_id in face:
            final += vert_id.to_bytes(4, 'little')
    return final


def write_mesh(mesh:C_Mesh):
    final = b''
    final += len(mesh.m_MeshID).to_bytes(4, "little")
    final += mesh.m_MeshID.encode("ANSI")
    final += mesh.m_SubMeshNum.to_bytes(4, "little")
    for submesh in mesh.m_SubMesh:
        final += write_submesh(submesh)
    final += struct.pack("f", mesh.m_BBox.Coord[0])
    final += struct.pack("f", mesh.m_BBox.Coord[1])
    final += struct.pack("f", mesh.m_BBox.Coord[2])
    final += struct.pack("f", mesh.m_BBox.Max[0])
    final += struct.pack("f", mesh.m_BBox.Max[1])
    final += struct.pack("f", mesh.m_BBox.Max[2])
    final += struct.pack("f", mesh.m_BBox.Min[0])
    final += struct.pack("f", mesh.m_BBox.Min[1])
    final += struct.pack("f", mesh.m_BBox.Min[2])
    return final

def export_o3d(self, context:bpy.types.Context, filepath):
    f = open(filepath, 'wb')
    final = b''
    root = bpy.context.selected_objects[0]
    Meshes = []
    Materials = []
    for meshs in root.children:
        newmesh = C_Mesh()
        newmesh.m_SubMeshNum = len(meshs.children)
        newmesh.m_MeshID = meshs.name
        for submesh in meshs.children:
            newsubmesh = read_submesh(Materials, submesh)
            newmesh.m_SubMesh.append(newsubmesh)
        minx, miny, minz = (999999.0,)*3
        maxx, maxy, maxz = (-999999.0,)*3
        location = [0.0,]*3
        for submesh in meshs.children:
            for v in submesh.bound_box:
                v_world = submesh.matrix_world @ mathutils.Vector((v[0],v[1],v[2]))

                if v_world[0] < minx:
                    minx = v_world[0]
                if v_world[0] > maxx:
                    maxx = v_world[0]

                if v_world[1] < miny:
                    miny = v_world[1]
                if v_world[1] > maxy:
                    maxy = v_world[1]

                if v_world[2] < minz:
                    minz = v_world[2]
                if v_world[2] > maxz:
                    maxz = v_world[2]
        location[0] = minx+((maxx-minx)/2)
        location[1] = miny+((maxy-miny)/2)
        location[2] = minz+((maxz-minz)/2)
        newmesh.m_BBox.Min = [minx, miny, minz]
        newmesh.m_BBox.Max = [maxx, maxy, maxz]
        newmesh.m_BBox.Coord = location
        Meshes.append(newmesh)
    final += len(Meshes).to_bytes(4, "little")
    final += len(Materials).to_bytes(4, "little")

    for i in range(len(Meshes)):
        final += write_mesh(Meshes[i])

    for material in Materials:
        final += len(material).to_bytes(4, "little")
        final += material.encode("ANSI")
    
    encodenum = random.randint(0, 99)
    final += Encode_Old(encodenum.to_bytes(4, "little"))
    final += Encode_Old(Encode(encodenum, len(root.name).to_bytes(4, "little")))
    final += Encode_Old(Encode(encodenum, root.name.encode("ANSI")))
    f.write(final)
    f.close()
    return {'FINISHED'}

def export_b3d(self, context:bpy.types.Context, filepath):
    f = open(filepath, 'wb')
    final = b''
    root = bpy.context.selected_objects[0]
    car = _S_Default_Car()
    for meshs in root.children:
        if "lod_" in meshs.name:
            car.LodLevel += 1
            newmesh = C_Mesh()
            newmesh.m_MeshID = meshs.name
            newmesh.m_SubMeshNum = len(meshs.children)
            newmesh.m_BBox.Coord = [0.0,0.0,0.0]
            newmesh.m_BBox.Min = [-999999, -999999, -999999]
            newmesh.m_BBox.Max = [999999, 999999, 999999]
            for submesh in meshs.children:
                newsubmesh = read_submesh(car.Material, submesh)
                newmesh.m_SubMesh.append(newsubmesh)
            newmesh.m_SubMeshNum = len(newmesh.m_SubMesh)
            car.LodBody.append(newmesh)
        if meshs.name.split('.')[0] == "Mesh":
            newmesh = C_Mesh()
            newmesh.m_SubMeshNum = len(meshs.children)
            for submesh in meshs.children:
                newsubmesh = read_submesh(car.Material, submesh)
                newmesh.m_SubMesh.append(newsubmesh)
            minx, miny, minz = (999999.0,)*3
            maxx, maxy, maxz = (-999999.0,)*3
            location = [0.0,]*3
            for submesh in meshs.children:
                for v in submesh.bound_box:
                    v_world = submesh.matrix_world @ mathutils.Vector((v[0],v[1],v[2]))

                    if v_world[0] < minx:
                        minx = v_world[0]
                    if v_world[0] > maxx:
                        maxx = v_world[0]

                    if v_world[1] < miny:
                        miny = v_world[1]
                    if v_world[1] > maxy:
                        maxy = v_world[1]

                    if v_world[2] < minz:
                        minz = v_world[2]
                    if v_world[2] > maxz:
                        maxz = v_world[2]
            location[0] = minx+((maxx-minx)/2)
            location[1] = miny+((maxy-miny)/2)
            location[2] = minz+((maxz-minz)/2)
            newmesh.m_BBox.Min = [minx, miny, minz]
            newmesh.m_BBox.Max = [maxx, maxy, maxz]
            newmesh.m_BBox.Coord = location
            car.Mesh.append(newmesh)

    final += len(car.Material).to_bytes(4, "little")
    final += car.LodLevel.to_bytes(4, "little")
    for material in car.Material:
        final += len(material).to_bytes(4, "little")
        final += material.encode("ANSI")
    for i in range(car.LodLevel):
        final += write_mesh(car.LodBody[i])
    for i in range(len(car.Mesh)):
        final += write_mesh(car.Mesh[i])

    encodenum = random.randint(0, 99)
    final += Encode_Old(encodenum.to_bytes(4, "little"))
    final += Encode_Old(Encode(encodenum, len(root.name).to_bytes(4, "little")))
    final += Encode_Old(Encode(encodenum, root.name.encode("ANSI")))
    f.write(final)
    f.close()
    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper, ExportHelper
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
        o3dimporter.read_o3d(self.properties.filepath, context.scene.ctr_texture_dir, path_add, context)
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
        m3dimporter.read_m3d(self.properties.filepath, context.scene.ctr_texture_dir, path_add, context)
        return {'FINISHED'}

class ExportB3D(Operator, ExportHelper):
    """CTR Vehicle Export"""
    bl_idname = "export_b3d.import"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export b3d"

    # ImportHelper mixin class uses this
    filename_ext = ".b3d"

    filter_glob: StringProperty(
        default="*.b3d",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return export_b3d(self, context, self.filepath)

class ExportO3D(Operator, ExportHelper):
    """CTR Object Export"""
    bl_idname = "export_o3d.import"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export o3d"

    # ImportHelper mixin class uses this
    filename_ext = ".o3d"

    filter_glob: StringProperty(
        default="*.o3d",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return export_o3d(self, context, self.filepath)
