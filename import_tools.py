#  ***** GPL LICENSE BLOCK *****
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  All rights reserved.
#  ***** GPL LICENSE BLOCK *****

import bpy
import os
from pathlib import Path
from . import orbiter_tools


class OrbiterImportSettings:
    """Container for the import settings."""

    def __init__(self,
                 verbose=False,
                 swap_yz=True):

        self.verbose = verbose
        self.swap_yz = swap_yz
        
        self.log_file_path = orbiter_tools.build_file_path(
            orbiter_tools.get_log_folder(), "BlenderTools", ".log")
        if self.verbose:
            try:
                self.log_file = open(self.log_file_path, 'w')
                print("Log file output to: {}".format(self.log_file_path))
            except Exception as error:
                print("Error opening logfile: {}".format(error))
                self.verbose = False

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.verbose:
            self.log_file.close()

    def log_line(self, log_string):
        if self.verbose:
            self.log_file.write(log_string + "\n")


class MeshException(Exception):
    pass


class ImportGroup():
    """ Import Group """

    def __init__(self):
        self.mat_index = 0
        self.tex_index = 0
        self.tex_wrap = None
        self.nonormal = False
        self.flag = None
        self.num_verts = 0
        self.num_tris = 0
        self.tris = []
        self.verts = []
        self.num_vert_entries = 0
        self.name = None

    def get_vert_size(self):
        """
        Return the number of entries in one vertex line.  This can be
        either 3, 6, or 8, and tells us if the line contains normals
        and UV data.
        Return of 0 indicates the Group has no vertices (has not been read).
        """
        if len(self.verts) == 0:
            return 0
        else:
            return len(self.verts[0])


class ImportMaterial():
    """
    Object container for materials as read from the mesh file.
    'name' is the name of the material in the mesh file.
    """

    def __init__(self, name):
        namepart = name.split(';')  # Remove any comments
        self.name = namepart[0].rstrip()
        self.diffuse = [0.0, 0.0, 0.0, 0.0]
        self.ambient = [0.0, 0.0, 0.0, 0.0]
        self.specular = [0.0, 0.0, 0.0, 0.0, 0.0]
        self.emissive = [0.0, 0.0, 0.0, 0.0]


def ensure_mesh(file):
    if "MSHX1" not in file.readline().upper():
        raise MeshException("File missing MSHX1 header")

    while True:
        parts = file.readline().split()
        if "GROUP" in parts[0].upper():
            return int(parts[1])


def read_group(file):
    """
    Read a mesh group from the mesh file.
    Return an ImportGroup object.
    ImportGroup contains the material and texture index,
    at this point we don't have a name for them.
    """
    new_group = ImportGroup()
    flag = ""
    while True:
        decomment = file.readline().split(';')
        # If something needs the comment, uncomment below, currently nothing does.
        # comment = decomment[1] if len(decomment) > 1 else None
        parts = decomment[0].split()
        if len(parts) == 0:
            continue
        flag = parts[0]
        if "MATERIAL" in flag.upper():
            if len(parts) < 2:
                raise MeshException(
                    "Invalid MATERIAL statement: {}".format(parts))
            new_group.mat_index = int(parts[1])

        if "TEXTURE" in flag.upper():
            if len(parts) < 2:
                raise MeshException(
                    "Invalid TEXTURE statement: {}".format(parts))
            new_group.tex_index = int(parts[1])

        if "TEXWRAP" in flag.upper():
            if len(parts) < 2:
                raise MeshException(
                    "Invalid TEXWRAP statement: {}".format(parts))
            new_group.tex_wrap = parts[1]

        if "NONORMAL" in flag.upper():
            new_group.nonormal = True

        if "FLAG" in flag.upper():
            new_group.flag = parts[1]

        if "LABEL" in flag.upper():
            new_group.name = "_".join(parts[1:])

        if "GEOM" in flag.upper():
            if len(parts) < 3:
                raise MeshException("Invalid GEOM statement: {}".format(parts))
            new_group.num_verts = int(parts[1])
            new_group.num_tris = int(parts[2])
            break

    sc = lambda x: x.split(';')[0]  # Clean out any comments
    for _ in range(new_group.num_verts):
        new_group.verts.append(sc(file.readline()).split())

    for _ in range(new_group.num_tris):
        new_group.tris.append(sc(file.readline()).split())

    return new_group


