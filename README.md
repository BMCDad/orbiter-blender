# Blender Orbiter Mesh Tools
Orbiter Mesh Tools is a [Blender](https://www.blender.org/) add-on for generating [Orbiter](http://orbit.medphys.ucl.ac.uk/index.html) mesh files.  It will also, optionally, generate a C++ source file for the mesh being created.

## Compatibility:
Blender 2.79


## Getting Started
1.	Copy the io_orbiter_tools folder into the *scripts/addons* folder of your Blender installation.
2.	In Blender open *User Preferences* and go to the *Add Ons* tab.
3.	Find *Orbiter Mesh Tools* and check the box to enable the add on.

- See _Resources\Simple Walkthrough.pdf_ for a quick tutorial on how to use the plugin to create and test an Orbiter mesh file.

## General Usage
The add-on will create an Orbiter mesh file for each scene in the blend file that has the _orbiter mesh file_ option set in the Scene properties panel.  See Scene Panel below.  A single C++ file, if enabled, will be created for all scenes.

The add-on swaps the orientation ‘y’ and ‘z’ axis values when generating the mesh file.  This was done to allow a more intuitive use of the Blender view keys ([End]-front back, [Home]-top bottom, [PgDn]-left right) when modelling ‘z is horizontal’ type models in Blender, since Blender treats the X-Y plane as the ‘floor’.  The result is a standard ‘left-handed’ orientation for the Orbiter mesh.

The add-on will use the first material and texture defined for the object.  It will not convert any image file into a compatible .DDS format.  Blender supports .DDS textures, so the supported work flow is to place the texture files directly into Orbiter\Textures and reference them from there.  The output mesh file will then correctly reference that text file.

## Blender Property Panels
### Render Panel
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
***Orbiter Mesh File:*** If checked this scene will build a mesh file.

***Scene Namespace:*** The namespace for values from this scene that will be written to the include file.  By default this will be the name of the scene but can be changed to whatever is convenient.

### Object Panel
***Name:*** The name of the currently selected object.

***OrbiterSortOrder:*** Controls the sort order for the object in the mesh file.  Default is 50.  Higher numbers will move that object later in the mesh file.  This is used to control render order of transparent objects.  An object with transparency should be given a higher value then other objects it may appear in front of.

***OrbiterMeshFlag:*** Sets the Orbiter mesh flag value.  See Orbiter SDK for values.

***Output Location:*** The location of the object will be output in the include file as a const VECTOR3 value.

***Output Vertex Array:*** Will output the object vertices as an array of NTVERTEX values.

***Output quad:*** If the object is a plane it will output VECTOR3 values for each corner.  These can be used to setup a ‘hit’ rectangle.

