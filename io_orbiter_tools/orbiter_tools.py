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

        self.log_file = build_file_path(
            os.path.dirname(bpy.data.filepath), "BlenderTools", ".log")
        
        if self.verbose:
            try:
                self.log_file = open(self.log_file, 'w')
                print("Writing to log file: {}".format(self.log_file))
            except FileNotFoundError:
                print("Log file could not be opened.  Log file will not be built.")
                self.verbose = False

        if self.build_include_file:
            try:
                self.include_file = open(self.include_path_file, "w")
            except FileNotFoundError:
                print("Build file could not be opened. Include file will not be built.")
                self.build_include_file = False
                self.log_line(
                    "ERROR: Include file {} could not be opened!".format(self.include_path_file))
        
    def __enter__(self):
        return self
        
    def __exit__(self, type, value, traceback):
        if self.build_include_file:
            self.include_file.close()
    
        if self.verbose:
            self.log_file.close()
            
    def log_line(self, log_string):
        if self.verbose:
            print(log_string)
            self.log_file.write(log_string + "\n")
    
    def write_to_include(self, include_text):
        if self.build_include_file:
            self.include_file.write(include_text)
    
        
class Color:
    """
    A Color class that does no more then provide a consistent way to
    output color to the exported file.
    """
    
    r = 0
    g = 0
    b = 0
    a = 0
    
    def __str__(self):
        return "Color(({}, {}, {}, {}))".format(self.r, self.g, self.b, self.a)

    def mesh_format(self):
        return "{:.3f} {:.3f} {:.3f} {:.3f}".format(self.r, self.g, self.b, self.a)
    

class ExportVertex:
    """
    An Orbiter Export Vertex Class.
    
    Conver a mesh vertex to world coordinates appropriate for the mesh file 
    using the world_matrix to world coordinates.
    """
    x = 0.0
    y = 0.0
    z = 0.0
    nx = 0.0
    ny = 0.0
    nz = 0.0
    u = None
    v = None
    
    def __init__(self, vert, world_matrix):
        w_vertex = world_matrix * vert.co
#        w_normal = world_matrix * vert.normal
        w_normal = vert.normal
            
        # swap y - z
        self.x = w_vertex.x
        self.y = w_vertex.z
        self.z = w_vertex.y
        
        # swap y - z
        self.nx = w_normal.x
        self.ny = w_normal.z
        self.nz = w_normal.y

    def __str__(self):
        result = "{:.4f} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f}".format(
            self.x, self.y, self.z, self.nx, self.ny, self.nz)

        if (self.u is not None) and (self.v is not None):
            result = "{} {:.4f} {:.4f}".format(result, self.u, self.v)
            
        return result

    def nvertex_form(self):
        result = "{:.4f}f, {:.4f}f, {:.4f}f, {:.4f}f, {:.4f}f, {:.4f}f,".format(
            self.x, self.y, self.z, self.nx, self.ny, self.nz)

        if (self.u is not None) and (self.v is not None):
            result = "{} {:.4f}f, {:.4f}f".format(result, self.u, self.v)
        else:
            result = "{} 0.0f, 0.0f"
            
        return result
    
    def is_uv_assigned(self):
        """Return True if both u anv v are assigned for this vertex."""
        return (self.u != None) or (self.v != None)        


    def is_uv_equal(self, u, v):
        """Return True if both params u and v are equal this vertex's u an v members."""
        return (self.u == u) and (self.v == v)
        
    def vertex_form(self):
        """Return the vertex in _V form."""
        result = "_V({:.4f}, {:.4f}, {:.4f})".format(self.x, self.y, self.z)
        return result

        
class Face:
    """
    An Orbiter Export Face Class.
    
    Provides a wrapper for a triangle face.
    """
    v1 = 0
    v2 = 0
    v3 = 0

    def __init__(self, v_idx_1, v_idx_2, v_idx_3):
        self.v1 = v_idx_1
        self.v2 = v_idx_2
        self.v3 = v_idx_3

    def __str__(self):
        return "{} {} {}".format(self.v1, self.v2, self.v3)
    

def build_triangle_faces(face):
    """
    Return a list of Face objects for the given Blender face.
    
    The Blender face may be a quad, if that is the case then
    return an array of two Face objects, each representing
    a triangle face.
    """

    result = []
    
    face1 = Face(face.vertices[0], face.vertices[2], face.vertices[1])
    result.append(face1)
    
    if len(face.vertices) == 4:
        face2 = Face(face.vertices[0], face.vertices[3], face.vertices[2])
        result.append(face2)
        
    return result
        

