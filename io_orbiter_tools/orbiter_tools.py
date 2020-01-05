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
                 name_pattern_id=None):

        self.mesh_path = mesh_path_file
        self.verbose = verbose
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

    def write_to_include(self, include_text):
        if self.build_include_file:
            self.include_file.write(include_text)


class Vertex:
    """
    An Orbiter Export Vertex Class.

    Convert a mesh vertex to world coordinates appropriate for the mesh
    file using the world_matrix to world coordinates.
    """

    def __init__(self, mesh_vertex, world_matrix):
        w_vertex = world_matrix @ mesh_vertex.co  # Transform to world coords
        w_normal = mesh_vertex.normal
        self.x = w_vertex.x  # Note: z : y coords swapped
        self.y = w_vertex.z
        self.z = w_vertex.y
        self.nx = w_normal.x
        self.ny = w_normal.z
        self.nz = w_normal.y
        self.u = None
        self.v = None

    def __str__(self):
        result = "{:.4f} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f}".format(
            self.x, self.y, self.z, self.nx, self.ny, self.nz)

        if (self.u is not None) and (self.v is not None):
            result = "{} {:.4f} {:.4f}".format(result, self.u, self.v)

        return result

    def nvertex_form(self):
        tmp = "{:.4f}f, {:.4f}f, {:.4f}f, {:.4f}f, {:.4f}f, {:.4f}f,"
        result = tmp.format(self.x, self.y, self.z, self.nx, self.ny, self.nz)

        if (self.u is not None) and (self.v is not None):
            result = "{} {:.4f}f, {:.4f}f".format(result, self.u, self.v)
        else:
            result = "{} 0.0f, 0.0f"

        return result

    def is_uv_assigned(self):
        """Return True if both u anv v are assigned for this vertex."""
        return (self.u is not None) or (self.v is not None)

    def is_uv_equal(self, u, v):
        """
        Return True if both params u and v are equal
        this vertex's u an v members.
        """
        return (self.u == u) and (self.v == v)

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
        temp_mesh.calc_loop_triangles()
        self.parse_mesh(config=config, mesh=temp_mesh)
        if len(temp_mesh.materials) > 0:
            self.mat_name = temp_mesh.materials[0].name
        else:
            self.mat_name = None
        object_eval.to_mesh_clear()

        self.num_vertices = len(self.vertices_dict)
        self.num_faces = len(self.triangles_list)

    def parse_textured_mesh(self, config, mesh):
        the_image = mesh.materials[0].node_tree.nodes['Image Texture'].image
        self.uv_tex_name_path = the_image.filepath
        self.is_dynamic_texture = mesh.materials[0].orbiter_is_dynamic
        self.uv_tex_name = bpy.path.basename(path=self.uv_tex_name_path)

        export_faces = []
        for tri in mesh.loop_triangles:
            export_tri_face = {}
            for loop_idx in range(0, 3):  # loop through the corners
                uv = mesh.uv_layers[0].data[tri.loops[loop_idx]].uv
                vert_u = uv[0]
                vert_v = 1-uv[1]
                vert_idx = tri.vertices[loop_idx]
                export_tri_face[loop_idx] = vert_idx
                exp_vertex = self.vertices_dict[vert_idx]

                if (exp_vertex.is_uv_assigned() and
                        not exp_vertex.is_uv_equal(vert_u, vert_v)):
                    new_vertex = Vertex(
                        mesh_vertex=mesh.vertices[vert_idx],
                        world_matrix=self.matrix_world)
                    new_key = len(self.vertices_dict.keys())
                    new_vertex.u = vert_u
                    new_vertex.v = vert_v
                    self.vertices_dict[new_key] = new_vertex
                    export_tri_face[loop_idx] = new_key
                else:
                    exp_vertex.u = vert_u
                    exp_vertex.v = vert_v

            export_faces.append(Triangle.from_dict(export_tri_face))

        self.triangles_list.extend(export_faces)

    def parse_mesh(self, config, mesh):
        """
        Parse the mesh getting vertex and triangle face data.
        """

        for vertex in mesh.vertices:
            self.vertices_dict[vertex.index] = Vertex(
                vertex, self.matrix_world)

        if (mesh.uv_layers and mesh.materials and
                'Image Texture' in mesh.materials[0].node_tree.nodes):
            self.parse_textured_mesh(config, mesh)
        else:
            config.log_line("group is not textured.")
            for tri in mesh.loop_triangles:
                self.triangles_list.append(Triangle.from_trimesh(tri))


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
                    config.name_pattern_verts.format(mesh_group.name),
                    mesh_group.num_vertices))

        for v_key in sorted(mesh_group.vertices_dict.keys()):
            if mesh_group.include_vertex_array:
                config.write_to_include(
                    "    {{{}}}".format(
                        mesh_group.vertices_dict[v_key].nvertex_form()))
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
                    ex_vert = Vertex(
                                q_mesh.vertices[vert_idx],
                                object.matrix_world)
                    config.write_to_include(
                        '    const VECTOR3 {}_QUAD_{} = '.format(
                            object.name, vert_idx))
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
    groups = [MeshGroup(
                config=config,
                mesh_object=m,
                scene=scene) for m in meshes]
    groups.sort(key=lambda x: x.sort_order, reverse=False)
    mat_names = [m.name for m in bpy.data.materials]  # Order is important.
    tex_names = [
        group.uv_tex_name for group in groups if group.uv_tex_name is not None]
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
            mesh_file.write(
                "GEOM {} {}\n".format(
                    mesh_group.num_vertices, mesh_group.num_faces))

            for v_key in sorted(mesh_group.vertices_dict.keys()):
                mesh_file.write("{}\n".format(mesh_group.vertices_dict[v_key]))

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
