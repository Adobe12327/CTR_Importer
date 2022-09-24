import struct
import bpy
from .DecodeTable import g_chDecodeCode1
from .EncodeTable import g_chEncodeCode1
import os

def read_float32(f):
    return struct.unpack('f', f.read(4))[0]

def read_int32(f):
    return int.from_bytes(f.read(4), 'little')

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
                strip.IndexNum = read_int32(f)
                self.m_StripIndex.append([strip, strip_num])
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
        self.SaveName = ''

def get_tstrip(value):
    result = []
    for i in range(len(value)):
        try:
            a = value[i]
            b = value[i+1]
            c = value[i+2]
            result.append((a,b,c))
        except:
            pass
    return result

def write_obj(Obj:C_SubMesh, parent=None):
    if isinstance(Obj, C_SubMesh):
        mesh = bpy.data.meshes.new(Obj.m_SubMeshName)  # add a new mesh
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
        obj.data.use_auto_smooth = True

        obj.select_set(False)

        if parent:
            parented_wm = obj.matrix_world.copy()
            obj.parent = bpy.data.objects[parent.name]
            obj.matrix_world = parented_wm

        return obj
    elif isinstance(Obj, C_Mesh):
        obj = bpy.data.objects.new("empty", None)
        if Obj.m_MeshID != '':
            obj.name = Obj.m_MeshID
        else:
            obj.name = "Mesh"
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        if parent:
            parented_wm = obj.matrix_world.copy()
            obj.parent = bpy.data.objects[parent.name]
            obj.matrix_world = parented_wm
        return obj

def Decode(nCodeNum, pbyData, nLen):
    for i in range(nLen):
        pbyData[i] = g_chDecodeCode1[nCodeNum][pbyData[i]]
    return pbyData

def Encode(nCodeNum, pbyData, nLen):
    for i in range(nLen):
        pbyData[i] = g_chEncodeCode1[nCodeNum][pbyData[i]]
    return pbyData

def __ROR__(num, count, bits=8):
    return ((num >> count) | (num << (bits - count))) & ((0b1<<bits) - 1)

def ConvertToTxt_Old(data, size):
    for i in range(size):
        data[i] = __ROR__(data[i], 1) ^ 0x9E
    return data

def DecodeSS(mat, txd, fp):
    for texture in mat:
        file = txd + '\\' +  texture.TextureName.split('.')[0] + '.ss'
        try:
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
            mat = bpy.data.materials.get(texture.TextureName)
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
        except FileNotFoundError:
            pass

class _S_Face():
    def __init__(self):
        self.Normal = []
        self.Vertex = []

class _S_Gate():
    def __init__(self):
        self.GateID = 0
        self.BBox = _S_BBox()
        self.Face = [_S_Face(), _S_Face()]

    def Load(self, f):
        self.BBox.Coord = [read_float32(f), read_float32(f), read_float32(f)]
        self.BBox.Max = [read_float32(f), read_float32(f), read_float32(f)]
        self.BBox.Min = [read_float32(f), read_float32(f), read_float32(f)]
        self.Face[0].Normal = [read_float32(f), read_float32(f), read_float32(f)]
        self.Face[0].Vertex = [[[read_float32(f), read_float32(f), read_float32(f)]], [[read_float32(f), read_float32(f), read_float32(f)]], [[read_float32(f), read_float32(f), read_float32(f)]]]
        self.Face[1].Normal = [read_float32(f), read_float32(f), read_float32(f)]
        self.Face[1].Vertex = [[[read_float32(f), read_float32(f), read_float32(f)]], [[read_float32(f), read_float32(f), read_float32(f)]], [[read_float32(f), read_float32(f), read_float32(f)]]]

class _S_CModule():
    def __init__(self):
        self.Attribute = 0
        self.FaceNum = 0
        self.BBox = _S_BBox()
        self.Face = []
    
    def Load(self, f):
        self.Attribute = read_int32(f)
        self.FaceNum = read_int32(f)
        self.BBox.Coord = [read_float32(f), read_float32(f), read_float32(f)]
        self.BBox.Max = [read_float32(f), read_float32(f), read_float32(f)]
        self.BBox.Min = [read_float32(f), read_float32(f), read_float32(f)]
        for i in range(self.FaceNum):
            face = _S_Face()
            face.Normal = [read_float32(f), read_float32(f), read_float32(f)]
            face.Vertex = [[[read_float32(f), read_float32(f), read_float32(f)]], [[read_float32(f), read_float32(f), read_float32(f)]], [[read_float32(f), read_float32(f), read_float32(f)]]]


class _S_Collision():
    def __init__(self):
        self.RoadModuleNum = 0
        self.FenceModuleNum = 0
    
    def Load(self, f):
        self.RoadModuleNum = read_int32(f)
        self.FenceModuleNum = read_int32(f)
        for i in range(self.RoadModuleNum):
            module = _S_CModule()
            module.Load(f)
        for i in range(self.FenceModuleNum):
            module = _S_CModule()
            module.Load(f)

def loadmesh(mesh, root, track):
    if mesh.m_SubMeshNum == 1:
        mesh.m_SubMesh[0].m_MaterialID = track.m_Material[mesh.m_SubMesh[0].m_MaterialID]
        write_obj(mesh.m_SubMesh[0], root)
    else:
        parent = write_obj(mesh, root)
        for sub in mesh.m_SubMesh:
            sub.m_MaterialID = track.m_Material[sub.m_MaterialID]
            write_obj(sub, parent)

