# Blender Orbiter Mesh Tools
_Version 2.0.2_

Orbiter Mesh Tools is a [Blender](https://www.blender.org/) add-on for generating [Orbiter](http://orbit.medphys.ucl.ac.uk/index.html) mesh files.  It will also, optionally, generate a C++ source file for the mesh being created.

## Compatibility:
Blender 2.81.


## Getting Started
1.	Copy the io_orbiter_tools folder into the *scripts/addons* folder of your Blender installation.
2.	In Blender open *User Preferences* and go to the *Add Ons* tab.
3.	Find *Orbiter Mesh Tools* and check the box to enable the add on.
4.  Read through the Simple Walkthrough.pdf located in the Resources folder for an exmaple of how to create and test a simple add-on for Orbiter.

## General Usage
This add-on will create an Orbiter mesh file for each scene in the blend file that has the _orbiter mesh file_ option set in the Scene properties panel.  See Scene Panel below.  A single C++ file, if enabled, will be created for all scenes.

In Blender, _z_ is treated as the _up_ and _y_ is the _forward_ axis.  When the mesh is created the _y_ and _z_ values are swapped to match what Orbiter expects.  This was done to allow a more intuitive use of the Blender view keys ([End]-front back, [Home]-top bottom, [PgDn]-left right) when modelling _z is horizontal_ type models in Blender, since Blender treats the X-Y plane as the _floor_.  The result is a standard _left-handed_ orientation for the Orbiter mesh.

The add-on will use the first material defined for the object.  It will not convert any image file into a compatible .DDS format.  Blender supports .DDS textures, so the supported work flow is to place the texture files directly into Orbiter\Textures and reference them from there.  The output mesh file will then correctly reference that texture file.


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

***Build Mesh:*** Initiates the process to build the mesh and include files as configured.  A ‘Blender Alert’ will display when the process is complete.

### Scene Panel
***Orbiter Mesh File:*** If checked, this scene will build a mesh file.

***Scene Namespace:*** The namespace for values from this scene that will be written to the include file.  By default this will be the name of the scene but can be changed to whatever is convenient.

### Object Panel
***Name:*** The name of the currently selected object.

***OrbiterSortOrder:*** Controls the sort order for the object in the mesh file.  Default is 50.  Higher numbers will move that object later in the mesh file.  This is used to control render order of transparent objects.  An object with transparency should be given a higher value then other objects it may appear in front of.

***OrbiterMeshFlag:*** Sets the Orbiter mesh flag value.  See Orbiter SDK for values.

***Output Location:*** Output object location as a const VECTOR3 value.

***Output Vertex Array:*** Output the object vertices as an array of NTVERTEX values.

***Output quad:*** If the object is a plane it will output VECTOR3 values for each corner.  These can be used to setup a ‘hit’ rectangle.

### Material Panel
***Diffuse Color:*** Orbiter diffuse color.
***Ambient Color:*** Orbiter ambient color.
***Specular Color:*** Orbiter specular color.
***Specular Power:*** Orbiter specular power.
***Emit Color:*** Orbiter emmisive color.
***Is Dynamic:*** If checked, the texture for this material will be treated by Orbiter as dynamic.

### Orbiter Mesh Import
Import an Orbiter mesh file by selecting 'File - Import - Orbiter Mesh Import' inside Blender.

A new Blender scene will be created with the name of the mesh file.  Axis values are treated as explaned above, with _Y_ and _Z_ coordinates swapped.

A node based material will be created for each unique Material + Texture combination found in the mesh file.

Normals are imported, but this is still a work in progress.  Blender 2.81 offers better normals support, but this appears to be very poorly documented in Blender, and good examples are sparse.