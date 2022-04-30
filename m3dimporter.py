from codecs import StreamReader
import math
import addon_utils
import struct
import bpy
import os 
import bmesh

def read_float32(f):
    return round(struct.unpack('f', f.read(4))[0], 4)

def read_float16(f):
    return round(struct.unpack('f', f.read(2))[0], 4)

def read_int32(f):
    return int.from_bytes(f.read(4), 'little')

def read_int16(f):
    return int.from_bytes(f.read(2), 'little')

def get_tstrip(values):
    result = []
    for i in range(0, len(values), 2):
        try:
            a = values[i]-1
            b = values[i+1]-1
            c = values[i+2]-1
            d = values[i+3]-1
            result.append((a,b,c))
            result.append((d,c,b))
        except:
            if a != None and b != None and c != None:
                result.append((a,b,c))
            if b != None and c != None and b != None:
                result.append((d,c,b))
    return result

class MapObj():
    def __init__(self):
        super().__init__()
        self.name = ''
        self.vertices = []
        self.uvs = []
        self.normals = []
        self.indices = []
        self.inherit = []
        self.material = ''

# def write_obj(Obj:MapObj, isherit, parent=None):
#     if isherit == True:
#         ff = open(parent.name+'_'+Obj.name+'.obj', 'w')
#         Obj.name = parent.name+'_'+Obj.name
#     else:
#         ff = open(Obj.name+'.obj', 'w')
#         Obj.name = Obj.name
#         ff.write(f"g {Obj.name}\n")
#     for vert in Obj.vertices:
#         ff.write(f'v {vert[0]} {vert[1]} {vert[2]}\n')
#     for uv in Obj.uvs:
#         ff.write(f'vt {uv[0]} {uv[1]}\n')
#     for normal in Obj.normals:
#         ff.write(f'vn {normal[0]} {normal[1]} {normal[2]}\n')
#     for indice in Obj.indices:
#         if indice[0] == 5:
#             tstrip = get_tstrip(indice[1])
#             for strip in tstrip:
#                 ff.write(f'f {strip[0]}/{strip[0]}/{strip[0]} {strip[1]}/{strip[1]}/{strip[1]} {strip[2]}/{strip[2]}/{strip[2]}\n')
#         elif indice[0] == 4:
#             for i in range(0, len(indice[1]), 3):
#                 ff.write(f'f {indice[1][i]}/{indice[1][i]}/{indice[1][i]} {indice[1][i+1]}/{indice[1][i+1]}/{indice[1][i+1]} {indice[1][i+2]}/{indice[1][i+2]}/{indice[1][i+2]}\n')
#     ff.close()

def write_obj(Obj:MapObj, isherit, parent=None):
    mesh = bpy.data.meshes.new("mesh")  # add a new mesh
    indices = []
    for indice in Obj.indices:
        if indice[0] == 5:
            tstrip = get_tstrip(indice[1])
            for strip in tstrip:
                indices.append((strip[0], strip[1], strip[2]))
        elif indice[0] == 4:
            for i in range(0, len(indice[1]), 3):
                indices.append((indice[1][i]-1, indice[1][i+1]-1, indice[1][i+2]-1))
    mesh.from_pydata(Obj.vertices, [], indices)
    mesh.update()
    obj = bpy.data.objects.new(Obj.name, mesh)
    obj.data = mesh

    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select = True

    mesh = bpy.context.selected_objects[0].data
    for vert, normal in zip(mesh.vertices, Obj.normals):
        vert.normal = normal

    mesh.uv_layers.new(name="UVMap")

    for face in obj.data.polygons:
        for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
            obj.data.uv_layers.active.data[loop_idx].uv = Obj.uvs[vert_idx]
    
    obj.active_material = bpy.data.materials.get(Obj.material)

    obj.select = False

    obj.rotation_euler.x = math.radians(90.0)

def read_obj(f:StreamReader, issubmesh):
    Obj = MapObj()
    subMeshCount = None
    if issubmesh == False:
        subMeshCount = read_int32(f)-1
        if subMeshCount < 0:
            return None, None
    meshNameCount = read_int32(f)
    Obj.name = f.read(meshNameCount).decode('ISO-8859-1')
    if Obj.name == '':
        Obj.name = 'mesh_' +  str(f.tell())
    Obj.material = read_int32(f)
    VerticesCount = read_int32(f)
    Unk2 = read_int32(f)
    IndicesCount = read_int32(f)
    f.read(4)
    startoffset = f.tell()
    Vertices = Obj.vertices
    for i in range(VerticesCount):
        x = round(struct.unpack('f', f.read(4))[0], 4)
        y = round(struct.unpack('f', f.read(4))[0], 4)
        z = round(struct.unpack('f', f.read(4))[0], 4)
        Vertices.append((x,y,z))
        f.read(20)
    f.seek(startoffset+(4*3))
    UVs = Obj.uvs
    for i in range(VerticesCount):
        u = round(struct.unpack('f', f.read(4))[0], 4)
        v = round(struct.unpack('f', f.read(4))[0], 4)
        UVs.append((u,v))
        f.read(24)
    f.seek(startoffset+(4*5))
    Normals = Obj.normals
    for i in range(VerticesCount):
        x = round(struct.unpack('f', f.read(4))[0], 4)
        y = round(struct.unpack('f', f.read(4))[0], 4)
        z = round(struct.unpack('f', f.read(4))[0], 4)
        Normals.append((x,y,z))
        f.read(20)
    f.seek(-20, 1)
    Indices = Obj.indices
    for i in range(IndicesCount):
        FaceType = read_int32(f)
        Counts = read_int32(f)
        asdf = []
        for i in range(Counts):
            asdf.append(read_int32(f)+1)
        Indices.append([FaceType, asdf])

    return Obj, subMeshCount

