"""Deterministic contour partition and shared-target-frame assembly helpers."""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image


def partition(masks):
    if not masks:
        raise ValueError('At least one semantic mask is required')
    shape = masks[0].shape
    claimed = np.zeros(shape, dtype=bool)
    parts, skipped = [], []
    for index, mask in enumerate(masks):
        if mask.shape != shape or mask.ndim != 2:
            raise ValueError('Masks must have identical two-dimensional dimensions')
        owned = (mask >= 128) & ~claimed
        if owned.any():
            parts.append((index, owned.astype(np.uint8) * 255))
        else:
            skipped.append(index)
        claimed |= owned
    if (~claimed).any():
        parts.append((len(masks), (~claimed).astype(np.uint8) * 255))
    return parts, skipped


def validate_partition(masks):
    if not masks:
        raise ValueError('No pieces supplied')
    shape = masks[0].shape
    if any(m.shape != shape for m in masks):
        raise ValueError('Piece dimensions differ')
    if any(not np.isin(m, [0, 255]).all() for m in masks):
        raise ValueError('Ownership masks must be binary 0/255')
    count = np.sum(np.stack(masks) > 0, axis=0)
    result = {'uncovered_pixels': int((count == 0).sum()),
              'overlap_pixels': int((count > 1).sum()), 'pieces': len(masks)}
    if result['uncovered_pixels'] or result['overlap_pixels']:
        raise ValueError(f'Invalid partition: {result}')
    return result


def progress(part, time):
    start, end = float(part['start']), float(part['end'])
    if not math.isfinite(start + end + time) or end <= start:
        raise ValueError('Finite animation times and end > start required')
    u = max(0., min(1., (time - start) / (end - start)))
    return 1 - (1 - u) ** 3


def transform(image, part, p):
    if p >= 1:
        return image.copy()
    width, height = image.size
    scale = float(part.get('scale', 1)) * (1-p) + p
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError('Scale must be positive and finite')
    angle = math.radians(float(part.get('angle', 0)) * (1-p))
    c, s = math.cos(angle) / scale, math.sin(angle) / scale
    # Pillow needs output -> source inverse mapping; pivot is shared frame centre.
    tx = width/2 + float(part.get('dx', 0)) * (1-p)
    ty = height/2 + float(part.get('dy', 0)) * (1-p)
    matrix = (c, s, width/2-c*tx-s*ty,
              -s, c, height/2+s*tx-c*ty)
    return image.transform(image.size, Image.Transform.AFFINE, matrix,
                           resample=Image.Resampling.BICUBIC)


def assemble(target, base, specs, time, foreground=None):
    target, base = target.convert('RGBA'), base.convert('RGBA')
    if base.size != target.size:
        raise ValueError('Base and target dimensions differ')
    masks = [np.asarray(p['_mask'].convert('L')) for p in specs]
    if any(m.shape != (target.height, target.width) for m in masks):
        raise ValueError('Mask and target dimensions differ')
    validate_partition(masks)
    if foreground is not None:
        foreground = foreground.convert('RGBA')
        if foreground.size != target.size:
            raise ValueError('Foreground dimensions differ')
    ps = [progress(p, time) for p in specs]
    # Avoid resampling, ordering or alpha-rounding seams at final registration.
    if all(p == 1 for p in ps):
        result = target.copy()
    else:
        result = base.copy()
        target_array = np.asarray(target)
        for spec, mask, p in zip(specs, masks, ps):
            if time < float(spec['start']):
                continue
            pixels = target_array.copy()
            alpha = pixels[..., 3].astype(np.float32) * (mask / 255.)
            if foreground is not None:
                alpha *= 1 - np.asarray(foreground)[..., 3] / 255.
            pixels[..., 3] = np.rint(alpha).astype(np.uint8)
            result = Image.alpha_composite(result, transform(Image.fromarray(pixels), spec, p))
            if spec.get('_edge') is not None and p < 1:
                edge = spec['_edge'].convert('RGBA')
                if edge.size != target.size:
                    raise ValueError('Prealigned edge must use full-frame dimensions')
                edge.putalpha(edge.getchannel('A').point(lambda a: round(a*(1-p))))
                result = Image.alpha_composite(result, transform(edge, spec, p))
    if foreground is not None:
        result = Image.alpha_composite(result, foreground)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('partition')
    p.add_argument('--masks', nargs='+', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p = sub.add_parser('assemble')
    for name in ('target', 'base', 'plan', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--foreground', type=Path)
    p.add_argument('--time', type=float, required=True)
    args = parser.parse_args()
    if args.command == 'partition':
        masks = [np.asarray(Image.open(p).convert('L')) for p in args.masks]
        pieces, skipped = partition(masks)
        report = validate_partition([m for _, m in pieces])
        args.out.mkdir(parents=True, exist_ok=True)
        report['skipped_input_indices'] = skipped
        report['masks'] = []
        for index, mask in pieces:
            label = args.masks[index].stem if index < len(args.masks) else 'remainder'
            name = f'{index:02d}_{label}.png'
            Image.fromarray(mask).save(args.out/name)
            report['masks'].append(name)
        (args.out/'partition.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
    else:
        root = args.plan.resolve().parent
        specs = json.loads(args.plan.read_text(encoding='utf-8'))['parts']
        for spec in specs:
            spec['_mask'] = Image.open(root/spec['mask']).convert('L')
            if 'edge' in spec:
                spec['_edge'] = Image.open(root/spec['edge']).convert('RGBA')
        result = assemble(Image.open(args.target), Image.open(args.base), specs, args.time,
                          Image.open(args.foreground) if args.foreground else None)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        result.save(args.out)


if __name__ == '__main__':
    main()
