import os
import struct
import bpy
import addon_utils
import os
import math

def read_float32(f):
    return struct.unpack('f', f.read(4))[0]

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

class ObjectObj():
    def __init__(self):
        super().__init__()
        self.name = ''
        self.vertices = []
        self.uvs = []
        self.normals = []
        self.indices = []
        self.inherit = []
        self.material = ''


def write_obj(Obj:ObjectObj, isherit, parent=None):
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
    for f in mesh.polygons:
        f.use_smooth = True
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
    if parent:
        parented_wm = obj.matrix_world.copy()
        obj.parent = bpy.data.objects[parent.name]
        obj.matrix_world = parented_wm

def read_o3d(filepath, txd):
    f = open(filepath, 'rb')
    Objcount = read_int32(f)
    Objs = []
    TexturesCount = read_int32(f)
    for i in range(Objcount):
        useless = read_int32(f)
        f.read(useless)
        subMeshCount = read_int32(f)-1
        meshNameCount = read_int32(f)
        meshName = f.read(meshNameCount).decode('ISO-8859-1')
        MaterialIndex = read_int32(f)
        VerticesCount = read_int32(f)
        Unk2 = read_int32(f)
        IndicesCount = read_int32(f)
        f.read(4)
        startoffset = f.tell()
        Vertices = []
        for i in range(VerticesCount):
            x = struct.unpack('f', f.read(4))[0]
            y = struct.unpack('f', f.read(4))[0]
            z = struct.unpack('f', f.read(4))[0]
            Vertices.append([x,y,z])
            f.read(20)
        f.seek(startoffset+(4*3))
        UVs = []
        for i in range(VerticesCount):
            u = struct.unpack('f', f.read(4))[0]
            v = struct.unpack('f', f.read(4))[0]
            UVs.append([u,v])
            f.read(24)
        f.seek(startoffset+(4*5))
        Normals = []
        for i in range(VerticesCount):
            x = struct.unpack('f', f.read(4))[0]
            y = struct.unpack('f', f.read(4))[0]
            z = struct.unpack('f', f.read(4))[0]
            Normals.append([x,y,z])
            f.read(20)
        f.seek(-20, 1)
        Indices = []
        for i in range(IndicesCount):
            FaceType = read_int32(f)
            Counts = read_int32(f)
            asdf = []
            for i in range(Counts):
                asdf.append(read_int32(f)+1)
            Indices.append([FaceType, asdf])

        Obj = ObjectObj()
        Obj.name = meshName
        Obj.vertices = Vertices
        Obj.uvs = UVs
        Obj.normals = Normals
        Obj.indices = Indices
        Obj.material = MaterialIndex
        Objs.append(Obj)

        pmesh = meshName
        for i in range(subMeshCount):
            meshNameCount = read_int32(f)
            meshName = f.read(meshNameCount).decode('ISO-8859-1')
            MaterialIndex = read_int32(f)
            VerticesCount = read_int32(f)
            Unk2 = read_int32(f)
            IndicesCount = read_int32(f)
            f.read(4)
            startoffset = f.tell()
            Vertices = []
            for i in range(VerticesCount):
                x = struct.unpack('f', f.read(4))[0]
                y = struct.unpack('f', f.read(4))[0]
                z = struct.unpack('f', f.read(4))[0]
                Vertices.append([x,y,z])
                f.read(20)
            f.seek(startoffset+(4*3))
            UVs = []
            for i in range(VerticesCount):
                u = struct.unpack('f', f.read(4))[0]
                v = struct.unpack('f', f.read(4))[0]
                UVs.append([u,v])
                f.read(24)
            f.seek(startoffset+(4*5))
            Normals = []
            for i in range(VerticesCount):
                x = struct.unpack('f', f.read(4))[0]
                y = struct.unpack('f', f.read(4))[0]
                z = struct.unpack('f', f.read(4))[0]
                Normals.append([x,y,z])
                f.read(20)
            f.seek(-20, 1)
            Indices = []
            for i in range(IndicesCount):
                FaceType = read_int32(f)
                Counts = read_int32(f)
                asdf = []
                for i in range(Counts):
                    asdf.append(read_int32(f)+1)
                Indices.append([FaceType, asdf])
            Objj = ObjectObj()
            Objj.name = meshName
            Objj.vertices = Vertices
            Objj.uvs = UVs
            Objj.normals = Normals
            Objj.indices = Indices
            Objj.material = MaterialIndex
            Obj.inherit.append(Objj)

        f.read(36)

    fp = ''
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == "CTR Importer":
            fp = mod.__file__
            fp = fp.replace('__init__.py', '')
        else:
            pass
    
    Textures = []
    for i in range(TexturesCount):
        TextureNameCount = read_int32(f)
        TextureName = f.read(TextureNameCount).decode('ISO-8859-1')
        Textures.append(TextureName)

    try: 
        os.makedirs(fp + "\\textures")
    except:
        pass

    for texture in Textures:
        file = txd + '\\' +  texture.split('.')[0] + '.ss'
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
        except:
            pass
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


    

    for i in range(len(Objs)):
        write_obj(Objs[i], False)
        for k in range(len(Objs[i].inherit)):
            write_obj(Objs[i].inherit[k], True, Objs[i])

    return Objs