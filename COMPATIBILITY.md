# Blender Version Compatibility

## Version Support Matrix

| Addon Version | Blender Version | Status |
|---|---|---|
| v2.3.x | 4.5 LTS | Current |
| v2.2.x | 4.2 LTS | Maintained (no new features) |
| v2.1.x | 4.0 – 4.1 | End of life |
| v2.0.x | 2.81 – 3.x | End of life |

---

## Blender APIs Used

This table lists every non-trivial Blender API call and where it appears. Check these when testing a new Blender version.

| API | File | Purpose |
|---|---|---|
| `bpy.context.evaluated_depsgraph_get()` | [orbiter_tools.py](orbiter_tools.py) | Get depsgraph with modifiers applied |
| `object.evaluated_get(depsgraph=...)` | [orbiter_tools.py](orbiter_tools.py) | Evaluate object with modifiers |
| `object.to_mesh()` / `object.to_mesh_clear()` | [orbiter_tools.py](orbiter_tools.py) | Temporary evaluated mesh |
| `mesh.validate()` | [orbiter_tools.py](orbiter_tools.py) | Ensure mesh integrity |
| `mesh.transform(matrix)` | [orbiter_tools.py](orbiter_tools.py) | Apply world transform |
| `mesh.calc_loop_triangles()` | [orbiter_tools.py](orbiter_tools.py) | Tessellate polygons |
| `mesh.loop_triangles` | [orbiter_tools.py](orbiter_tools.py) | Iterate tessellated faces |
| `mesh.uv_layers[0].data[loop_idx].uv` | [orbiter_tools.py](orbiter_tools.py) | Read UV coordinates |
| `material.node_tree.nodes.get('Principled BSDF')` | [orbiter_tools.py](orbiter_tools.py) | Read base color / texture |
| `mesh.from_pydata(verts, [], tris)` | [import_tools.py](import_tools.py) | Build mesh from Python data |
| `bpy.path.clean_name(name)` | [orbiter_tools.py](orbiter_tools.py) | Sanitize names for C++ output |
| `bpy.props.StringProperty(subtype='DIR_PATH', options={'PATH_SUPPORTS_BLEND_RELATIVE'})` | [__init__.py](__init__.py) | Blend-relative path support (4.5+) |

---

## Manual Smoke Test Procedure

Run these steps after installing the addon on a new Blender version.

### Install
1. Zip the repo folder (or use the release zip).
2. In Blender: *Edit → Preferences → Add-ons → Install* — select the zip.
3. Enable *Import-Export: Orbiter Mesh Tools*.
4. Open Blender's **System Console** (*Window → Toggle System Console* on Windows). Confirm no Python errors or deprecation warnings appear on enable.

### Export test
1. Open `Resources/MyShip.blend`.
2. Go to the **Output** properties panel → **Orbiter Output Panel**.
3. Set **Mesh Path** to a temp folder using both an absolute path and a blend-relative path (`//output/`) — confirm no warnings in the system console for either.
4. Click **Build Mesh**. Confirm `.msh` files appear in the output folder and the info bar shows "Mesh build done".

### Import test
1. *File → Import → Orbiter Mesh Import (.msh)* — select one of the exported `.msh` files.
2. Confirm mesh objects appear in the scene with correct geometry and materials.

### Unregister test
1. *Edit → Preferences → Add-ons* — disable the addon.
2. Confirm no errors in the system console on disable.
3. Re-enable. Confirm it registers cleanly again.

---

## When a New Blender LTS is Released

1. Check the Blender release notes Python API section for breaking changes.
2. Cross-reference the APIs listed above against any deprecation notices.
3. Run the smoke test procedure above on the new version.
4. Update `blender_manifest.toml` (`blender_version_min`) and `bl_info["blender"]` in `__init__.py`.
5. Bump the addon version and add a changelog entry in `__init__.py`.
6. Update the version support matrix in this file.
