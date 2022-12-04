import os
import struct
import bpy
import addon_utils
import os
import math
from .utils import _S_Material, C_Mesh, _S_Default_Car, DecodeSS, write_obj, Decode, ConvertToTxt_Old

def read_float32(f):
    return struct.unpack('f', f.read(4))[0]

def read_int32(f):
    return int.from_bytes(f.read(4), 'little')

def read_b3d(filepath, txd, path_add, context):
    txd += path_add
    f = open(filepath, 'rb')
    car = _S_Default_Car()
    MaterialNum = read_int32(f)
    car.LodLevel = read_int32(f)
    for i in range(MaterialNum):
        mat = _S_Material()
        mat.NameLen = read_int32(f)
        mat.TextureName = f.read(mat.NameLen).decode('ISO-8859-1')
        car.Material.append(mat)
    if car.LodLevel > 0:
        for i in range(car.LodLevel):
            newmesh = C_Mesh()
            C_Mesh.Load(newmesh, f)
            car.LodBody.append(newmesh)
    for i in range(15):
        newmesh = C_Mesh()
        C_Mesh.Load(newmesh, f)
        car.Mesh.append(newmesh)

    encodeNum = int.from_bytes(ConvertToTxt_Old(bytearray(f.read(4)), 4), 'little')
    if not encodeNum >= 0 and encodeNum <= 100:
        context.report({'ERROR'}, "파일이 손상되었습니다")
        return
    nameSize = int.from_bytes(Decode(encodeNum, ConvertToTxt_Old(bytearray(f.read(4)), 4), 4), 'little')
    if nameSize < 1 or nameSize > 40:
        context.report({'ERROR'}, "파일이 손상되었습니다")
        return
    car.SaveName = Decode(encodeNum, ConvertToTxt_Old(bytearray(f.read(nameSize)), nameSize), nameSize).decode('ISO-8859-1')

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

    for texture in car.Material:
        mat = bpy.data.materials.new(texture.TextureName)

    DecodeSS(car.Material, txd, fp)

    root = bpy.data.objects.new("empty", None)
    root.name = car.SaveName
    root.rotation_euler.x = math.radians(90.0)
    bpy.context.collection.objects.link(root)
    bpy.context.view_layer.objects.active = root

                
    for obj in car.LodBody:
        parent = write_obj(obj, root)
        for objj in obj.m_SubMesh:
            objj.m_MaterialID = car.Material[objj.m_MaterialID]
            write_obj(objj, parent)
    for obj in car.Mesh:
        parent = write_obj(obj, root)
        for objj in obj.m_SubMesh:
            objj.m_MaterialID = car.Material[objj.m_MaterialID]
            write_obj(objj, parent)

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    # bpy.ops.mesh.remove_doubles(threshold = 0.00001)
    # bpy.ops.mesh.average_normals(average_type='CUSTOM_NORMAL')
    # bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.select_all(action='DESELECT')