def read_m3d(filepath, txd):
    print(filepath)
    f = open(filepath, 'rb')
    Unk1 = read_int32(f)
    Unktable1 = []
    UnkIndices = []
    Textures = []
    if Unk1 == 1:
        for i in range(6):
            Unktable1.append(read_int32(f))
        f.seek(0xA8, 0)
    elif Unk1 == 2:
        for i in range(6):
            Unktable1.append(read_int32(f))
        f.seek(0xAC, 0)
    Objs = []
    for i in range(len(Unktable1)):
        if i == 0:
            for ii in range(Unktable1[i]):
                UnkIndices = []
                for k in range(10):
                    UnkIndices.append(read_int32(f))
                if Unk1 == 1:
                    f.read(0x70)
                    Unk3 = read_int32(f)
                    f.read(0x28)
                elif Unk1 == 2:
                    f.read(0x74)
                    Unk3 = read_int32(f)
                    f.read(0x28)
                for k in range(2):
                    print(f.tell())
                    Obj, subMeshCount = read_obj(f, False)
                    if Obj != None:
                        for i in range(subMeshCount):
                            SubMesh = read_obj(f, True)[0]
                            Obj.inherit.append(SubMesh)
                        Objs.append(Obj)
                        f.read(40)
                    else:
                        f.read(0x28)
                f.seek(-4, 1)
                for i in range(len(UnkIndices)):
                    f.read(UnkIndices[i]*4)
                for i in range(Unk3):
                    f.read(4)
                UnkVertices = []
                for i in range(2):
                    UnkVertices.append(read_int32(f))
                for i in range(len(UnkVertices)):
                    for k in range(UnkVertices[i]):
                        f.read(4)
                        count = read_int32(f)-2
                        final = 0x30*count
                        f.read(0x84+final)
        elif i==1:
            for i in range(Unktable1[i]):
                NameCount = read_int32(f)
                Textures.append(f.read(NameCount).decode('ISO-8859-1'))
        else:
            for i in range(Unktable1[i]):
                print(f.tell())
                Obj = MapObj()
                meshNameCount = read_int32(f)
                Obj.name = f.read(meshNameCount).decode('ISO-8859-1').replace("*","-")
                subMeshCount = read_int32(f)-1
                f.read(4)
                f.read(meshNameCount)
                Obj.material = read_int32(f)
                VerticesCount = read_int32(f)
                Unk2 = read_int32(f)
                IndicesCount = read_int32(f)
                f.read(4)
                startoffset = f.tell()
                Vertices = Obj.vertices
                for i in range(VerticesCount):
                    x = round(struct.unpack('f', f.read(4))[0], 4)
                    y = round(struct.unpack('f', f.read(4))[0], 4)
                    z = round(struct.unpack('f', f.read(4))[0], 4)
                    Vertices.append((x,y,z))
                    f.read(20)
                f.seek(startoffset+(4*3))
                UVs = Obj.uvs
                for i in range(VerticesCount):
                    u = round(struct.unpack('f', f.read(4))[0], 4)
                    v = round(struct.unpack('f', f.read(4))[0], 4)
                    UVs.append((u,v))
                    f.read(24)
                f.seek(startoffset+(4*5))
                Normals = Obj.normals
                for i in range(VerticesCount):
                    x = round(struct.unpack('f', f.read(4))[0], 4)
                    y = round(struct.unpack('f', f.read(4))[0], 4)
                    z = round(struct.unpack('f', f.read(4))[0], 4)
                    Normals.append((x,y,z))
                    f.read(20)
                f.seek(-20, 1)
                Indices = Obj.indices
                for i in range(IndicesCount):
                    FaceType = read_int32(f)
                    Counts = read_int32(f)
                    asdf = []
                    for i in range(Counts):
                        asdf.append(read_int32(f)+1)
                    Indices.append([FaceType, asdf])
                Objs.append(Obj)
                # print(f.tell())
                f.read(0x24)
    names = {}
    for i in range(len(Objs)):
        try:
            names[Objs[i].name]
            names[Objs[i].name] += "_"+str(i)
            Objs[i].name += "_"+str(i)
        except:
            names[Objs[i].name] = Objs[i].name

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

    for texture in Textures:
        file = txd + '\\' +  texture.split('.')[0] + '.ss'
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
        mat = bpy.data.materials.new(texture)
        if texture.split('.')[1].lower() == "tga":
            mat.blend_method = "CLIP"
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        try:
            texImage.image = bpy.data.images.load(fp+'textures/'+texture)
            mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
            mat.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha'])
        except:
            if texture.split(".")[1] == "bmp":
                texture.replace("bmp", "tga")
            else:
                texture.replace("tga", "bmp")
            try:
                texImage.image = bpy.data.images.load(fp+'textures/'+texture)
                mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
                mat.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha'])
            except:
                print("Texture " + texture.split(".")[0] + " Couldn't find")
            
    for obj in Objs:
        obj.material = Textures[obj.material]
        for objj in obj.inherit:
            objj.material = Textures[objj.material]

    # write_obj(Objs[0], False)
    for i in range(len(Objs)):
        write_obj(Objs[i], False)
        for k in range(len(Objs[i].inherit)):
            write_obj(Objs[i].inherit[k], True, Objs[i])