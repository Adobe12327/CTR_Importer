import os
import bpy
import math
import addon_utils
from .utils import read_int32, C_Mesh, _S_Material, C_Track, C_Node, _S_Gate, DecodeSS, write_obj, loadmesh

def load_mesh(f, track, name, root, count):
    rooot = bpy.data.objects.new("empty", None)
    rooot.name = name
    bpy.context.collection.objects.link(rooot)
    bpy.context.view_layer.objects.active = rooot
    rooot.parent = bpy.data.objects[root.name]
    for i in range(count):
        newmesh = C_Mesh()
        C_Mesh.Load(newmesh, f)
        loadmesh(newmesh, rooot, track)

def read_m3d(filepath, txd, path_add, context):
    f = open(filepath, 'rb')
    txd += path_add
    root = bpy.data.objects.new("empty", None)
    root.name = os.path.basename(filepath)
    root.rotation_euler.x = math.radians(90.0)
    bpy.context.collection.objects.link(root)
    bpy.context.view_layer.objects.active = root
    track = C_Track()
    track.MapVersion = read_int32(f)
    track.m_nNodeNum = read_int32(f)
    track.m_nMaterialNum = read_int32(f)
    track.m_nStructureNum = read_int32(f)
    track.m_nInstallNum = read_int32(f)
    track.m_nUnderSignNum = read_int32(f)
    track.m_nDummyNum = read_int32(f)
    track.m_nLightNum = read_int32(f)
    track.m_nGateNum = read_int32(f)
    track.m_nDestNum = read_int32(f)
    track.m_WarpZoneNum = read_int32(f)
    track.m_OneSideInstallNum = read_int32(f)
    track.m_nLightMapNum = read_int32(f)
    if track.MapVersion >= 5:
        track.m_nGuildFlagNum = read_int32(f)
    track.m_BillboardNum = read_int32(f)
    track.m_CheckPointNum = read_int32(f)
    if track.MapVersion >= 4:
        track.m_nRoadAttachmentNum = read_int32(f)

    for i in range(27):
        track.m_ReservedNum.append(read_int32(f))

    if track.MapVersion >= 2:
        track.m_PokjuZoneNum = read_int32(f)
    if track.MapVersion >= 3:
        track.m_AdvencedZoneNum = read_int32(f)
    if track.MapVersion >= 5:
        track.m_GuildBattleZoneNum = read_int32(f)
    if track.MapVersion >= 6:
        track.m_DriftZoneNum = read_int32(f)
    
    if track.m_nNodeNum > 0:
        for i in range(track.m_nNodeNum):
            node = C_Node()
            C_Node.Load(node, f, track.MapVersion)
            track.m_Node.append(node)
        
    if not track.m_nMaterialNum <= 0:
        for i in range(track.m_nMaterialNum):
            mat = _S_Material()
            mat.NameLen = read_int32(f)
            mat.TextureName = f.read(mat.NameLen).decode('ISO-8859-1')
            track.m_Material.append(mat)

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

    for texture in track.m_Material:
        mat = bpy.data.materials.new(texture.TextureName)

    DecodeSS(track.m_Material, txd, fp)

    if track.m_nNodeNum > 0:
        noderoot = bpy.data.objects.new("empty", None)
        noderoot.name = "Nodes"
        bpy.context.collection.objects.link(noderoot)
        bpy.context.view_layer.objects.active = noderoot
        noderoot.parent = bpy.data.objects[root.name]
        for node in track.m_Node:
            noderoot_ = bpy.data.objects.new("empty", None)
            noderoot_.name = "Node"
            bpy.context.collection.objects.link(noderoot_)
            bpy.context.view_layer.objects.active = noderoot_
            noderoot_.parent = bpy.data.objects[noderoot.name]
            loadmesh(node.m_Road, noderoot, track)
            loadmesh(node.m_Fence, noderoot, track)

    if track.m_nStructureNum > 0:
        load_mesh(f, track, "Structure", root, track.m_nStructureNum)
    if track.m_nInstallNum > 0:
        load_mesh(f, track, "Install", root, track.m_nInstallNum)
    if track.m_nUnderSignNum > 0:
        load_mesh(f, track, "UnderSign", root, track.m_nUnderSignNum)
    if track.m_nDummyNum > 0:
        load_mesh(f, track, "Dummy", root, track.m_nDummyNum)
    if track.m_nLightNum > 0:
        load_mesh(f, track, "Light", root, track.m_nLightNum)
    
    if track.m_nGateNum > 0:
        for i in range(track.m_nGateNum):
            newmesh = _S_Gate()
            _S_Gate.Load(newmesh, f)
            track.m_Gate.append(newmesh)