class C_Node():
    def __init__(self):
        self.m_nNearNodeNum = 0
        self.m_nStructureNum = 0
        self.m_nInstallNum = 0
        self.m_nUnderSignNum = 0
        self.m_nDummyNum = 0
        self.m_nLightNum = 0
        self.m_nGateNum = 0
        self.m_nDestNum = 0
        self.m_OneSideInstallNum = 0
        self.m_nLightMapNum = 0

        self.m_nGuildFlagNum = 0
        self.m_BillboardNum = 0
        self.m_CheckPointNum = 0

        self.m_ReservedNum = []

        self.m_RoadAttachmentNum = 0
        self.m_PokjuZoneNum = 0
        self.m_GuildBattleZoneNum = 0
        self.m_DriftZoneNum = 0
        self.m_MyNodeIndex = 0
        self.m_NearNodeIndex = 0
        self.m_RoadAttachmentIndex = 0

        self.m_Road = C_Mesh()
        self.m_Fence = C_Mesh()
        self.m_Structure = []
        self.m_Install = []
        self.m_UnderSign = []
        self.m_Dummy = []
        self.m_Light = []
        self.m_Gate = []
        self.m_Dest = []
        self.m_OneSideInstall = []
        self.m_LightMap = []
        self.m_GuildFlag = []
        self.m_Billboard = []
        self.m_CheckPoint = []
        self.m_RoadAttachment = []
        self.m_PokjuZone = []
        self.m_GuildBattleZone = []
        self.m_DriftZone = []
        self.m_CollisionInfo = []
    def Load(self, f, MapVersion):
        self.m_nNearNodeNum = read_int32(f)
        self.m_nStructureNum = read_int32(f)
        self.m_nInstallNum = read_int32(f)
        self.m_nUnderSignNum = read_int32(f)
        self.m_nDummyNum = read_int32(f)
        self.m_nLightNum = read_int32(f)
        self.m_nGateNum = read_int32(f)
        self.m_nDestNum = read_int32(f)
        self.m_OneSideInstallNum = read_int32(f)
        self.m_nLightMapNum = read_int32(f)

        if MapVersion >= 5:
            self.m_nGuildFlagNum = read_int32(f)
        self.m_BillboardNum = read_int32(f)
        self.m_CheckPointNum = read_int32(f)
        if MapVersion >= 4:
            self.m_RoadAttachmentNum = read_int32(f)

        for i in range(27):
            self.m_ReservedNum.append(read_int32(f))
        if MapVersion >= 2:
            self.m_PokjuZoneNum = read_int32(f)
        if MapVersion >= 5:
            self.m_GuildBattleZoneNum = read_int32(f)
        if MapVersion >= 6:
            self.m_DriftZoneNum = read_int32(f)
        f.read(12*3)
        self.m_Road.Load(f)
        self.m_Fence.Load(f)
        for i in range(self.m_nNearNodeNum):
            read_int32(f)
        for i in range(self.m_nStructureNum):
            self.m_Structure.append(read_int32(f))
        for i in range(self.m_nInstallNum):
            self.m_Install.append(read_int32(f))
        for i in range(self.m_nUnderSignNum):
            self.m_UnderSign.append(read_int32(f))
        for i in range(self.m_nDummyNum):
            self.m_Dummy.append(read_int32(f))
        for i in range(self.m_nLightNum):
            self.m_Light.append(read_int32(f))
        for i in range(self.m_nGateNum):
            self.m_Gate.append(read_int32(f))
        for i in range(self.m_nDestNum):
            self.m_Dest.append(read_int32(f))
        for i in range(self.m_OneSideInstallNum):
            self.m_OneSideInstall.append(read_int32(f))
        for i in range(self.m_nLightMapNum):
            self.m_LightMap.append(read_int32(f))
        if MapVersion >= 5:
            for i in range(self.m_nGuildFlagNum):
                self.m_GuildFlag.append(read_int32(f))
        for i in range(self.m_BillboardNum):
            self.m_Billboard.append(read_int32(f))
        for i in range(self.m_CheckPointNum):
            self.m_CheckPoint.append(read_int32(f))
        if MapVersion >= 4:
            self.m_RoadAttachment.append(read_int32(f))
        for i in range(27):
            f.read(4*self.m_ReservedNum[i])
        if MapVersion >= 2:
            for i in range(self.m_PokjuZoneNum):
                self.m_PokjuZone.append(read_int32(f))
        if MapVersion >= 5:
            for i in range(self.m_GuildBattleZoneNum):
                self.m_GuildBattleZone.append(read_int32(f))
        if MapVersion >= 6:
            for i in range(self.m_DriftZoneNum):
                self.m_DriftZone.append(read_int32(f))
        col = _S_Collision()
        col.Load(f)


class C_Track():
    def __init__(self):
        self.MapVersion = 0
        self.m_nNodeNum = 0
        self.m_nMaterialNum = 0
        self.m_nStructureNum = 0
        self.m_nInstallNum = 0
        self.m_nUnderSignNum = 0
        self.m_nDummyNum = 0
        self.m_nLightNum = 0
        self.m_nGateNum = 0
        self.m_nDestNum = 0
        self.m_WarpZoneNum = 0
        self.m_OneSideInstallNum = 0
        self.m_nLightMapNum = 0

        #map version 5 이상
        self.m_nGuildFlagNum = 0
        self.m_BillboardNum = 0
        self.m_CheckPointNum = 0

        #map version 4 이상
        self.m_nRoadAttachmentNum = 0

        self.m_ReservedNum = []

        #map version 2 이상
        self.m_PokjuZoneNum = 0
        #map version 3 이상
        self.m_AdvencedZoneNum = 0
        #map version 5 이상
        self.m_GuildBattleZoneNum = 0
        #map version 6 이상
        self.m_DriftZoneNum = 0

        self.m_Node = []
        self.m_Material = []
        self.m_Structure = []
        self.m_Install = []
        self.m_UnderSign = []
        self.m_Dummy = []
        self.m_Light = []
        self.m_Gate = []
