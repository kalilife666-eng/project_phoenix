#!/usr/bin/env python3
"""Build a simple 2.5D Blender scene:
- skull_2 acts as reaper/thrower
- molotov flies into prison
- skull_1, skull_3, skull_4 emerge from prison smoke area

Run:
blender --python tools/blender_prison_molotov.py -- \
  --assets-dir /home/s/legal_analyzer/assets/reaper_elements/isolated \
  --save /home/s/legal_analyzer/assets/reaper_elements/isolated/prison_molotov_scene.blend
"""

from __future__ import annotations

import argparse
import math
import os
import sys

import bpy
from mathutils import Vector


ASSETS = {
    "prison": "prison_isolated.png",
    "reaper": "skull_2_isolated.png",
    "skull_a": "skull_1_isolated.png",
    "skull_b": "skull_3_isolated.png",
    "skull_c": "skull_4_isolated.png",
}


def _args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets-dir", required=True)
    parser.add_argument("--save", default="")
    parser.add_argument("--render", default="")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--start-frame", type=int, default=1)
    parser.add_argument("--end-frame", type=int, default=140)
    return parser.parse_args(argv)


def _safe_set_material_transparency(mat: bpy.types.Material) -> None:
    # Blender versions differ in the property naming.
    if hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"
    if hasattr(mat, "surface_render_method"):
        try:
            mat.surface_render_method = "BLENDED"
        except Exception:
            pass


def _set_socket_if_exists(node: bpy.types.Node, socket_name: str, value: float) -> None:
    sock = node.inputs.get(socket_name)
    if sock is not None:
        sock.default_value = value


def _clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Purge orphan data so repeated runs are clean.
    for _ in range(3):
        try:
            bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        except Exception:
            break


def _look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _make_image_material(name: str, image_path: str) -> tuple[bpy.types.Material, bpy.types.Node]:
    image = bpy.data.images.load(image_path, check_existing=True)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.location = (-420, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (-120, 0)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (180, 0)

    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if "Alpha" in tex.outputs and "Alpha" in bsdf.inputs:
        links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])

    # Keep the cutout art mostly flat/lit consistently.
    _set_socket_if_exists(bsdf, "Roughness", 1.0)
    _set_socket_if_exists(bsdf, "Specular", 0.0)
    _set_socket_if_exists(bsdf, "Specular IOR Level", 0.0)

    _safe_set_material_transparency(mat)
    return mat, bsdf


