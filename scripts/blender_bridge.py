"""Blender-only importer for verified world matrices and image assets, not a solver."""
import argparse
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Matrix


def keyed_world(obj, matrices):
    obj.rotation_mode = 'QUATERNION'
    previous = None
    for frame, rows in sorted(matrices.items(), key=lambda kv: int(kv[0])):
        if len(rows)!=4 or any(len(row)!=4 for row in rows):
            raise ValueError('World matrices must be 4 x 4')
        if not all(math.isfinite(float(v)) for row in rows for v in row):
            raise ValueError('Nonfinite matrix')
        if any(abs(float(v)-expected)>1e-6 for v,expected in zip(rows[3],[0,0,0,1])):
            raise ValueError('Matrix must be affine')
        matrix = Matrix(rows)
        rotation = matrix.to_3x3()
        if abs(rotation.determinant()-1)>1e-3:
            raise ValueError('Expected rigid, unit-scale world pose')
        gram = rotation.transposed() @ rotation
        if any(abs(gram[i][j]-(1 if i==j else 0))>1e-3 for i in range(3) for j in range(3)):
            raise ValueError('Pose axes must be orthonormal')
        location, quaternion, scale = matrix.decompose()
        if previous is not None and quaternion.dot(previous)<0:
            quaternion.negate()
        obj.location, obj.rotation_quaternion, obj.scale = location, quaternion, scale
        previous = quaternion.copy()
        for prop in ('location','rotation_quaternion','scale'):
            obj.keyframe_insert(data_path=prop, frame=int(frame))
    # Dense tracked samples should not acquire Bezier overshoot between poses.
    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        if hasattr(action, 'fcurves'):
            for curve in action.fcurves:
                for point in curve.keyframe_points: point.interpolation = 'LINEAR'


def image_plane(name, path, size, frames=1):
    image = bpy.data.images.load(str(path), check_existing=True)
    if frames > 1:
        image.source = 'SEQUENCE'
    material = bpy.data.materials.new(name+'_material')
    material.use_nodes = True
    if hasattr(material,'surface_render_method'): material.surface_render_method = 'BLENDED'
    nodes = material.node_tree.nodes
    nodes.clear()
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.image_user.frame_duration = frames
    tex.image_user.frame_start = 1
    tex.image_user.use_auto_refresh = True
    emission = nodes.new('ShaderNodeEmission')
    transparent = nodes.new('ShaderNodeBsdfTransparent')
    mix = nodes.new('ShaderNodeMixShader')
    output = nodes.new('ShaderNodeOutputMaterial')
    links = material.node_tree.links
    links.new(tex.outputs['Color'],emission.inputs['Color'])
    links.new(tex.outputs['Alpha'],mix.inputs[0])
    links.new(transparent.outputs[0],mix.inputs[1])
    links.new(emission.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0],size[1],1)
    obj.data.materials.append(material)
    return obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--render', type=Path, help='Optional frame-1 smoke PNG')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    data = json.loads(args.project.read_text(encoding='utf-8'))
    root = args.project.resolve().parent
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = int(data['width'])
    scene.render.resolution_y = int(data['height'])
    scene.render.resolution_percentage = 100
    fps = float(data['fps'])
    scene.render.fps = round(fps)
    scene.render.fps_base = round(fps)/fps
    scene.frame_end = int(data['frames'])
    scene.view_settings.view_transform = 'Standard'
    camera_data = bpy.data.cameras.new('SolvedCamera')
    camera_data.lens = float(data['camera']['lens_mm'])
    camera_data.sensor_width = float(data['camera']['sensor_width_mm'])
    camera_data.sensor_fit = 'HORIZONTAL'
    camera_data.dof.use_dof = False
    camera = bpy.data.objects.new('SolvedCamera',camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    keyed_world(camera,data['camera']['world_matrices'])
    phone = bpy.data.objects.new('TrackedPhone',None)
    scene.collection.objects.link(phone)
    keyed_world(phone,data['phone']['world_matrices'])
    phone_width, phone_height = float(data['phone']['width']),float(data['phone']['height'])
    for side,sign in [('left',-1),('right',1)]:
        anchor = bpy.data.objects.new(side+'_anchor',None)
        scene.collection.objects.link(anchor)
        anchor.parent = phone
        anchor.location = (sign*phone_width*.85,0,phone_height*.02)
        if data.get(side+'_image'):
            plane = image_plane(side+'_widget',root/data[side+'_image'],
                                (phone_width*.55,phone_height*.75))
            plane.parent = anchor
            plane.location = (0,0,0)
    if data.get('background'):
        distance = float(data.get('background_distance',10))
        width = distance*camera_data.sensor_width/camera_data.lens
        height = width*data['height']/data['width']
        background = image_plane('Background',root/data['background'],(width,height),
                                 int(data.get('background_frames',1)))
        background.parent = camera
        background.location = (0,0,-distance)
    scene.frame_set(1)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()))
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()))
    if args.render:
        args.render.parent.mkdir(parents=True,exist_ok=True)
        scene.render.image_settings.file_format='PNG'
        scene.render.filepath=str(args.render.resolve())
        bpy.ops.render.render(write_still=True)
    print('Bridge imported verified inputs; no tracking or visual approval implied.')


if __name__ == '__main__': main()
