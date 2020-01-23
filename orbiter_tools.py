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


import os
import bpy
import shutil


class OrbiterBuildSettings:
    """Container for the exporter settings."""

    def __init__(self,
                 verbose=False,
                 include_path_file=None,
                 build_include_file=True,
                 mesh_path_file=None,
                 name_pattern_location=None,
                 name_pattern_verts=None,
                 name_pattern_id=None,
                 debug=False):

        self.mesh_path = mesh_path_file
        self.verbose = verbose
        self.debug = debug
        self.build_include_file = build_include_file
        self.include_path_file = bpy.path.abspath(include_path_file)
        self.name_pattern_location = name_pattern_location
        self.name_pattern_verts = name_pattern_verts
        self.name_pattern_id = name_pattern_id
        self.log_file_path = build_file_path(
            os.path.dirname(bpy.data.filepath),
            "BlenderTools", ".log")
        if self.verbose:
            try:
                self.log_file = open(self.log_file_path, 'w')
                print("Log file output to: {}".format(self.log_file_path))
            except Exception as error:
                print("Log file could not be opened. Error: {}".format(error))
                self.verbose = False

        if self.build_include_file:
            try:
                self.include_file = open(self.include_path_file, "w")
            except Exception as error:
                print("Include could not be opened. Error: {}".format(error))
                self.build_include_file = False
                self.log_line(
                    "ERROR: Include file {} could not be opened!".format(
                        self.include_path_file))
                self.log_line("ERROR: {}".format(error))

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.build_include_file:
            self.include_file.close()

        if self.verbose:
            self.log_file.close()

    def log_line(self, log_string):
        if self.verbose:
            self.log_file.write(log_string + "\n")

    def log_debug(self, log_string):
        if self.debug:
            self.log_file.write(log_string + "\n")

    def write_to_include(self, include_text):
        if self.build_include_file:
            self.include_file.write(include_text)


class Vertex:
    """
    An Orbiter Export Vertex Class.

    Vertex data is maintained in its native state until output.  At that point matrix
    and axis swap will be applied if needed.
    """

    def __init__(self):
        self.x = None
        self.y = None
        self.z = None
        self.nx = None
        self.ny = None
        self.nz = None
        self.u = None
        self.v = None

    @classmethod
    def from_BlenderVertex(cls, blvert, world_matrix):
        nv = cls()
        tv = world_matrix @ blvert.co  #  Transform
        nv.x = tv.x
        nv.y = tv.z  # swap y, z
        nv.z = tv.y
        nv.world_matrix = world_matrix
        return nv

    @classmethod
    def from_Vertex(cls, Vertex, normal=None, uv=None):
        nv = cls()
        nv.x = Vertex.x  #  World transform and swap has already been done
        nv.y = Vertex.y
        nv.z = Vertex.z

        if normal:
            nv.nx = normal.x
            nv.ny = normal.z  # Swap y,z for the normal
            nv.nz = normal.y
        
        if uv:
            nv.u = uv[0]
            nv.v = 1 - uv[1]

        return nv

    def __str__(self):
        """
        String representation of Vertex.
        """
        result = "V:[{:8.4f} {:8.4f} {:8.4f}]".format(self.x, self.y, self.z)

        if self.nx or self.ny or self.nz:
            result = "{} N:[{:7.4f} {:7.4f} {:7.4f}]".format(
                result, self.nx, self.ny, self.nz)

        if self.u or self.v:
            result = "{} U:[{:6.4f} {:6.4f}]".format(result, self.u, self.v)

        return result

    def mesh_form(self, world_matrix):
        result = "{:.4f} {:.4f} {:.4f}".format(self.x, self.y, self.z)

        if self.nx or self.ny or self.nz:
            result = "{} {:.4f} {:.4f} {:.4f}".format(
            result, self.nx, self.ny, self.nz)

        if self.u or self.v:
            result = "{} {:.4f} {:.4f}".format(result, self.u, self.v)

        return result

    def set_uv(self, uv):
        """
        Set the u,v value of the vertex if not set.
        Return True if the uv value matches the uv value passed in.
        """
        if uv is None:
            return True

        if (self.u is None) or (self.v is None):
            self.u = uv[0]
            self.v = 1 - uv[1]

        return self.u == uv[0] and self.v == 1 - uv[1]

    def set_normal(self, normal):
        """
        Sets the vertex normal if not set.
        Return True if the vertex.normal, and the passed in normal are now equal.
        False indicates the vertex already has a normal different from the one passed in.
        """
        if normal is None:
            return True

        if ((self.nx is None) or (self.ny is None) or (self.nz is None)):
            self.nx = normal.x
            self.ny = normal.z  # Swap y,z
            self.nz = normal.y

        return self.nx == normal.x and self.ny == normal.z and self.nz == normal.y

    def nvertex_form(self):
        tmp = "{:.4f}f, {:.4f}f, {:.4f}f, {:.4f}f, {:.4f}f, {:.4f}f,"
        result = tmp.format(self.x, self.y, self.z, self.nx, self.ny, self.nz)

        if self.u or self.v:
            result = "{} {:.4f}f, {:.4f}f".format(result, self.u, self.v)
        else:
            result = "{} 0.0f, 0.0f".format(result)

        return result

    def vertex_form(self):
        """Return the vertex in _V form."""
        result = "_V({:.4f}, {:.4f}, {:.4f})".format(self.x, self.y, self.z)
        return result


