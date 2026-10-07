"""Reproduce Figure 3 from the archived main experiment."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import t
from inside_labels import arrange_inside
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'figures'
OUT.mkdir(exist_ok=True)
raw = np.concatenate([np.loadtxt(ROOT.parent / 'PLOS_ONE_Mixed_Traffic_Merging_Data' / 'data' / 'raw' / n, delimiter=',', skiprows=1) for n in ['joint_raw.csv', 'eco_joint_raw.csv']])
plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 8, 'axes.labelsize': 8, 'xtick.labelsize': 7.2, 'ytick.labelsize': 7.2, 'axes.linewidth': 0.65, 'pdf.fonttype': 42, 'svg.fonttype': 'none'})
fig, aa = plt.subplots(2, 2, figsize=(6.45, 4.25))
fig.subplots_adjust(left=0.095, right=0.98, bottom=0.12, top=0.98, wspace=0.31, hspace=0.34)
spacing = [40, 34, 28, 24, 20]
density = 1000 / np.array(spacing)
colors = ['#AD332B', '#1A6B4D', '#3D5294']
markers = ['o', 'D', 's']
names = ['Safety-priority cooperation', 'State-triggered cooperation', 'Passive merging']
for ax, col, yl in zip(aa.flat, [8, 10, 12, 20], ['Fuel (L/100 km)', 'Speed standard deviation (m/s)', 'Stopped-vehicle time (veh s)', 'Mean speed (m/s)']):
    for mode, c, m, n in zip([1, 3, 2], colors, markers, names):
        mu = []
        ci = []
        for sp in spacing:
            v = raw[np.isclose(raw[:, 1], sp) & np.isclose(raw[:, 2], 0.75) & (raw[:, 3] == mode), col]
            assert len(v) == 20
            mu.append(v.mean())
            ci.append(t.ppf(0.975, 19) * v.std(ddof=1) / np.sqrt(20))
        ax.errorbar(density, mu, yerr=ci, fmt=m + '-', color=c, mfc='white', ms=3.5, lw=1, capsize=2, elinewidth=0.7, label=n)
    ax.set_xlabel('Target-lane density (veh/km)')
    ax.set_ylabel(yl)
    ax.tick_params(direction='in', top=True, right=True, length=2.5, width=0.6)
    ax.grid(color='#DFE3E8', lw=0.4)
    ax.set_axisbelow(True)
fig.legend(*aa[0, 0].get_legend_handles_labels())
arrange_inside(fig, list(aa.flat), 3)
fig.canvas.draw()
for ext in ['png', 'pdf', 'svg', 'tif']:
    kw = {'dpi': 400} if ext == 'png' else {'dpi': 600, 'pil_kwargs': {'compression': 'tiff_lzw'}} if ext == 'tif' else {}
    fig.savefig(OUT / f'Fig3.{ext}', **kw)
for letter, ax in zip('abcd', aa.flat):
    box = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.02, 1.04)
    fig.savefig(OUT / f'Fig3{letter}.pdf', bbox_inches=box)
print('Reproduced Figure 3 with its legend inside.')
