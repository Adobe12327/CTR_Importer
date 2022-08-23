import os
import struct
import bpy
import addon_utils
import os
import math
from . import DecodeTable

def read_float32(f):
    return struct.unpack('f', f.read(4))[0]

def read_float16(f):
    return round(struct.unpack('f', f.read(2))[0], 4)

def read_int32(f):
    return int.from_bytes(f.read(4), 'little')

def read_int16(f):
    return int.from_bytes(f.read(2), 'little')

class _S_Material():
    def __init__(self):
        self.NameLen = 0
        self.TextureName = ''

class _S_BBox():
    def __init__(self):
        self.Coord = []
        self.Max = []
        self.Min = []

class _S_StripIndex():
    def __init__(self):
        self.Index = []
        self.IndexNum = 0
        self.GLMode = -1

class C_SubMesh():
    def __init__(self):
        self.m_DisplayListID = -1
        self.m_SubMeshName = ''
        self.m_MaterialID = -1
        self.m_nVertexNum = 0
        self.m_nFaceNum = 0
        self.m_nStripNum = 0
        self.m_nLightNum = 0
        self.m_VertexList = []
        self.m_UVVertexList = []
        self.m_VertexNList = []
        self.m_StripIndex = []

    def Load(self, f):
        NameLen = read_int32(f)
        self.m_SubMeshName = f.read(NameLen).decode('ISO-8859-1')
        self.m_MaterialID = read_int32(f)
        self.m_nVertexNum = read_int32(f)
        self.m_nFaceNum = read_int32(f)
        self.m_nStripNum = read_int32(f)
        self.m_nLightNum = read_int32(f)
        if self.m_nVertexNum > 0:
            for i in range(self.m_nVertexNum):
                self.m_VertexList.append([read_float32(f), read_float32(f), read_float32(f)])
                self.m_UVVertexList.append([read_float32(f), read_float32(f)])
                self.m_VertexNList.append([read_float32(f), read_float32(f), read_float32(f)])
        if self.m_nStripNum > 0:
            for i in range(self.m_nStripNum):
                strip = _S_StripIndex()
                strip_num = read_int32(f)
                self.m_StripIndex.append([strip, strip_num])
                strip.IndexNum = read_int32(f)
                for i in range(strip.IndexNum):
                    strip.Index.append(read_int32(f))

class C_Mesh():
    def __init__(self):
        self.m_BBox = _S_BBox()
        self.m_SubMeshNum = 0
        self.m_SubMesh = []
        self.m_TextureShaderMode = 0
        self.m_EnvTexID = -1
        self.m_MeshID = ''

    def Load(self, f):
        NameLen = read_int32(f)
        temp = f.read(NameLen).decode('ISO-8859-1')
        pdwRead = NameLen
        self.m_MeshID = temp
        self.m_SubMeshNum = read_int32(f)
        if self.m_SubMeshNum > 0:
            for i in range(self.m_SubMeshNum):
                newsubmesh = C_SubMesh()
                C_SubMesh.Load(newsubmesh, f)
                self.m_SubMesh.append(newsubmesh)
        self.m_BBox.Coord = [read_float32(f), read_float32(f), read_float32(f)]
        self.m_BBox.Max = [read_float32(f), read_float32(f), read_float32(f)]
        self.m_BBox.Min = [read_float32(f), read_float32(f), read_float32(f)]

class _S_Default_Car():
    def __init__(self) :
        self.LodLevel = 0
        self.Material = []
        self.LodBody = []
        self.Mesh = [] # 21

def get_tstrip(value):
    result = []
    for i in range(0, len(value), 2):
        try:
            a = value[i]
            b = value[i+1]
            c = value[i+2]
            d = value[i+3]
            result.append((a,b,c))
            result.append((d,c,b))
        except:
            if a != None and b != None and c != None:
                result.append((a,b,c))
            if b != None and c != None and b != None:
                result.append((d,c,b))
    return result

def write_obj(Obj:C_SubMesh, isherit, parent=None):
    if isinstance(Obj, C_SubMesh):
        mesh = bpy.data.meshes.new("mesh")  # add a new mesh
        indices = []
        for indice in Obj.m_StripIndex:
            if indice[1] == 5:
                tstrip = get_tstrip(indice[0].Index)
                for strip in tstrip:
                    indices.append((strip[0], strip[1], strip[2]))
            elif indice[1] == 4:
                for i in range(0, len(indice[0].Index), 3):
                    indices.append((indice[0].Index[i], indice[0].Index[i+1], indice[0].Index[i+2]))
        mesh.from_pydata(Obj.m_VertexList, [], indices)
        for f in mesh.polygons:
            f.use_smooth = True
        mesh.update()
        obj = bpy.data.objects.new(Obj.m_SubMeshName, mesh)
        obj.data = mesh

        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        mesh = bpy.context.selected_objects[0].data
        for vert, normal in zip(mesh.vertices, Obj.m_VertexNList):
            vert.normal = normal

        mesh.uv_layers.new(name="UVMap")

        for face in obj.data.polygons:
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                obj.data.uv_layers.active.data[loop_idx].uv = Obj.m_UVVertexList[vert_idx]

        obj.active_material = bpy.data.materials.get(Obj.m_MaterialID.TextureName)

        obj.select_set(False)

        if parent:
            parented_wm = obj.matrix_world.copy()
            obj.parent = bpy.data.objects[parent.name]
            obj.matrix_world = parented_wm

        return obj
    elif isinstance(Obj, C_Mesh):
        obj = bpy.data.objects.new("empty", None)
        obj.name = Obj.m_MeshID
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        if parent:
            parented_wm = obj.matrix_world.copy()
            obj.parent = bpy.data.objects[parent.name]
            obj.matrix_world = parented_wm
        return obj