class Triangle:
    """
    An Orbiter Export Triangle.

    Provides a wrapper for a triangle definition.
    """

    def __init__(self, v1, v2, v3):
        self.v1 = v1  # Note: orientation reversed to match Orbiter
        self.v2 = v3
        self.v3 = v2

    @classmethod
    def from_dict(cls, tri_list):
        return cls(tri_list[0], tri_list[1], tri_list[2])

    @classmethod
    def from_trimesh(cls, tri_mesh):
        return cls(
            tri_mesh.vertices[0],
            tri_mesh.vertices[1],
            tri_mesh.vertices[2])

    def __str__(self):
        return "{} {} {}".format(self.v1, self.v2, self.v3)


class MeshGroup:
    """
    An Orbiter mesh group.

    Takes a Blender mesh object and parses it to create the vertex and triangle
    lists needed for export.

    Vertex data is stored in the mesh .vertices collection.  Each vertex
    contains the position (x,y,z) data as well as the normal data for that
    vertex.  The vertex data is in object local coordinates and must be
    transformed into world coordinates for use in Orbiter.  The triangle data
    (the three vertices that make up one tri-polygon) is stored in the
    loop_triangles collection.  Each member of that collection contains an
    array of three ints, which are indexes into the .vertices array.

    If the mesh has a texture, then we also must get the uv data for each
    triangle.  A mesh can have multiple uv maps, but for Orbiter we will only
    use the first map located in mesh.uv_layers[0].  The uv layer has a .data
    collection where each entry contains a uv pair.  The index into that
    .data collection is also in the mesh.loop_triangles collection  Each
    triangle also has a .loops collection of 3 integers, which is an index
    into the .data collection mentioned.

    In Blender a vertex can have multiple UV mappings, but in Orbiter each
    vertex must have its own UV mapping.  This means as we are collecting
    the UV data for a triangle, we must see if the vertex that triangle
    references already has UV data assigned.  If it does, we must duplicate
    that vertex and assign the UV to that new vertex.  The two vertices will
    have the same location, but will have different UV assignments.
    """

    def __init__(self, config, mesh_object, scene):
        self.name = mesh_object.name.replace(' ', '_')
        self.uv_tex_name = None
        self.uv_tex_name_path = None
        self.mat_name = None
        self.vertices_dict = {}
        self.triangles_list = []
        self.matrix_world = mesh_object.matrix_world
        self.sort_order = mesh_object.orbiter_sort_order
        self.include_vertex_array = mesh_object.orbiter_include_vertex_array
        self.is_dynamic_texture = False
        self.mesh_flag = mesh_object.orbiter_mesh_flag

        # 2.81  In order to get the mesh with modifiers applied, you need
        #       to get the dependency graph and use that to get an
        #       evaluated instance of the mesh.
        deps = bpy.context.evaluated_depsgraph_get()
        object_eval = mesh_object.evaluated_get(depsgraph=deps)
        temp_mesh = object_eval.to_mesh()
        temp_mesh.validate()  # To fix a possibly invalid mesh.  This seems to help.
        temp_mesh.calc_loop_triangles()  #  Orbiter needs triangles, so turn all polygons to tris.
        
        #  Calc split normals here, even if not using auto smooth, this will put
        #  the normals in the mesh.loops collection where we can read them.
        temp_mesh.calc_normals_split()

        self.vertices_dict = {v.index:Vertex.from_BlenderVertex(v, self.matrix_world) for v in temp_mesh.vertices}
        # for vertex in temp_mesh.vertices:
        #     self.vertices_dict[vertex.index] = Vertex.from_BlenderVertex(vertex, self.matrix_world)

        start_vert_count = len(temp_mesh.vertices)
        config.log_line("Parsing mesh: {}, Vertices: {}".format(temp_mesh.name, start_vert_count))

        has_uv = False
        if (temp_mesh.uv_layers and 
                temp_mesh.materials and 
                temp_mesh.materials[0].use_nodes and 
                'Image Texture' in temp_mesh.materials[0].node_tree.nodes):
            self.uv_tex_name_path = temp_mesh.materials[0].node_tree.nodes['Image Texture'].image.filepath
            self.is_dynamic_texture = temp_mesh.materials[0].orbiter_is_dynamic
            self.uv_tex_name = bpy.path.basename(path=self.uv_tex_name_path)
            has_uv = True
            config.log_line("Mesh has texture node: {}".format(self.uv_tex_name))

        #  The vertex alone is not enough to know the normal used by the current triangle face
        #  corner, for that we also need the polygon it belongs to.  The following lookup is
        #  a map from (polygon, vertex) to a mesh.loops entry where the normal for this triangle
        #  corner is stored.
        loop_lookup = {}
        for poly in temp_mesh.polygons:
            for idx, vert in enumerate(poly.vertices):
                loop_lookup[(poly.index, vert)] = poly.loop_indices[idx]

        config.log_line("  Polys: {}  Tris: {}".format(len(temp_mesh.polygons), len(temp_mesh.loop_triangles)))

        #  Now walk through the tri faces.  Each face has the polygon it belongs to
        #  and each corner has the vertex.  Use this to look up the correct vertex normal.
        export_faces = []
        for tri_face in temp_mesh.loop_triangles:
            #  Each face has a vertices collection that contains the index to the vertices
            #  these make up this triangle.  We need to collect these to define the triangle
            #  face.  For each corner we look up that corner's normal in the mesh.loops
            #  collection.  If the vertex our corner points to already has a normal assigned,
            #  and it does not match our normal, we create a new vertex for the new normal.
            #  When we do this, we need to update the face vertex index to point to the
            #  new vertex.
            export_tri_face = {}
            poly_index = tri_face.polygon_index

            for corner_idx, corner_vert in enumerate(tri_face.vertices):
                export_tri_face[corner_idx] = corner_vert
                
                uv = temp_mesh.uv_layers[0].data[tri_face.loops[corner_idx]].uv if has_uv else None

                #  Deal with the normal
                norm = temp_mesh.loops[loop_lookup[(poly_index, corner_vert)]].normal
                work_vert = self.vertices_dict[corner_vert]

                need_norm = not work_vert.set_normal(norm)
                need_uv = not work_vert.set_uv(uv)

                config.log_debug("{} Pidx:Tri[{}, {}][N {}, V {}]".format(
                    work_vert, poly_index, corner_vert, need_norm, need_uv))
                if need_norm or need_uv:
                    #  duplicate vert.
                    new_vert = Vertex.from_Vertex(work_vert, norm, uv)
                    new_key = len(self.vertices_dict.keys())
                    self.vertices_dict[new_key] = new_vert
                    export_tri_face[corner_idx] = new_key
                    config.log_line(" * {}".format(new_vert))

            export_faces.append(Triangle.from_dict(export_tri_face))

        self.triangles_list.extend(export_faces)
        config.log_line("Finished parsing mesh: {}, Verts: {} to {}".format(
            temp_mesh.name, start_vert_count, len(self.vertices_dict)))

        if len(temp_mesh.materials) > 0:
            self.mat_name = temp_mesh.materials[0].name
        else:
            self.mat_name = None

        object_eval.to_mesh_clear()

        self.num_vertices = len(self.vertices_dict)
        self.num_faces = len(self.triangles_list)