class Material:
    """
    A Material class.
    
    Creates the appropriate material output text for a Blender material.
    """
    
    diffuse = Color()
    specular = Color()
    specular_power = 10
    ambient = Color()
    emissive = Color()
    name = None
    
    def __init__(self, material):
        self.diffuse.r = material.diffuse_color.r
        self.diffuse.g = material.diffuse_color.g
        self.diffuse.b = material.diffuse_color.b
        self.diffuse.a = material.alpha
        
        self.specular.r = material.specular_color.r
        self.specular.g = material.specular_color.g
        self.specular.b = material.specular_color.b
        self.specular.a = material.specular_alpha
        
        self.specular_power = material.specular_hardness
    
        self.emissive.r = material.orbiter_emit_color.r
        self.emissive.g = material.orbiter_emit_color.g
        self.emissive.b = material.orbiter_emit_color.b
        self.emissive.a = material.orbiter_emit_alpha
    
        self.ambient.r = material.orbiter_ambient_color.r
        self.ambient.g = material.orbiter_ambient_color.g
        self.ambient.b = material.orbiter_ambient_color.b
        self.ambient.a = material.orbiter_ambient_alpha
            
        self.name = material.name

    def __str__(self):
        return "Material(material)"
    
    def mesh_format(self):
        return "{}\n{}\n{} {}\n{}\n".format(self.diffuse.mesh_format(),
                                       self.ambient.mesh_format(),
                                       self.specular.mesh_format(), self.specular_power,
                                       self.emissive.mesh_format())

                                       
class MeshGroup:
    """
    An Orbiter mesh group.
    
    Takes a Blender mesh object and parses it to create the vertex and triangle
    lists needed for export.
    
    If the mesh has a texture the appropriate UV coordinates are extracted.  If
    a vertex has multiple UV coordinates then new vertices are added to account
    for the duplicate coordinates.
    
    Only texture 1 of material 1 will be used for texturing.
    """
    
    def __init__(self, config, mesh_object, scene):
        self.name = mesh_object.name.replace(' ', '_')
        self.uv_tex_name = None
        self.uv_tex_name_path = None
        self.material_name = None
        self.vertices_list = {}
        self.triangles_list = []
        self.matrix_world = mesh_object.matrix_world
        self.sort_order = mesh_object.orbiter_sort_order
        self.include_vertex_array = mesh_object.orbiter_include_vertex_array
        self.is_dynamic = False
        self.mesh_flag = mesh_object.orbiter_mesh_flag

        temp_mesh = mesh_object.to_mesh(scene, True, 'PREVIEW')

        #added to support 2.62 n-gons
        temp_mesh.update(calc_tessface=True)
        
        config.log_line("\nSTART mesh: {}".format(mesh_object.name))

        self.parse_mesh(config, temp_mesh)
            
        if len(temp_mesh.materials) > 0:
            self.material_name = temp_mesh.materials[0].name
            config.log_line("Material: {}".format(temp_mesh.materials[0].name))

        bpy.data.meshes.remove(temp_mesh)
        
        self.num_vertices = len(self.vertices_list)
        self.num_faces = len(self.triangles_list)

        config.log_line("END Mesh: {}".format(mesh_object.name))
        
    def parse_textured_mesh(self, config, mesh):
        the_image = mesh.materials[0].texture_slots[0].texture.image
        self.uv_tex_name_path = the_image.filepath

        self.is_dynamic = mesh.materials[0].texture_slots[0].texture.orbiter_is_dynamic
        self.uv_tex_name = bpy.path.basename(self.uv_tex_name_path)
    
        config.log_line("group is textured.")
        config.log_line("UV texture: {}".format(self.uv_tex_name))
        config.log_line("Texture file: {}".format(the_image.name))
        config.log_line("Texture dimensions: {} x {}".format(the_image.size[0], the_image.size[1]))
    
        if len(mesh.tessface_uv_textures) > 0:
            # textures[].data contains uv data by mesh face
            for idx_mesh_face, uv_itself in enumerate(mesh.tessface_uv_textures[0].data):
                face_uvs = uv_itself.uv1, uv_itself.uv2, uv_itself.uv3, uv_itself.uv4
                export_faces = build_triangle_faces(mesh.tessfaces[idx_mesh_face])
           
                # We now enumerate the vertices for the current face.  This will
                # give us the mesh index for the vertex as well as the face index
                # for the vertex.  If the vertex is shared between faces then it 
                # may have more then one UV coordinate assigned to it.  We use the
                # mesh vertex index to keep a dictionary of vertices so we can 
                # check if it has already been assigned a UV coordinate, if it has
                # we create a new vertex and add it to the list.
                for idx_face_vert, idx_mesh_vert in enumerate(mesh.tessfaces[idx_mesh_face].vertices):
                    face_vertex_u = face_uvs[idx_face_vert].x
                    face_vertex_v = 1 - face_uvs[idx_face_vert].y
                    exported_vertex = self.vertices_list[idx_mesh_vert]
                
                    if exported_vertex.is_uv_assigned():
                        # the exported vertex already has u v
                        # if they differ, then we need to create a new vertex
                        # and fix up the face triangles to point to the new vertex.
                
                        if not exported_vertex.is_uv_equal(face_vertex_u, face_vertex_v):
                            new_vertex = ExportVertex(mesh.vertices[idx_mesh_vert], self.matrix_world)
                            new_key = len(self.vertices_list.keys())
                            new_vertex.u = face_vertex_u
                            new_vertex.v = face_vertex_v
                            self.vertices_list[new_key] = new_vertex
                        
                            # We need to look through our export face list for this
                            # face and change any faces pointing to the old vertex
                            # to point to the new one we just added.
                            for export_face in export_faces:
                                if export_face.v1 == idx_mesh_vert:
                                    export_face.v1 = new_key
                                
                                if export_face.v2 == idx_mesh_vert:
                                    export_face.v2 = new_key
                                
                                if export_face.v3 == idx_mesh_vert:
                                    export_face.v3 = new_key
                    
                    else:
                        # The vertex does not have a u v assigned so we are good to
                        # assign this uv to the vertex.
                        exported_vertex.u = face_vertex_u
                        exported_vertex.v = face_vertex_v
    
                self.triangles_list.extend(export_faces)
        else:
            config.log_line("WARNING: Mesh is assigned a texture but has no UV map.")
       
    def parse_mesh(self, config, mesh):
        """
        Parse the mesh getting vertex and triangle face data.
        """

        config.log_line("parsing {} vertices.".format(len(mesh.vertices)))
        
        for vertex in mesh.vertices:
            self.vertices_list[vertex.index] = ExportVertex(vertex, self.matrix_world)

        # If the mesh has a texture, we must read the faces
        if (
                mesh.materials and 
                (mesh.materials[0].texture_slots[0] != None) and 
                (mesh.materials[0].texture_slots[0].texture.type == 'IMAGE')
           ):
            self.parse_textured_mesh(config, mesh)
        else:
            config.log_line("group is not textured.")
                
            for face in mesh.tessfaces:
                self.triangles_list.extend(build_triangle_faces(face))

                