def __ROR__(num, count, bits=8):
    return ((num >> count) | (num << (bits - count))) & ((0b1<<bits) - 1)

def ConvertToTxt_Old(data, size):
    for i in range(size):
        data[i] = __ROR__(data[i], 1) ^ 0x9E
    return data

def Decode(nCodeNum, pbyData, nLen):
    for i in range(nLen):
        pbyData[i] = DecodeTable.g_chDecodeCode1[nCodeNum][pbyData[i]]
    return pbyData

def read_b3d(filepath, txd, path_add):
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
        print('File Error')
        return
    nameSize = int.from_bytes(Decode(encodeNum, ConvertToTxt_Old(bytearray(f.read(4)), 4), 4), 'little')
    if nameSize < 1 or nameSize > 40:
        print('File Error')
        return
    saveName = Decode(encodeNum, ConvertToTxt_Old(bytearray(f.read(nameSize)), nameSize), nameSize).decode('ISO-8859-1')

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
        file = txd + '\\' +  texture.TextureName.split('.')[0] + '.ss'
        f = open(file, 'rb')
        f.read(4)
        Width = read_int32(f)
        Height = read_int32(f)
        BitLevel = read_int32(f)
        f.read(4*2)
        FrameCount = read_int32(f)
        TextureSize = read_int32(f)
        Content = bytearray(f.read(TextureSize))
        if BitLevel == 24:
            for i in range(0, len(Content), 3):
                first = Content[i]
                third = Content[i+2]
                Content[i] = third
                Content[i+2] = first
                
            Final = b''
            Final += b'\x42\x4D'
            Final += ((TextureSize) + 40 + 14).to_bytes(4, byteorder='little')
            Final += b'\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00'
            Final += Width.to_bytes(4, byteorder='little')
            Final += Height.to_bytes(4, byteorder='little')
            Final += b'\x01\x00\x18\x00\x00\x00\x00\x00'
            Final += (TextureSize).to_bytes(4, byteorder='little')
            Final += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            Final += Content
            ff = open(fp+'\\textures\\' + os.path.basename(file).split(".")[0] + ".bmp", 'wb')
            ff.write(Final)
            ff.close()
        elif BitLevel == 32:
            for i in range(0, len(Content), 4):
                first = Content[i]
                third = Content[i+2]
                Content[i] = third
                Content[i+2] = first
            Final = b''
            Final += b'\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            Final += Width.to_bytes(2, byteorder='little')
            Final += Height.to_bytes(2, byteorder='little')
            Final += b'\x20\x00'
            Final += Content
            ff = open(fp+'\\textures\\' + os.path.basename(file).split(".")[0] + ".tga", 'wb')
            ff.write(Final)
            ff.close()
        mat = bpy.data.materials.new(texture.TextureName)
        if texture.TextureName.split('.')[1].lower() == "tga":
            mat.blend_method = "CLIP"
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        try:
            texImage.image = bpy.data.images.load(fp+'textures/'+texture.TextureName)
            mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
            mat.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha'])
        except:
            if texture.TextureName.split(".")[1] == "bmp":
                texture.TextureName.replace("bmp", "tga")
            else:
                texture.TextureName.replace("tga", "bmp")
            try:
                texImage.image = bpy.data.images.load(fp+'textures/'+texture.TextureName)
                mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
                mat.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha'])
            except:
                print("Texture " + texture.TextureName.split(".")[0] + " Couldn't find")

    root = bpy.data.objects.new("empty", None)
    root.name = os.path.basename(filepath)
    root.rotation_euler.x = math.radians(90.0)
    bpy.context.collection.objects.link(root)
    bpy.context.view_layer.objects.active = root

                
    for obj in car.LodBody:
        parent = write_obj(obj, True, root)
        for objj in obj.m_SubMesh:
            objj.m_MaterialID = car.Material[objj.m_MaterialID]
            write_obj(objj, True, parent)
    for obj in car.Mesh:
        parent = write_obj(obj, True, root)
        for objj in obj.m_SubMesh:
            objj.m_MaterialID = car.Material[objj.m_MaterialID]
            write_obj(objj, True, parent)