def get_log_folder():
    """
    Determines the log folder, which is the current .blend folder if the
    current file is saved, otherwise it is the os TEMP folder.
    """
    return bpy.path.abspath("//") if bpy.data.is_saved else os.environ['TEMP']


def build_file_path(path, filename, extension):
    temppath = os.path.join(path, filename)
    fullpath = bpy.path.ensure_ext(temppath, extension)
    return bpy.path.abspath(fullpath)


def output_material(mesh_file, material):
    mesh_file.write(
        "{:.3f} {:.3f} {:.3f} {:.3f}\n".format(
            material.diffuse_color[0],
            material.diffuse_color[1],
            material.diffuse_color[2],
            material.diffuse_color[3]))

    mesh_file.write(
        "{:.3f} {:.3f} {:.3f} {:.3f}\n".format(
            material.orbiter_ambient_color[0],
            material.orbiter_ambient_color[1],
            material.orbiter_ambient_color[2],
            material.orbiter_ambient_color[3]))

    mesh_file.write(
        "{:.3f} {:.3f} {:.3f} {:.3f} {:.3f}\n".format(
            material.orbiter_specular_color[0],
            material.orbiter_specular_color[1],
            material.orbiter_specular_color[2],
            material.orbiter_specular_color[3],
            material.orbiter_specular_power))

    mesh_file.write(
        "{:.3f} {:.3f} {:.3f} {:.3f}\n".format(
            material.orbiter_emit_color[0],
            material.orbiter_emit_color[1],
            material.orbiter_emit_color[2],
            material.orbiter_emit_color[3]))