def build_file_path(path, filename, extension):
    temppath = os.path.join(path, filename)
    fullpath = bpy.path.ensure_ext(temppath, extension)
    return bpy.path.abspath(fullpath)
   

def export_orbiter(config, scene):
    """
    Export scene to Orbiter mesh format.
    """
    
    # Make sure we have a namespace for this scene:
    if not scene.orbiter_scene_namespace:
        scene.orbiter_scene_namespace = scene.name

    config.log_line("Building scene: {}".format(scene.name))
    config.write_to_include("\n// Scene {}\n".format(scene.name))

    # Start the scene namespace:
    config.write_to_include("\nnamespace {} \n{{\n".format(scene.orbiter_scene_namespace))

    meshPath = build_file_path(config.mesh_path, scene.name, ".msh")
    
    config.log_line("Mesh out file: {}".format(meshPath))
    
    mesh_file = open(meshPath, "w")

    groups = []
    mesh_objects = [m for m in scene.objects if m.type == 'MESH']
    
    config.log_line("Found {} mesh object(s)".format(len(mesh_objects)))
    
    for mesh_object in mesh_objects:
        groups.append(MeshGroup(config, mesh_object, scene))

    # Get the material names from bpy.data.  Order here is important.  This is
    # the order they will appear in the file and they will be referenced by
    # index.
    material_names = [m.name for m in bpy.data.materials]
    
    # Get the texture names from the group list.  This is the order they will
    # appear in the file and be referenced by index.
    texture_names = [mesh_group.uv_tex_name for mesh_group in groups if not mesh_group.uv_tex_name == None]

    texture_names = list(set(texture_names))    # this removes dups.

    mesh_file.write("MSHX1\n")
    mesh_file.write("GROUPS {}\n".format(len(mesh_objects)))
    
    groups.sort(key=lambda x: x.sort_order, reverse=False)
    
    group_order = []
    dynamic_textures = []
    config.log_line("\nWriting out groups")

    for mesh_group in groups:
        group_order.append(mesh_group.name)
        
        if mesh_group.is_dynamic:
            dynamic_textures.append(mesh_group.uv_tex_name)
            
        mat_index = 0
        if mesh_group.material_name in material_names:
            mat_index = material_names.index(mesh_group.material_name) + 1
            
        tex_index = 0
        if mesh_group.uv_tex_name in texture_names:
            tex_index = texture_names.index(mesh_group.uv_tex_name) + 1
            
        config.log_line("Writing group: {}, Mat: {}, Tex: {}, Verts: {}, Faces: {}, Dynamic Texture: {}"
            .format(
                mesh_group.name, 
                mat_index, 
                tex_index, 
                mesh_group.num_vertices, 
                mesh_group.num_faces, 
                mesh_group.is_dynamic))
            
        mesh_file.write("LABEL {}\n".format(mesh_group.name))
        mesh_file.write("MATERIAL {}\n".format(mat_index))
        mesh_file.write("TEXTURE {}\n".format(tex_index))
        mesh_file.write("FLAG {}\n".format(mesh_group.mesh_flag))
        mesh_file.write("GEOM {} {}\n".format(mesh_group.num_vertices, mesh_group.num_faces))
        
        if mesh_group.include_vertex_array:
            config.write_to_include(
                "const NTVERTEX {}[{}] = {{\n".format(
                    config.name_pattern_verts.format(mesh_group.name), 
                    mesh_group.num_vertices))
            
        for v_key in sorted(mesh_group.vertices_list.keys()):
            mesh_file.write("{}\n".format(mesh_group.vertices_list[v_key]))
            if mesh_group.include_vertex_array:
                config.write_to_include(
                    "{{{}}}".format(
                        mesh_group.vertices_list[v_key].nvertex_form()))
                if v_key < (mesh_group.num_vertices - 1):
                    config.write_to_include(",\n")

        if mesh_group.include_vertex_array:
            config.write_to_include("};\n")

        for fl in mesh_group.triangles_list:
            mesh_file.write("{}\n".format(fl))
            
    mesh_file.write("MATERIALS {}\n".format(len(bpy.data.materials)))
    for m in bpy.data.materials:
        mesh_file.write("{}\n".format(m.name.replace(' ', '_')))
        
    for m in bpy.data.materials:
        mesh_file.write("MATERIAL {}\n".format(m.name.replace(' ', '_')))
        out = Material(m)
        mesh_file.write(out.mesh_format())

    mesh_file.write("TEXTURES {}\n".format(len(texture_names)))
    for idx, tex in enumerate(texture_names):
        mesh_file.write("{}".format(tex))
        if (tex in dynamic_textures):
            mesh_file.write(" D\n")
        else:
            mesh_file.write("\n")

        config.write_to_include(
            "const DWORD TXIDX_{} = {};\n".format(
                bpy.path.clean_name(tex), (idx + 1)))
        
    config.log_line("Done")

    mesh_file.close()
    
    config.log_line("Finished scene: {}".format(scene.name))

    config.write_to_include('#define {}_MESH_NAME "{}"\n\n'.format(scene.name, scene.name))
        
    for idx, group in enumerate(group_order):
        config.write_to_include('const UINT {} = {};\n'.format(config.name_pattern_id.format(group), idx))
        
    # Output selected objects
    objs = scene.objects
    vecfmt = '{{{:.4f}, {:.4f}, {:.4f}}};\n'
    
    for object in scene.objects:
        if object.orbiter_include_position:
            ov = object.location
            config.write_to_include('const VECTOR3 {} = '.format(config.name_pattern_location.format(object.name)))
            # swap y - z
            config.write_to_include(
                '{{{:.4f}, {:.4f}, {:.4f}}};\n'.format(ov.x, ov.z, ov.y))
    
        if object.orbiter_include_quad:
            q_mesh = object.to_mesh(scene, True, 'PREVIEW')
            if len(q_mesh.vertices) == 4:
                v_face = q_mesh.tessfaces[0]
                for vert_idx in v_face.vertices:
                    ex_vert = ExportVertex(q_mesh.vertices[vert_idx], object.matrix_world)
                    config.write_to_include(
                        'const VECTOR3 {}_QUAD_{} = '.format(object.name, vert_idx))
                    config.write_to_include(
                        '{{{:.4f}, {:.4f}, {:.4f}}};\n'.format(ex_vert.x, ex_vert.z, ex_vert.y))
            
            # Don't include quad objects in mesh.
            bpy.data.meshes.remove(q_mesh)    

    # Close scene namespace
    config.write_to_include("\n}\n")