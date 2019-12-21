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

#   2.0.1       - Blender 2.81 support

bl_info = {
    "name": "Orbiter Mesh Tools",
    "author": "Blake Christensen",
    "version": (2, 0, 1),
    "blender": (2, 81, 0),
    "location": "",
    "description": "Tools for building Orbiter mesh files.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

if "bpy" in locals():
    import importlib
    if "orbiter_tools" in locals():
        importlib.reload(orbiter_tools)
else:
    import bpy
    import time
    import traceback
    from . import orbiter_tools


class OrbiterBuildMesh(bpy.types.Operator):
    """Build Orbiter Mesh Operator."""
    
    bl_idname = "orbiter.buildmesh"
    bl_label = "Orbiter Build Mesh"
    
    @classmethod
    def poll(cls, context):
        return context.mode is not 'EDIT_MESH'
        
    def execute(self, context):
        print("Orbiter Build Mesh called.")
        home_scene = bpy.data.scenes[0]
        if not home_scene.orbiter_outer_namespace:
            home_scene.orbiter_outer_namespace = "bl"

        with orbiter_tools.OrbiterBuildSettings(
            verbose=home_scene.orbiter_verbose,
            include_path_file=home_scene.orbiter_include_path,
            build_include_file=home_scene.orbiter_build_include_file,
            mesh_path_file=home_scene.orbiter_mesh_path,
            name_pattern_location=home_scene.orbiter_location_name_pattern,
            name_pattern_verts=home_scene.orbiter_vertex_array_name_pattern,
            name_pattern_id=home_scene.orbiter_id_name_pattern) as config:

            config.log_line("Orbiter Tools Build Log - Date: {}".format(time.asctime()))
            config.log_line("Versions  Blender: {}  Blender Tools: {}".format(bpy.app.version_string, bl_info["version"]))
            config.log_line(" ")
            config.log_line("Mesh Path: " + config.mesh_path)
            config.log_line("Build Include File: {}".format(config.build_include_file))
            if (config.build_include_file):
                config.log_line("Include Path File: " + config.include_path_file)
                config.log_line("Id name pattern: " + config.name_pattern_id)
                config.log_line("Location name pattern: " + config.name_pattern_location)
                config.log_line("Verts name pattern: " + config.name_pattern_verts)
            
            config.log_line(" ")
            config.write_to_include("// Auto generated code file.  Blender: {}  Blender Tools: {}\n".format(
                bpy.app.version_string, bl_info["version"]))
            config.write_to_include("// Date: {}\n\n\n".format(time.asctime()))
            config.write_to_include('#include "orbitersdk.h"\n\n')
            config.write_to_include('#ifndef __{}_H\n'.format(home_scene.name))
            config.write_to_include('#define __{}_H\n'.format(home_scene.name))
            config.write_to_include('\nnamespace {} \n{{\n'.format(home_scene.orbiter_outer_namespace))
            try:
                for scene in bpy.data.scenes:
                    orbiter_tools.export_orbiter(config, scene)
            except Exception:
                config.log_line(traceback.format_exc())
                raise

            config.write_to_include('\n}\n')        # close outer namespace
            config.write_to_include('#endif\n')     # close include guards
            self.report({'INFO'}, "Mesh build done: {}".format(config.mesh_path))
            
        return {"FINISHED"}

        
class OBJECT_PT_OrbiterMaterialContext(bpy.types.Panel):
    bl_label = "Orbiter Materials Panel"
    bl_idname = "OBJECT_PT_OrbiterMaterialContext"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return (context.material or context.object)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        mat = context.material
        ob = context.object
        space = context.space_data
        row = layout.row()
        if ob:
            row.template_ID(ob, "active_material", new="material.new")
        elif mat:
            row.template_ID(space, "pin_id")

        if mat:
            layout.prop(mat, "type", expand=True)

                    
class OBJECT_PT_OrbiterMaterial(bpy.types.Panel):
    bl_label = "Orbiter Materials Panel"
    bl_idname = "OBJECT_PT_OrbiterMaterial"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        mat = context.material
        row = layout.row()

        # diffuse
        row.prop(mat, "diffuse_color")
        row = layout.row()
        row.prop(mat, "alpha")
        
        # specular
        layout.separator()
        row = layout.row()
        row.prop(mat, "specular_color")
        row = layout.row()
        row.prop(mat, "specular_hardness")
        row = layout.row()
        row.prop(mat, "specular_alpha")

        # ambient
        layout.separator()
        row = layout.row()
        row.prop(mat, "orbiter_ambient_color")
        row = layout.row()
        row.prop(mat, "orbiter_ambient_alpha")

        # emit
        layout.separator()
        row = layout.row()
        row.prop(mat, "orbiter_emit_color")
        row = layout.row()
        row.prop(mat, "orbiter_emit_alpha")
        
        row = layout.row()
        row.prop(mat, "orbiter_is_dynamic")

        
class OBJECT_PT_OrbiterObject(bpy.types.Panel):
    bl_label = "Orbiter Object Panel"
    bl_idname = "OBJECT_PT_OrbiterObject"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        obj = context.object
        row = layout.row()
        row.label(text="Active object is: " + obj.name)
        row = layout.row()
        row.prop(obj, "name")
        row = layout.row()
        row.prop(obj, "orbiter_sort_order")
        row = layout.row()
        row.prop(obj, "orbiter_mesh_flag")
        row = layout.row()
        row.prop(obj, "orbiter_include_position")
        row = layout.row()
        row.prop(obj, "orbiter_include_vertex_array")
        if obj.type == 'MESH':
            row = layout.row()
            row.prop(obj, "orbiter_include_quad", text="Output quad.")
        

class OBJECT_PT_OrbiterOutput(bpy.types.Panel):
    bl_label = "Orbiter Output Panel"
    bl_idname = "OBJECT_PT_OrbiterOutput"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "output"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        props_scene = bpy.data.scenes[0]
        layout.separator()
        row = layout.row()
        row.prop(props_scene, "orbiter_mesh_path", text="Mesh Path")
        row = layout.row()
        row.prop(props_scene, "orbiter_build_include_file", text="Build Include File")
        if props_scene.orbiter_build_include_file:
            row = layout.row()
            box = row.box()
            box.prop(props_scene, "orbiter_include_path", text="Include Path")
            box.prop(props_scene, "orbiter_outer_namespace", text="Outer Namespace")
            box.prop(props_scene, "orbiter_id_name_pattern", text="Id Name")
            box.prop(props_scene, "orbiter_location_name_pattern", text="Location Name")
            box.prop(props_scene, "orbiter_vertex_array_name_pattern", text="Vertex Name")

        layout.separator()
        row = layout.row()
        row.prop(props_scene, "orbiter_verbose")
        row = layout.row()
        row.operator("orbiter.buildmesh", text="Build Mesh")


class OBJECT_PT_OrbiterScene(bpy.types.Panel):
    bl_label = "Orbiter Scene Panel"
    bl_idname = "OBJECT_PT_OrbiterScene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        scene = context.scene
        row = layout.row()
        row.prop(scene, "orbiter_create_mesh_file")
        row = layout.row()
        row.prop(scene, "orbiter_scene_namespace")
        
classes = {
    OrbiterBuildMesh,
    OBJECT_PT_OrbiterMaterialContext,
    OBJECT_PT_OrbiterMaterial,
    OBJECT_PT_OrbiterObject,
    OBJECT_PT_OrbiterOutput,
    OBJECT_PT_OrbiterScene
}

def register():
    print("Register Orbiter tools.")
    for cls in classes:
        bpy.utils.register_class(cls)

    # Object properties:
    bpy.types.Object.orbiter_sort_order = bpy.props.IntProperty(
        name="Sort Order", 
        description="Determines the order of the object in the mesh file.",
        default=50)
    bpy.types.Object.orbiter_mesh_flag = bpy.props.IntProperty(
        name="Mesh Flag",
        description="Mesh Flag.  See Orbiter SDK for values.",
        default=0)
    bpy.types.Object.orbiter_include_position = bpy.props.BoolProperty(
        name="Include Position",
        description="Include object position as a const VECTOR3 value.",
        default=False)
    bpy.types.Object.orbiter_include_quad = bpy.props.BoolProperty(
        name="Include Quad",
        description="Include plane as quadrilateral.",
        default=False)
    bpy.types.Object.orbiter_include_vertex_array = bpy.props.BoolProperty(
        name="Include Vertex Array",
        description="Include object vertices as an array of NTVERTEX values.",
        default=False)
    
    # Scene properties:
    bpy.types.Scene.orbiter_create_mesh_file = bpy.props.BoolProperty(
        name="Output Mesh File",
        description="If True, creates a mesh file for this scene.",
        default=True)
    bpy.types.Scene.orbiter_scene_namespace = bpy.props.StringProperty(
        name="Scene Namespace",
        description="Namespace for this scene in the include file")

    # These props are only referenced from scene[0] this
    # seems to be the best place to put general settings.
    bpy.types.Scene.orbiter_include_path = bpy.props.StringProperty(
        subtype='FILE_PATH',
        description="Directory where the include file will be written to.")
    bpy.types.Scene.orbiter_mesh_path = bpy.props.StringProperty(
        subtype='DIR_PATH',
        description="Directory where the mesh files will be written to.")
    bpy.types.Scene.orbiter_build_include_file = bpy.props.BoolProperty(
        name="Build Include File",
        description="Build C++ Include File.",
        default=True)
    bpy.types.Scene.orbiter_verbose = bpy.props.BoolProperty(
        name="Verbose", 
        description="When enabled, outputs a detailed log file in same folder as the .blend file.", 
        default=False)
    bpy.types.Scene.orbiter_outer_namespace = bpy.props.StringProperty(
        name="Outer Namespace",
        description="Outer namespace in the include file.")
    bpy.types.Scene.orbiter_location_name_pattern = bpy.props.StringProperty(
        name="Location Name",
        description="Name pattern for object location.  Must contain {} which will be replaced with object name.",
        default="{}Location")
    bpy.types.Scene.orbiter_vertex_array_name_pattern = bpy.props.StringProperty(
        name="Vertex Array Name",
        description="Name pattern for Vetex Arrays. Must contain {} which will be replaced with the object name.",
        default="{}Verts")
    bpy.types.Scene.orbiter_id_name_pattern = bpy.props.StringProperty(
        name="Id Name",
        description="String appended to the object name when creating the const for the object's Id.",
        default="{}Id")
    
    # Material properties:
    bpy.types.Material.orbiter_ambient_color = bpy.props.FloatVectorProperty(
        name="Ambient color",
        description="Ambient color.",
        subtype='COLOR',
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=(1.0,1.0,1.0))
    bpy.types.Material.orbiter_ambient_alpha = bpy.props.FloatProperty(
        name="Ambient alpha",
        description="Ambient alpha",
        min=0.0,
        max=1.0,
        default=1.0)
    bpy.types.Material.orbiter_emit_color = bpy.props.FloatVectorProperty(
        name="Emit color",
        description="Emit color.",
        subtype='COLOR',
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=(0.0,0.0,0.0))
    bpy.types.Material.orbiter_emit_alpha = bpy.props.FloatProperty(
        name="Emit alpha",
        description="Emit alpha",
        min=0.0,
        max=1.0,
        default=1.0)
    bpy.types.Material.orbiter_is_dynamic = bpy.props.BoolProperty(
        name="Is Dynamic", 
        description="Indicates to Orbiter to treat the texture as dynamic.", 
        default=False)
        
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    print("Unregister Orbiter tools.")
    del bpy.types.Object.orbiter_sort_order
    del bpy.types.Object.orbiter_include_position
    del bpy.types.Scene.orbiter_create_mesh_file
    del bpy.types.Scene.orbiter_scene_namespace
    del bpy.types.Scene.orbiter_build_include_file
    del bpy.types.Scene.orbiter_verbose
    del bpy.types.Scene.orbiter_include_path
    del bpy.types.Scene.orbiter_mesh_path
    del bpy.types.Scene.orbiter_outer_namespace
    del bpy.types.Scene.orbiter_location_name_pattern
    del bpy.types.Scene.orbiter_vertex_array_name_pattern
    del bpy.types.Scene.orbiter_id_name_pattern
    del bpy.types.Material.orbiter_ambient_color
    del bpy.types.Material.orbiter_ambient_alpha
    del bpy.types.Material.orbiter_emit_color
    del bpy.types.Material.orbiter_emit_alpha
    del bpy.types.Object.orbiter_include_quad
    del bpy.types.Object.orbiter_include_vertex_array
    del bpy.types.Object.orbiter_mesh_flag
    del bpy.types.Material.orbiter_is_dynamic
    

if __name__ == "__main__":
    register()