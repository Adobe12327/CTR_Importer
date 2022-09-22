import os
import struct
import bpy
import addon_utils
import os
import math
from .utils import _S_Material, C_Mesh, DecodeSS, write_obj, Decode

def read_float32(f):
    return struct.unpack('f', f.read(4))[0]

def read_int32(f):
    return int.from_bytes(f.read(4), 'little')

def __ROR__(num, count, bits=8):
    return ((num >> count) | (num << (bits - count))) & ((0b1<<bits) - 1)

def ConvertToTxt_Old(data, size):
    for i in range(size):
        data[i] = __ROR__(data[i], 1) ^ 0x9E
    return data

def read_o3d(filepath, txd, path_add, context):
    f = open(filepath, 'rb')
    Meshes = []
    meshNum = read_int32(f)
    materialNum = read_int32(f)
    if not meshNum <= 0:
        for i in range(meshNum):
            newmesh = C_Mesh()
            C_Mesh.Load(newmesh, f)
            Meshes.append(newmesh)
    Material = []
    if materialNum > 0:
        for i in range(materialNum):
            mat = _S_Material()
            mat.NameLen = read_int32(f)
            mat.TextureName =  f.read(mat.NameLen).decode('ISO-8859-1')
            Material.append(mat)

    encodeNum = int.from_bytes(ConvertToTxt_Old(bytearray(f.read(4)), 4), 'little')
    if not encodeNum >= 0 and encodeNum <= 100:
        context.report({'ERROR'}, "파일이 손상되었습니다")
        return
    nameSize = int.from_bytes(Decode(encodeNum, ConvertToTxt_Old(bytearray(f.read(4)), 4), 4), 'little')
    if nameSize < 1 or nameSize > 40:
        context.report({'ERROR'}, "파일이 손상되었습니다")
        return
    saveName = Decode(encodeNum, ConvertToTxt_Old(bytearray(f.read(nameSize)), nameSize), nameSize).decode('ISO-8859-1')

    if not txd == '':
        txd += path_add
        fp = ''
        for mod in addon_utils.modules():
            if mod.bl_info['name'] == "CTR Importer":
                fp = mod.__file__
                fp = fp.replace('__init__.py', '')
            else:
                pass

        try: 
            os.makedirs(fp + "\\textures")
        except:
            pass

        for texture in Material:
            mat = bpy.data.materials.new(texture.TextureName)

        DecodeSS(Material, txd, fp)

    root = bpy.data.objects.new("empty", None)
    root.name = os.path.basename(filepath)
    root.rotation_euler.x = math.radians(90.0)
    bpy.context.collection.objects.link(root)
    bpy.context.view_layer.objects.active = root

    for obj in Meshes:
        parent = write_obj(obj, True, root)
        for objj in obj.m_SubMesh:
            objj.m_MaterialID = Material[objj.m_MaterialID]
            write_obj(objj, True, parent)