def build_include(config, scene, groups, texNames):
    """
    Build include file.
    """

    if not config.build_include_file:
        return

    grp_names = [grp.name for grp in groups]

    config.write_to_include("\n// Scene {}\n".format(scene.name))
    config.write_to_include(
        "\n  namespace {} \n  {{\n".format(scene.orbiter_scene_namespace))

    for mesh_group in groups:
        if mesh_group.include_vertex_array:
            config.write_to_include(
                "    const NTVERTEX {}[{}] = {{\n".format(
                    config.name_pattern_verts.format(mesh_group.name), mesh_group.num_vertices))

        for v_key in sorted(mesh_group.vertices_dict.keys()):
            if mesh_group.include_vertex_array:
                config.write_to_include("    {{{}}}".format(mesh_group.vertices_dict[v_key].nvertex_form()))
                if v_key < (mesh_group.num_vertices - 1):
                    config.write_to_include(",\n")

        if mesh_group.include_vertex_array:
            config.write_to_include("    };\n")

    for idx, tex in enumerate(texNames):
        config.write_to_include(
            "    const DWORD TXIDX_{} = {};\n".format(
                bpy.path.clean_name(tex), (idx + 1)))

    config.write_to_include(
        '    #define {}_MESH_NAME "{}"\n\n'.format(scene.name, scene.name))
    for idx, group in enumerate(grp_names):
        config.write_to_include(
            '    const UINT {} = {};\n'.format(
                config.name_pattern_id.format(group), idx))

    for object in scene.objects:
        if object.orbiter_include_position:
            ov = object.location
            config.write_to_include(
                '    const VECTOR3 {} = '.format(
                    config.name_pattern_location.format(object.name)))
            # swap y - z
            config.write_to_include(
                '    {{{:.4f}, {:.4f}, {:.4f}}};\n'.format(ov.x, ov.z, ov.y))

        if object.orbiter_include_quad:
            q_mesh = object.to_mesh(preserve_all_data_layers=True)
            if len(q_mesh.vertices) == 4:
                q_mesh.calc_loop_triangles()
                for vert_idx in q_mesh.vertices:
                    ex_vert = Vertex.from_BlenderVertex(q_mesh.vertices[vert_idx], object.matrix_world)
                    config.write_to_include(
                        '    const VECTOR3 {}_QUAD_{} = '.format(object.name, vert_idx))
                    config.write_to_include(
                        '    {{{:.4f}, {:.4f}, {:.4f}}};\n'.format(
                            ex_vert.x, ex_vert.z, ex_vert.y))

            object.to_mesh_clear()

    config.write_to_include("\n  }\n")    # close namespace


