#!/usr/bin/env python3
"""Audit the recorded Fig.7 input; derived pixels only, never manufacturing dimensions."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SCRIPT = HERE / 'official-input-a9d383c-measure_pads.py'
IMAGE = HERE.parents[2] / 'claude/official-evidence/fig7-baseboard-back-native.png'
spec = importlib.util.spec_from_file_location('official_directional_input', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
a = np.asarray(Image.open(IMAGE).convert('RGB')).astype(int)
r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
c = mod.components((r > 110) & (g > 85) & (b < r - 35) & (g > b + 25))
n, cy, cx, hh, ww = c.T
dia = (hh + ww) / 2
circ = np.abs(hh - ww) / np.maximum(hh, ww)
fill = n / (np.pi / 4 * hh * ww)
solid = c[(fill > .8) & (circ < .18) & (dia > 40) & (dia < 60)]
rows = {}
for p in solid:
    rows.setdefault(round(p[1] / 20), []).append(p)
pads = np.array(sorted(max(rows.values(), key=len), key=lambda p: p[2]))
assert len(pads) == 4, 'Unexpected pad count'
holes = c[(circ < .3) & (dia > 35) & (dia < 95)][:, [2, 1]]
p = holes[(holes[:, 0] > 1040) & (holes[:, 0] < 1170)]
cols = [p[p[:, 0] < 1105], p[p[:, 0] >= 1105]]
assert [len(x) for x in cols] == [10, 10], 'Not exactly two columns of ten'
cols = [x[np.argsort(x[:, 1])] for x in cols]
h, v = mod.grid_pitch(holes, 1040, 1170, 1105)
sx, sy = h / 2.54, v / 2.54
result = {
    'classification': 'derived; no physical measurements; not for fabrication',
    'script_sha256': hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
    'image_sha256': hashlib.sha256(IMAGE.read_bytes()).hexdigest(),
    'header_column_counts': [len(x) for x in cols],
    'header_columns_xy_px': [x.tolist() for x in cols],
    'paired_header_horizontal_pitch_px': (cols[1][:, 0] - cols[0][:, 0]).tolist(),
    'paired_header_vertical_misalignment_px': (cols[1][:, 1] - cols[0][:, 1]).tolist(),
    'sx_px_per_mm': sx,
    'sy_px_per_mm': sy,
    'sx_over_sy': sx / sy,
    'pad_centres_xy_px': pads[:, [2, 1]].tolist(),
    'pad_widths_px': pads[:, 4].tolist(),
    'pad_heights_px': pads[:, 3].tolist(),
    'pad_adjacent_horizontal_distances_mm': (np.diff(pads[:, 2]) / sx).tolist(),
    'pad_first_last_horizontal_distance_mm': float((pads[-1, 2] - pads[0, 2]) / sx),
    'pad_mean_width_mm_using_sx': float(pads[:, 4].mean() / sx),
    'pad_mean_height_mm_using_sy': float(pads[:, 3].mean() / sy),
    'upstream_printed_diameter_mm_mixes_axes': float(((pads[:, 3] + pads[:, 4]) / 2).mean() / sx),
    'limitations': ['Segmentation reused from upstream; this is an algorithm audit, not an independent physical measurement.', 'Directional diameter values remain bounding-box estimates of image segmentation, not verified metal contact areas.', 'Upstream grid_pitch only requires >=3 points per column; this fixed input was explicitly verified to have 10 each.'],
}
print(json.dumps(result, ensure_ascii=False, indent=2))