def read_materials(file):
    """
    Read MATERIALS block from the mesh file.
    Returns a list of ImportMaterial objects.
    The Orbiter material list is index 1-based, so this method
    creates a 0 position default material to use when a group
    does not call for a material.
    """
    parts = file.readline().split()
    if len(parts) < 2 or "MATERIALS" not in parts[0]:
        raise MeshException(
            "Mesh error, MATERIALS block missing or malformed.")

    num_materials = int(parts[1])
    materials = []
    materials.append(ImportMaterial("default"))  # Add default material.

    for matidx in range(num_materials):
        materials.append(ImportMaterial(file.readline()))

    for matidx in range(num_materials):
        sc = lambda x: x.split(';')[0]  # Clean out any comments
        file.readline()  # Read past material header
        materials[matidx + 1].diffuse = sc(file.readline()).split()
        materials[matidx + 1].ambient = sc(file.readline()).split()
        materials[matidx + 1].specular = sc(file.readline()).split()
        materials[matidx + 1].emissive = sc(file.readline()).split()

    return materials


def read_textures(file):
    """
    Read TEXTURES block from mesh file.
    Returns list of tuples: (name, (bool)is_dynamic)
    """
    parts = file.readline().split()
    if len(parts) < 2 or "TEXTURES" not in parts[0]:
        raise MeshException("Mesh error, TEXTURES block missing or malformed.")

    num_textures = int(parts[1])
    tex_names = []
    tex_names.append(("", False))  # add default empty texture.
    for _ in range(num_textures):
        tex_name = file.readline().split(';')[0].rstrip()
        is_dynamic = False
        if tex_name.endswith(' D'):
            is_dynamic = True
            tex_name = tex_name[:-2]

        tex_names.append((tex_name, is_dynamic))

    return tex_names


def get_verts(group, swap_yz = True):
    """
    Returns the collection of vertices, normals, and uvs for a group.

    A vertex line is in the form:
    vx vy vz [nx ny nz [u v]]
    so can have len of 3, 5, 6, or 8.
    """
    verts = []
    normals = []
    uvs = []

    for vert in group.verts:
        vts = [float(v) for v in vert]
        if swap_yz:
            verts.append([vts[0], vts[2], vts[1]])  # swap y-z
        else:
            verts.append([0 - vts[0], vts[1], vts[2]])

        lenvts = len(vts)
        if lenvts == 3:  # no normals or uvs, but we still need entries.
            uvs.append([0.0, 0.0])
            normals.append([0.0, 0.0, 0.0])
        if lenvts == 5:  # no normals, but yes uvs
            uvs.append(vts[3:])
            normals.append([0.0, 0.0, 0.0])
        if lenvts == 6:
            if swap_yz:
                normals.append([vts[3], vts[5], vts[4]])    # swap y - z
            else:
                normals.append([0 - vts[3], vts[4], vts[5]])
            uvs.append([0.0, 0.0])
        if lenvts == 8:
            if swap_yz:
                normals.append([vts[3], vts[5], vts[4]])    # swap y - z
            else:
                normals.append([0 - vts[3], vts[4], vts[5]])
            uvs.append(vts[6:])

    return verts, normals, uvs


def get_tris(group, swap_yz = True):
    tris = []
    for tri in group.tris:
        tr = [int(t) for t in tri]
        #if swap_yz:
        tris.append([tr[0], tr[2], tr[1]])  # Change order from Orbiter
        #else:
        #    tris.append([tr[0], tr[1], tr[2]])
    return tris