def export_orbiter(config, scene):
    """
    Export scene to Orbiter mesh format.
    """

    mesh_path = build_file_path(config.mesh_path, scene.name, ".msh")
    config.log_line("Start scene: {} : {}".format(scene.name, mesh_path))

    if not scene.orbiter_scene_namespace:
        scene.orbiter_scene_namespace = scene.name

    meshes = [m for m in scene.objects if m.type == 'MESH']
    groups = [MeshGroup(config=config, mesh_object=m, scene=scene) for m in meshes]
    groups.sort(key=lambda x: x.sort_order, reverse=False)
    mat_names = [m.name for m in bpy.data.materials]  # Order is important.
    tex_names = [group.uv_tex_name for group in groups if group.uv_tex_name is not None]
    tex_names = list(set(tex_names))    # this removes dups.
    dyn_texs = [grp.uv_tex_name for grp in groups if grp.is_dynamic_texture]

    with open(mesh_path, "w") as mesh_file:
        mesh_file.write("MSHX1\n")
        mesh_file.write("GROUPS {}\n".format(len(meshes)))

        for mesh_group in groups:
            if mesh_group.mat_name in mat_names:
                matIdx = mat_names.index(mesh_group.mat_name) + 1
            else:
                matIdx = 0

            if mesh_group.uv_tex_name in tex_names:
                texIdx = tex_names.index(mesh_group.uv_tex_name) + 1
            else:
                texIdx = 0

            config.log_line(
                "Writing group: {}, Mat: {}, Tex: {}, Verts: {}, Faces: "
                "{}, Dynamic Texture: {}"
                .format(
                    mesh_group.name,
                    matIdx,
                    texIdx,
                    mesh_group.num_vertices,
                    mesh_group.num_faces,
                    mesh_group.is_dynamic_texture))

            mesh_file.write("LABEL {}\n".format(mesh_group.name))
            mesh_file.write("MATERIAL {}\n".format(matIdx))
            mesh_file.write("TEXTURE {}\n".format(texIdx))
            mesh_file.write("FLAG {}\n".format(mesh_group.mesh_flag))
            mesh_file.write("GEOM {} {}\n".format(mesh_group.num_vertices, mesh_group.num_faces))

            for v_key in sorted(mesh_group.vertices_dict.keys()):
                mesh_file.write("{}\n".format(mesh_group.vertices_dict[v_key].mesh_form(mesh_group.matrix_world)))

            for fl in mesh_group.triangles_list:
                mesh_file.write("{}\n".format(fl))

        mesh_file.write("MATERIALS {}\n".format(len(bpy.data.materials)))
        for mName in mat_names:
            mesh_file.write("{}\n".format(mName.replace(' ', '_')))

        for m in bpy.data.materials:
            mesh_file.write("MATERIAL {}\n".format(m.name.replace(' ', '_')))
            output_material(mesh_file, m)

        mesh_file.write("TEXTURES {}\n".format(len(tex_names)))
        for tex in tex_names:
            mesh_file.write("{}".format(tex))
            if (tex in dyn_texs):
                mesh_file.write(" D\n")
            else:
                mesh_file.write("\n")

    config.log_line("Finished scene: {}".format(scene.name))
    build_include(config, scene, groups, tex_names)