def _add_image_plane(
    name: str,
    image_path: str,
    height: float,
    location: tuple[float, float, float],
) -> tuple[bpy.types.Object, bpy.types.Material, bpy.types.Node]:
    image = bpy.data.images.load(image_path, check_existing=True)
    w, h = image.size
    aspect = w / max(h, 1)
    width = height * aspect

    bpy.ops.mesh.primitive_plane_add(
        size=1.0,
        location=location,
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (width / 2.0, height / 2.0, 1.0)

    mat, bsdf = _make_image_material(f"{name}_MAT", image_path)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj, mat, bsdf


def _add_emission_ball(
    name: str,
    location: tuple[float, float, float],
    radius: float,
    color: tuple[float, float, float, float],
    strength: float,
) -> tuple[bpy.types.Object, bpy.types.Node]:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    obj = bpy.context.active_object
    obj.name = name
    mat = bpy.data.materials.new(f"{name}_MAT")
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    emission = nodes.new("ShaderNodeEmission")
    emission.location = (-100, 0)
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (160, 0)
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = strength
    links.new(emission.outputs["Emission"], out.inputs["Surface"])

    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj, emission


def _iter_action_fcurves(action: bpy.types.Action, action_slot=None):
    if action is None:
        return
    # Blender <= 4.x
    if hasattr(action, "fcurves"):
        for fcurve in action.fcurves:
            yield fcurve
        return
    # Blender 5.x layered actions
    if hasattr(action, "layers"):
        for layer in action.layers:
            strips = getattr(layer, "strips", [])
            for strip in strips:
                channelbags = getattr(strip, "channelbags", [])
                for channelbag in channelbags:
                    # If a specific action slot is provided, prefer its bag.
                    if action_slot is not None and hasattr(channelbag, "slot") and channelbag.slot != action_slot:
                        continue
                    fcurves = getattr(channelbag, "fcurves", [])
                    for fcurve in fcurves:
                        yield fcurve


def _set_linear(obj: bpy.types.ID) -> None:
    ad = getattr(obj, "animation_data", None)
    action = getattr(ad, "action", None) if ad else None
    if action is None:
        return
    slot = getattr(ad, "action_slot", None)
    for fcurve in _iter_action_fcurves(action, action_slot=slot):
        for point in fcurve.keyframe_points:
            point.interpolation = "LINEAR"


def _key_visibility(obj: bpy.types.Object, frame: int, visible: bool) -> None:
    obj.hide_viewport = not visible
    obj.hide_render = not visible
    obj.keyframe_insert(data_path="hide_viewport", frame=frame)
    obj.keyframe_insert(data_path="hide_render", frame=frame)


def build_scene(args: argparse.Namespace) -> None:
    assets_dir = os.path.abspath(args.assets_dir)
    for key, filename in ASSETS.items():
        full = os.path.join(assets_dir, filename)
        if not os.path.exists(full):
            raise FileNotFoundError(f"Missing asset for {key}: {full}")
        ASSETS[key] = full

    _clear_scene()

    scene = bpy.context.scene
    scene.frame_start = args.start_frame
    scene.frame_end = args.end_frame
    scene.render.fps = args.fps
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100

    # Prefer Eevee for fast iteration.
    engine_options = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    if "BLENDER_EEVEE_NEXT" in engine_options:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    elif "BLENDER_EEVEE" in engine_options:
        scene.render.engine = "BLENDER_EEVEE"
    else:
        scene.render.engine = "CYCLES"

    # Camera.
    bpy.ops.object.camera_add(location=(0.0, -18.0, 4.8))
    cam = bpy.context.active_object
    cam.name = "Camera_Main"
    cam.data.lens = 50
    cam.data.clip_end = 1000
    _look_at(cam, Vector((0.0, 6.0, 3.2)))
    scene.camera = cam

    # Light.
    bpy.ops.object.light_add(type="SUN", location=(-6.0, -8.0, 15.0))
    sun = bpy.context.active_object
    sun.data.energy = 2.4
    _look_at(sun, Vector((0.0, 5.0, 2.5)))

    # Scene cards.
    prison, _, _ = _add_image_plane(
        "Prison",
        ASSETS["prison"],
        height=9.8,
        location=(1.2, 8.2, 3.1),
    )
    reaper, _, _ = _add_image_plane(
        "Reaper_Skull2",
        ASSETS["reaper"],
        height=4.3,
        location=(-6.2, 2.2, 2.4),
    )

    skull_a, mat_a, bsdf_a = _add_image_plane(
        "Skull_A",
        ASSETS["skull_a"],
        height=2.0,
        location=(0.2, 7.6, 2.0),
    )
    skull_b, mat_b, bsdf_b = _add_image_plane(
        "Skull_B",
        ASSETS["skull_b"],
        height=2.1,
        location=(1.7, 7.7, 1.8),
    )
    skull_c, mat_c, bsdf_c = _add_image_plane(
        "Skull_C",
        ASSETS["skull_c"],
        height=2.0,
        location=(3.2, 7.8, 2.0),
    )

    # Reaper throw motion.
    reaper.location = (-6.4, 2.1, 2.35)
    reaper.rotation_euler = (math.radians(90.0), 0.0, math.radians(6.0))
    reaper.keyframe_insert(data_path="location", frame=1)
    reaper.keyframe_insert(data_path="rotation_euler", frame=1)

    reaper.location = (-6.0, 2.3, 2.55)
    reaper.rotation_euler = (math.radians(90.0), 0.0, math.radians(-14.0))
    reaper.keyframe_insert(data_path="location", frame=34)
    reaper.keyframe_insert(data_path="rotation_euler", frame=34)

    reaper.location = (-6.2, 2.15, 2.45)
    reaper.rotation_euler = (math.radians(90.0), 0.0, math.radians(4.0))
    reaper.keyframe_insert(data_path="location", frame=52)
    reaper.keyframe_insert(data_path="rotation_euler", frame=52)
    _set_linear(reaper)

    # Molotov object and path.
    molotov, molotov_em = _add_emission_ball(
        "Molotov",
        location=(-4.7, 2.4, 3.45),
        radius=0.16,
        color=(1.0, 0.55, 0.08, 1.0),
        strength=18.0,
    )
    _key_visibility(molotov, 1, False)
    _key_visibility(molotov, 30, True)

    molotov.location = (-4.7, 2.4, 3.45)
    molotov.keyframe_insert(data_path="location", frame=30)
    molotov.location = (-1.2, 5.2, 5.7)
    molotov.keyframe_insert(data_path="location", frame=40)
    molotov.location = (0.9, 7.75, 3.35)
    molotov.keyframe_insert(data_path="location", frame=50)
    _key_visibility(molotov, 53, False)
    _set_linear(molotov)

    # Impact flash.
    blast, blast_em = _add_emission_ball(
        "ImpactFlash",
        location=(0.9, 7.75, 3.35),
        radius=0.08,
        color=(1.0, 0.33, 0.06, 1.0),
        strength=0.0,
    )
    blast.scale = (0.01, 0.01, 0.01)
    blast.keyframe_insert(data_path="scale", frame=48)
    blast_em.inputs["Strength"].default_value = 0.0
    blast_em.inputs["Strength"].keyframe_insert(data_path="default_value", frame=48)

    blast.scale = (2.1, 2.1, 2.1)
    blast.keyframe_insert(data_path="scale", frame=53)
    blast_em.inputs["Strength"].default_value = 85.0
    blast_em.inputs["Strength"].keyframe_insert(data_path="default_value", frame=53)

    blast.scale = (0.45, 0.45, 0.45)
    blast.keyframe_insert(data_path="scale", frame=66)
    blast_em.inputs["Strength"].default_value = 18.0
    blast_em.inputs["Strength"].keyframe_insert(data_path="default_value", frame=66)

    blast.scale = (0.01, 0.01, 0.01)
    blast.keyframe_insert(data_path="scale", frame=80)
    blast_em.inputs["Strength"].default_value = 0.0
    blast_em.inputs["Strength"].keyframe_insert(data_path="default_value", frame=80)

    # Skull emergence animation.
    # Start hidden/low; rise and fade in from prison region after impact.
    skull_tracks = [
        (skull_a, bsdf_a, 54, (0.1, 7.7, 1.35), (0.4, 8.0, 3.4)),
        (skull_b, bsdf_b, 60, (1.6, 7.8, 1.2), (2.0, 8.1, 3.6)),
        (skull_c, bsdf_c, 67, (3.1, 7.9, 1.1), (3.35, 8.2, 3.35)),
    ]

    for obj, bsdf, start_f, start_loc, end_loc in skull_tracks:
        obj.location = start_loc
        obj.scale = (0.55, 0.55, 0.55)
        obj.keyframe_insert(data_path="location", frame=start_f)
        obj.keyframe_insert(data_path="scale", frame=start_f)
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 0.0
            bsdf.inputs["Alpha"].keyframe_insert(data_path="default_value", frame=start_f)

        mid_f = start_f + 8
        obj.location = (
            (start_loc[0] + end_loc[0]) * 0.5,
            (start_loc[1] + end_loc[1]) * 0.5,
            (start_loc[2] + end_loc[2]) * 0.5 + 0.45,
        )
        obj.scale = (0.9, 0.9, 0.9)
        obj.keyframe_insert(data_path="location", frame=mid_f)
        obj.keyframe_insert(data_path="scale", frame=mid_f)
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 0.7
            bsdf.inputs["Alpha"].keyframe_insert(data_path="default_value", frame=mid_f)

        end_f = start_f + 18
        obj.location = end_loc
        obj.scale = (1.05, 1.05, 1.05)
        obj.keyframe_insert(data_path="location", frame=end_f)
        obj.keyframe_insert(data_path="scale", frame=end_f)
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = 1.0
            bsdf.inputs["Alpha"].keyframe_insert(data_path="default_value", frame=end_f)
        _set_linear(obj)

    # Optional outputs.
    if args.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save))

    if args.render:
        render_out = os.path.abspath(args.render)
        scene.render.filepath = render_out
        scene.render.image_settings.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    build_scene(_args())