def resolve_texture_path(config, orbiter_path, tex_name):
    """
    Resolve the texture file path.  Textures can be in Orbiter\\Textures,
    or sometimes in Orbiter\\Textures2.  Textures2 is searched first, if not
    found then Textures will be searched.
    """
    tex2_file = os.path.join(orbiter_path, "Textures2", tex_name)
    tex_file = os.path.join(orbiter_path, "Textures", tex_name)
    if os.path.exists(tex2_file):
        config.log_line("Texture: {}".format(tex2_file))
        return tex2_file

    if os.path.exists(tex_file):
        config.log_line("Texture: {}".format(tex_file))
        return tex_file

    print("WARN: Texture file not found: {}".format(tex_name))
    config.log_line("WARN: Missing texture:[{}], [{}]".format(tex2_file, tex_file))
    return ""


def build_mat_textures(
        config,
        orbiter_path,
        scene_name,
        mesh_groups,
        materials,
        textures):
    """
    In Blender, materials are shared between scenes.  In Orbiter they belong
    to a mesh, so as we create materials and textures we will make them unique
    to this mesh file.  Furthermore, in Orbiter a material can be used with
    different textures on different mesh groups.  In Blender we will create a
    unique material+texture for each combination used.  That makes using
    material+nodes+textures in Blender easier.

    What this method does is look at the combination of material + texture in
    the mesh file and create a material for each combination.  If the texture
    index is not 0, then an image texture node is created for that material.

    Returns a dictionary of [mat_index, tex_index] -> new material name, which
    can then be used to assign a new material to a mesh group.
    """

    # Here we are creating a list of tuples comprised of the material and
    # texture index from the mesh groups.  Then we eliminate duplicates to get
    # the unique set of material+texture combinations in the mesh file.
    mat_tex = [(g.mat_index, g.tex_index) for g in mesh_groups]
    mat_tex = list(set(mat_tex))  # remove dups.

    config.log_line(
        "{} material + texture combinations found.".format(len(mat_tex)))
    dict_mat = {}
    max_mat_idx = len(materials)
    for mt in mat_tex:
        mat_idx = mt[0]
        config.log_line("Start material: Mat:{}, Tex:{}".format(mat_idx, mt[1]))
        if mat_idx > max_mat_idx:
            mat_idx = 0
            warn = "INVALID MATERIAL: Material index out of range ({}), using 0"
            config.log_line(warn.format(mat_idx))
            print(warn.format(mat_idx))

        src_mat = materials[mat_idx]
        src_tex = textures[mt[1]][0]  # tuple, [0] is the texture name
        src_tex_file = ""
        if src_tex:   # Material has a texture
            mat_name = "{}_{}_{}".format(
                src_mat.name, src_tex.split(".")[0], scene_name)
            src_tex_file = resolve_texture_path(config, orbiter_path, src_tex)
            print("Tex: {}".format(src_tex_file))
        else:
            mat_name = "{}_{}".format(src_mat.name, scene_name)
        #  Note: Blender will truncate material names at 64, so mat_name
        #  may not be the actual name.  Use new_mat.name in the dictionary.
        new_mat = bpy.data.materials.new(mat_name)
        new_mat.diffuse_color = [float(c) for c in src_mat.diffuse[:4]]
        new_mat.orbiter_ambient_color = [float(c) for c in src_mat.ambient[:4]]
        new_mat.orbiter_specular_color = [
            float(c) for c in src_mat.specular[:4]
            ]
        if len(src_mat.specular) > 4:
            new_mat.orbiter_specular_power = float(src_mat.specular[4])
        else:
            new_mat.orbiter_specular_power = 0
        new_mat.orbiter_emit_color = [float(c) for c in src_mat.emissive[:4]]
        config.log_line("Created material: {}->{}".format(mt, new_mat.name))
        config.log_line("  diffuse : {0:.4}, {0:.4}, {0:.4}, {0:.4}".format(
            *new_mat.diffuse_color))
        config.log_line("  ambient : {0:.4}, {0:.4}, {0:.4}, {0:.4}".format(
            *new_mat.orbiter_ambient_color))
        config.log_line("  specular: {0:.4}, {0:.4}, {0:.4}, {0:.4}".format(
            *new_mat.orbiter_specular_color))
        config.log_line("     power: {0:.4}".format(
            new_mat.orbiter_specular_power))
        config.log_line("  emissive: {0:.4}, {0:.4}, {0:.4}, {0:.4}".format(
            *new_mat.orbiter_emit_color))
        if src_tex:
            config.log_line("  texture node image: {}".format(src_tex_file))
            new_mat.use_nodes = True
            bsdf = new_mat.node_tree.nodes["Principled BSDF"]
            texImage = new_mat.node_tree.nodes.new('ShaderNodeTexImage')
            texImage.image = bpy.data.images.load(src_tex_file)
            new_mat.node_tree.links.new(
                bsdf.inputs['Base Color'], texImage.outputs['Color'])

        dict_mat[mt] = new_mat.name     # dict: (tuple) -> mat name.
    config.log_line("Finished building {} materials.".format(len(dict_mat)))
    return dict_mat


