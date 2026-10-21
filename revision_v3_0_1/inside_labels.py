"""Keep panel letters inside the axes, without title bands or blank heatmap rows."""
import json
from pathlib import Path
import numpy as np
from matplotlib.transforms import Bbox
from matplotlib.path import Path as MPath
from matplotlib.collections import LineCollection
ROOT = Path(__file__).resolve().parent

def overlaps_data(ax, box, renderer, skip):
    padded = box.expanded(1.1, 1.14)
    score = 0
    for txt in ax.texts:
        if txt is skip or not txt.get_visible():
            continue
        if padded.overlaps(txt.get_window_extent(renderer)):
            score += 200
    lg = ax.get_legend()
    if lg and padded.overlaps(lg.get_window_extent(renderer)):
        score += 500
    for ln in ax.lines:
        if ln.get_visible() and ln.get_path().vertices.size:
            path = ln.get_transform().transform_path(ln.get_path())
            if path.intersects_bbox(padded, filled=False):
                score += 30
    for collection in ax.collections:
        offsets = np.asarray(collection.get_offsets())
        if len(offsets) > 1:
            pts = collection.get_offset_transform().transform(offsets)
            if any((padded.contains(*p) for p in pts)):
                score += 30
        if isinstance(collection, LineCollection):
            for p in collection.get_paths():
                if collection.get_transform().transform_path(p).intersects_bbox(padded, filled=False):
                    score += 20
    for patch in ax.patches:
        if patch.get_visible() and patch.get_transform().transform_path(patch.get_path()).intersects_bbox(padded, filled=True):
            score += 20
    return score

