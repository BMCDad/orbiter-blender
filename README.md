# Blender Orbiter Mesh Tools

Orbiter Mesh Tools is a [Blender](https://www.blender.org/) add-on for generating [Orbiter](http://orbit.medphys.ucl.ac.uk/index.html) mesh files.  It will also, optionally, generate a C++ source file for the mesh being created.

## Compatibility:
Blender 4.2.x - 4.3 may also work, but is untested.
For Blender 4.0 download the latest 2.1.x version of the tools from Releases.


## Getting Started
1.	Under _Releases_ above, click on the _Latest_ release.  This will open the Release page.
2.  Under _Assets_ click on _orbiter-blender-2.zip_.  This will download a zip file to your PC.
3.	In Blender open *User Preferences* and go to the *Add Ons* tab.
4.	Select _Install_ at the top of the Preferences window and find the zip file you just download, and click the _Install Add-on_ button.
5.  Click the check box next to the add on name _Import-Export: Orbiter Mesh Tools_ to enable the add-on.
6.  Read the included _Orbiter Tools Tutorial.pdf_ document for a tutorial on how to create a simple textured vessel for Orbiter using this plugin.


## General Usage
This add-on will create an Orbiter mesh file for each scene in the blend file that has the _orbiter mesh file_ option set in the Scene properties panel.  See Scene Panel below.  A single C++ file, if enabled, will be created for all scenes.

In Blender, _z_ is treated as the _up_ and _y_ is the _forward_ axis.  When the mesh is created the _y_ and _z_ values are swapped to match what Orbiter expects.  This was done to allow a more intuitive use of the Blender view keys ([End]-front back, [Home]-top bottom, [PgDn]-left right) when modelling _z is horizontal_ type models in Blender, since Blender treats the X-Y plane as the _floor_.  The result is a standard _left-handed_ orientation for the Orbiter mesh.  This behavior can be overridden by un-selecting the Swap YZ Axis option when building the mesh file.

The add-on will use the first material defined for the object.  It will not convert any image file into a compatible .DDS format.  Blender supports .DDS textures, so the supported work flow is to place the texture files directly into Orbiter\Textures and reference them from there.  The output mesh file will then correctly reference that texture file.

## Exporting and Import of Normals
With version 2.0.3 the export and import process will use the 'split' normals for the mesh.  This has several benefits:
- The shading you see in Blender will be closer to what you see in Orbiter.  This means if you shade a mesh as flat, it will show as flat in Orbiter and if you shade smooth, it will show smooth.
- Blender 2.81 has Auto Smooth, which is similar to the split edge modifier, but easier to use.  This feature works with split normals.
- Split normals can be edited independent of the faces it is associated with.  This allows you to do things like more natural rounded corners without introducing a lot of new geometry.

Fewer modifiers and geometry loops means cleaner geometry to model with.

If you want to mimic the use of vertex normals, you can do this by telling Blender to shade an object as 'smooth'.  This basically tells the split normals to behave as vertex normals.

## Blender Property Panels
### Output Panel
***Mesh Path:*** Output folder where the generated mesh file will be written to.

***Build Include File:*** If checked, a C++ include file will be generated that defines mesh group IDs as well as other useful values (see Object Property Panel).

***Include Path:*** The folder and filename for the generated include file.  One include file is created for the blend file.  Scene (mesh) specific values can be identified with a mesh namespace (see Scene Property Panel).

***Outer Namespace:*** This is the top-level namespace for the include file.  Scene namespaces will be nested within this namespace.

***Id Name:*** Name pattern for object IDs in the generated source file.  {} is replaced with the name of the object.

***Location Name:*** Name of the object location in the generated source file.  {} is replaced with the name of the object.

***Vertex Name:*** Name of the object vertex object in the generated source file.  {} is replaced with the name of the object.

***Verbose:*** If checked a detailed log file will be generated that can be used for debugging when a mesh is not being generated as expected.  The name of the file is ‘BlenderTools.log’ and it will be written to the same folder that holds the blend file.

***Export Selected:***  If checked, only selected objects from the active scene will be included in the mesh file.  However, if checked and *no* objects are selected, all objects will be included in the mesh file.

***Swap YZ Axis:***  If checked (default) the Y and Z axis values are swapped, as explained above.

***Sort Mode:***  Select the sort mode for the exported groups.  *Sort Order* (default) sort the groups based on the Sort Order property in the Blender object.  *Group Name ASC* sort the groups by group name in ascending order.  *Group Name DESC* sort the groups by name in descending order.

***Exclude Hidden From Render:***  If selected, only objects marked to be visible in a render (the camera icon in the outliner) will be exported to the mesh file.  This is a universal setting and will impact all scenes.  If an include file is generated, any location and size data requested for that object will still be included in the output.  This allows you to create objects that can be used for sizing and position in C++ code, but not actually exist in the mesh.  Similar to an 'Empty', but probably more useful.

***Parse Material Name:***  If selected, the material name used in the resulting mesh will be the Blender mesh name up to the first '_' in the name.  When importing a mesh the material name is a combination of the material, texture and scene.  This option, if true, allows for the resulting mesh file to use the same material name that was used in the imported mesh.

***Build Mesh:*** Initiates the process to build the mesh and include files as configured.  A ‘Blender Alert’ will display when the process is complete.

### Scene Panel
***Orbiter Mesh File:*** If checked, this scene will build a mesh file.

***Scene Namespace:*** The namespace for values from this scene that will be written to the include file.  By default this will be the name of the scene but can be changed to whatever is convenient.

***Is Scene 2D Panel:*** If checked, this scene will adjust the axis values so that the mesh file for this scene can be used as a 2D panel.  

### Object Panel
***Name:*** The name of the currently selected object.

***Sort Order:*** Controls the sort order for the object in the mesh file.  Default is 50.  Higher numbers will move that object later in the mesh file.  This is used to control render order of transparent objects.  An object with transparency should be given a higher value then other objects it may appear in front of.

***Mesh Flag:*** Sets the Orbiter mesh flag value.  See Orbiter SDK for values.

***Include Position:*** Output object location as a const VECTOR3 value.

***Include Vertex Array:*** Output the object vertices as an array of NTVERTEX values.

***Output quad:*** If the object is a plane it will output VECTOR3 values for each corner.  These can be used to setup a ‘hit’ rectangle.

***Include Width and Height:*** Output a width and height variable for the object in the include file.  Width is the size of the X axis, and height is the Y axis.  Useful for 2d panel development.

***Include RECT:*** Output a RECT structure for this object.  Assumes the object is a simple plane with four vertices.

***Output

### Material Panel
***Diffuse Color:*** Orbiter diffuse color.
***Ambient Color:*** Orbiter ambient color.
***Specular Color:*** Orbiter specular color.
***Specular Power:*** Orbiter specular power.
***Emit Color:*** Orbiter emmisive color.
***Is Dynamic:*** If checked, the texture for this material will be treated by Orbiter as dynamic.

### Orbiter Mesh Import
Import an Orbiter mesh file by selecting 'File - Import - Orbiter Mesh Import' inside Blender.

A new Blender scene will be created with the name of the mesh file.  By default, axis values are treated as explaned above, with _Y_ and _Z_ coordinates swapped.  Disable this swap by un-checking the Swap YZ Axis option on the import screen.

A node based material will be created for each unique Material + Texture combination found in the mesh file.  The name of the material will be the imported material name plus the texture name plus the scene name.  This naming can be disabled by setting the import option 'Concatenate material name' to false (default true).  Disable this will cause the resulting material names to have a numeric suffix if used with different textures.  The import process will look for textures in the Orbiter\Textures\ folder, so if you have renamed your Orbiter folder the import may fail.  

Normals are imported as 'split', not 'vertex' normals.  Split normals are more versatile and easier to edit.