def read_mesh_file(config, file_path):
    """
    Reads the entire mesh file, returning the groups, materials and
    texture collections.
    """
    config.log_line("Reading mesh file: {}".format(file_path))
    try:
        with open(file_path, "r") as file:
            n_groups = ensure_mesh(file)
            groups = []
            for _ in range(n_groups):
                groups.append(read_group(file))

            materials = read_materials(file)
            textures = read_textures(file)
    except Exception as error:
        config.log_line("Error parsing file {}".format(error))
        raise error

    config.log_line(
        "Finished reading mesh file.  Grps: {}, Mats: {}, Texs: {}".format(
            len(groups), len(materials) - 1, len(textures) - 1))

    return groups, materials, textures


def import_mesh(config, file_path):
    """ Import an Orbiter mesh file into Blender. """
    config.log_line("Import start: {}".format(file_path))

    scene_name = bpy.path.display_name_from_filepath(file_path)
    config.log_line("Target scene: {}".format(scene_name))

    # find the Orbiter path
    p = Path(file_path)
    up = [pp.lower() for pp in p.parts]
    msh_index = up.index('meshes')
    orbiter_path = os.path.join(*p.parts[0:msh_index])
    print("Orbiter path: {}".format(orbiter_path))

    groups, materials, textures = read_mesh_file(config, file_path)
    mat_dict = build_mat_textures(
        config,
        orbiter_path,
        scene_name,
        groups,
        materials,
        textures)

    new_scene = bpy.data.scenes.new(name=scene_name)
    config.log_line("Start building {} groups in scene: {}".format(len(groups), scene_name))
    for idx, group in enumerate(groups):
        verts, normals, uvs = get_verts(group, config.swap_yz)
        tris = get_tris(group, config.swap_yz)
        group_name = group.name if group.name else "Group_{}".format(idx)
        config.log_line(
            "  Group: {}, name: {},  verts: {}, tris {}, normals: {}, uvs: {}".format(
                idx, group_name, len(verts), len(tris), len(normals), len(uvs)))
        mesh_data = bpy.data.meshes.new(group_name)
        mesh_data.from_pydata(verts, [], tris)
        # test normals
        if len(normals) > 0:
            mesh_data.create_normals_split()
            for l in mesh_data.loops:
                l.normal[:] = normals[l.vertex_index]

            mesh_data.normals_split_custom_set_from_vertices(normals)
            mesh_data.use_auto_smooth = True
        # end test

        if group.tex_index != 0:
            config.log_line("  Adding uvs for textured group: {}".format(idx))
            uvl = mesh_data.uv_layers.new()  # default name, init
            mesh_data.uv_layers.active = uvl
            for face in mesh_data.polygons:
                for i_vert, i_loop in zip(face.vertices, face.loop_indices):
                    uvl.data[i_loop].uv = (uvs[i_vert][0], 1-uvs[i_vert][1])

        mesh_data.validate()
        mesh_data.update()

        obj = bpy.data.objects.new(group_name, mesh_data)
        new_scene.collection.objects.link(obj)
        grp_mat_name = mat_dict[group.mat_index, group.tex_index]
        mat = bpy.data.materials[grp_mat_name]
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

    bpy.context.window.scene = new_scene

    # Clean up
    bpy.ops.object.select_all()
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
    bpy.ops.object.select_all(action='DESELECT')
