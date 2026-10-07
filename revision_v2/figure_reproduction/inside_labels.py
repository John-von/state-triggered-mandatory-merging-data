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

def arrange_inside(fig, axes, n):
    for ax in axes:
        for loc in ['left', 'center', 'right']:
            ax.set_title('', loc=loc)
    if n in [9, 10, 11, 12, 13]:
        fig.subplots_adjust(top=0.98)
    if n == 5:
        fig.subplots_adjust(top=0.98, hspace=0.3)
    if n == 8:
        fig.subplots_adjust(top=0.97)
    if n == 6:
        for ax in axes:
            for c in ax.collections:
                if len(c.get_offsets()) == 20:
                    c.set_sizes(np.full(20, 26.0))
        for lg in list(fig.legends):
            lg.remove()
    else:
        for lg in list(fig.legends):
            handles = axes[0].get_legend_handles_labels()[0] if n == 3 else lg.legend_handles
            labels = [t.get_text() for t in lg.get_texts()]
            lg.remove()
            names = {'Safety-priority cooperation': 'COOP', 'State-triggered cooperation': 'ECO', 'Passive merging': 'PASSIVE'}
            labels = [names.get(s, s) for s in labels]
            if n == 10:
                axes[0].legend(handles, labels, loc='upper right', ncol=1, frameon=False, fontsize=6.7, handlelength=1.3, handletextpad=0.4, labelspacing=0.2, borderaxespad=0.3)
            elif n in [3, 11, 12, 13]:
                lo, hi = axes[0].get_ylim()
                if n in [3, 11]:
                    axes[0].set_ylim(lo, hi + 0.12 * (hi - lo))
                axes[0].legend(handles, labels, loc='upper center', bbox_to_anchor=(0.58, 0.99), ncol=3, frameon=False, fontsize=6.7, handlelength=1.15, columnspacing=0.7, handletextpad=0.3, borderaxespad=0.2)
            else:
                axes[0].legend(handles, labels, loc='best', frameon=False, fontsize=7)
    if n == 9:
        axes[0].legend(loc='upper right', frameon=False, fontsize=7.2)
    if n == 12:
        for ax in axes[2:]:
            lo, hi = ax.get_ylim()
            ax.set_ylim(lo + 0.5, hi)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for i, ax in enumerate(axes):
        is_heat = bool(ax.images)
        label = ax.text(0.016, 0.985, f'({chr(97 + i)})', transform=ax.transAxes, ha='left', va='top', fontsize=7.6 if is_heat else 8.3, zorder=20)
        candidates = [(0.018, 0.975, 'left', 'top'), (0.98, 0.975, 'right', 'top'), (0.018, 0.035, 'left', 'bottom'), (0.98, 0.035, 'right', 'bottom'), (0.5, 0.975, 'center', 'top'), (0.98, 0.5, 'right', 'center'), (0.018, 0.5, 'left', 'center'), (0.5, 0.035, 'center', 'bottom')]
        if is_heat:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            box = label.get_window_extent(renderer)
            conflicting = [t for t in ax.texts if t is not label and box.expanded(1.08, 1.12).overlaps(t.get_window_extent(renderer))]
            for text in conflicting:
                x, y = text.get_position()
                shift = 0.16 if ax.yaxis_inverted() else -0.16
                text.set_position((x, y + shift))
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            remaining = [t.get_text() for t in ax.texts if t is not label and label.get_window_extent(renderer).overlaps(t.get_window_extent(renderer))]
            assert not remaining, (n, i, remaining)
            assert np.allclose(ax.get_ylim(), ax.images[0].get_extent()[2:])
        else:
            if n == 10 and i == 1:
                candidates = [(0.018, 0.89, 'left', 'top')] + candidates
            if n == 7:
                candidates = ([(0.5, 0.975, 'center', 'top')] if i == 4 else [(0.98, 0.975, 'right', 'top')]) + candidates
            candidates += [(x, y, 'left', 'top') for y in [0.9, 0.75, 0.6, 0.45, 0.3, 0.15] for x in [0.02, 0.3, 0.6, 0.85]]
            best = None
            for x, y, ha, va in candidates:
                label.set_position((x, y))
                label.set_ha(ha)
                label.set_va(va)
                score = overlaps_data(ax, label.get_window_extent(renderer), renderer, label)
                if best is None or score < best[0]:
                    best = (score, x, y, ha, va)
                if score == 0:
                    break
            score, x, y, ha, va = best
            label.set_position((x, y))
            label.set_ha(ha)
            label.set_va(va)
            assert score == 0, (n, i, 'No unobstructed letter position', score)
        label.set_gid('panel-letter')
