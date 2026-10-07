"""Redraw Figs 5, 6 and 8 from archived summary CSVs. 
Usage: python replot_original.py [--data-dir PATH] [--output-dir PATH]
"""
from pathlib import Path
import argparse, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from inside_labels import arrange_inside
from matplotlib.colors import LinearSegmentedColormap, Normalize
ROOT = Path(__file__).resolve().parent
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--data-dir', type=Path, default=ROOT.parent / 'PLOS_ONE_Mixed_Traffic_Merging_Data' / 'data' / 'summary')
p.add_argument('--output-dir', type=Path, default=ROOT / 'figures')
args = p.parse_args()
OUT = args.output_dir
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 8, 'axes.labelsize': 8, 'axes.titlesize': 8.3, 'xtick.labelsize': 7.2, 'ytick.labelsize': 7.2, 'legend.fontsize': 7.4, 'axes.linewidth': 0.65, 'savefig.facecolor': 'white', 'pdf.fonttype': 42, 'svg.fonttype': 'none'})

def frame(ax):
    ax.tick_params(direction='in', top=True, right=True, length=2.5, width=0.6, pad=2)
    ax.set_axisbelow(True)

def save(fig, axs, n):
    arrange_inside(fig, axs, n)
    fig.canvas.draw()
    for ext in ['png', 'pdf', 'svg', 'tif']:
        kw = {'dpi': 400} if ext == 'png' else {'dpi': 600, 'pil_kwargs': {'compression': 'tiff_lzw'}} if ext == 'tif' else {}
        fig.savefig(OUT / f'Fig{n}.{ext}', **kw)
    for l, ax in zip('abcd', axs):
        box = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted()).expanded(1.02, 1.04)
        fig.savefig(OUT / f'Fig{n}{l}.pdf', bbox_inches=box)
    plt.close(fig)
C = pd.read_csv(args.data_dir / 'eco_vs_coop_paired_summary.csv')
P = pd.read_csv(args.data_dir / 'eco_vs_passive_paired_summary.csv')
A = pd.read_csv(args.data_dir / 'eco_safety_ablation_summary.csv')
assert len(C) == len(P) == 25 and len(A) == 4
k = sorted(C.k1.unique())
pens = sorted(C.penetration.unique())
cmap = LinearSegmentedColormap.from_list('co_benefit', ['#AD332B', '#F7F7F2', '#1A6B4D'])
norm = Normalize(-26, 26)
fig, aa = plt.subplots(2, 2, figsize=(6.45, 3.9))
axs = list(aa.flat)
fig.subplots_adjust(left=0.075, right=0.875, bottom=0.12, top=0.94, wspace=0.23, hspace=0.4)
for ax, (key, title), letter in zip(axs, [('L100_saving_pct', 'Fuel-intensity saving'), ('sigma_reduction_pct', 'Speed-disturbance reduction'), ('arms_reduction_pct', 'Acceleration-RMS reduction'), ('speed_gain_pct', 'Mean-speed gain')], 'abcd'):
    z = C.pivot(index='penetration', columns='k1', values=key).loc[pens, k].to_numpy()
    im = ax.imshow(z, origin='lower', aspect='auto', cmap=cmap, norm=norm, interpolation='nearest')
    ax.set_xticks(range(5), [f'{v:.1f}' for v in k])
    ax.set_yticks(range(5), [str(round(v * 100)) for v in pens])
    ax.set_title(f'({letter}) {title}', loc='left', pad=5)
    ax.set_xlabel('Density (veh/km)')
    ax.set_ylabel('CAV penetration (%)')
    for i in range(5):
        for j in range(5):
            v = z[i, j]
            s = f'{(0 if abs(v) < 0.05 else v):.1f}'
            ax.text(j, i, s, ha='center', va='center', fontsize=7.4, color='white' if abs(v) > 16 else '#202020')
    frame(ax)
cax = fig.add_axes([0.904, 0.2, 0.02, 0.62])
cb = fig.colorbar(im, cax=cax, ticks=[-25, -10, 0, 10, 25])
cb.set_label('Relative improvement (%)', labelpad=4)
cb.ax.tick_params(labelsize=7.2, length=2.5, width=0.6)
save(fig, axs, 5)
c = C[C.penetration > 0].sort_values(['k1', 'penetration'])
q = P[P.penetration > 0].sort_values(['k1', 'penetration'])
assert np.allclose(c[['k1', 'penetration']], q[['k1', 'penetration']])
fig, aa = plt.subplots(1, 3, figsize=(6.45, 2.3))
axs = list(aa)
fig.subplots_adjust(left=0.075, right=0.882, bottom=0.245, top=0.93, wspace=0.4)
for ax, df, yk, xlabel, ylabel, letter in [(aa[0], c, 'speed_gain_pct', 'Fuel-intensity saving\nvs COOP (%)', 'Mean-speed gain (%)', 'a'), (aa[1], q, 'speed_gain_pct', 'Fuel-intensity saving\nvs PASSIVE (%)', 'Mean-speed gain (%)', 'b'), (aa[2], c, 'total_fuel_saving_pct', 'Fuel-intensity saving\nvs COOP (%)', 'Total-fuel saving (%)', 'c')]:
    sizes = 12 + 24 * df.penetration.to_numpy()
    im = ax.scatter(df.L100_saving_pct, df[yk], s=sizes, c=df.k1, cmap='viridis', vmin=25, vmax=50, edgecolor='#333', linewidth=0.35, zorder=3)
    ax.axhline(0, color='#555', ls=':', lw=0.65)
    ax.axvline(0, color='#555', ls=':', lw=0.65)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f'({letter})', loc='left', pad=4)
    ax.grid(color='#DFE3E8', lw=0.4)
    frame(ax)
handles = [aa[0].scatter([], [], s=12 + 24 * v, facecolor='#A6A6A6', edgecolor='#333', linewidth=0.35) for v in [0.25, 0.5, 0.75, 1]]
lg = fig.legend(handles, ['25%', '50%', '75%', '100%'], title='CAV penetration', loc='upper center', bbox_to_anchor=(0.49, 1), ncol=4, frameon=True, fancybox=False, edgecolor='#333', fontsize=7.2, title_fontsize=7.4, columnspacing=0.9, handletextpad=0.3, borderpad=0.25)
lg.get_frame().set_linewidth(0.5)
cax = fig.add_axes([0.909, 0.26, 0.015, 0.65])
cb = fig.colorbar(im, cax=cax, ticks=[25, 35, 50])
cb.set_label('Density (veh/km)', labelpad=3, fontsize=7.4)
cb.ax.tick_params(labelsize=7.2, length=2.5, width=0.6)
save(fig, axs, 6)
fig, aa = plt.subplots(1, 2, figsize=(6.45, 2.45))
axs = list(aa)
fig.subplots_adjust(left=0.084, right=0.98, bottom=0.28, top=0.9, wspace=0.26)
labs = ['Full\nsafeguards', 'No speed\nprediction', 'No barrier\nfilter', 'All three\ndisabled']
vals = [np.log10(A.final_gap_violation_sum + 1), A.min_gap_min]
for i, (ax, y, lab, col) in enumerate(zip(aa, vals, ['log₁₀(gap violations + 1)', 'Minimum net gap (m)'], ['#AD332B', '#3D5294'])):
    ax.bar(range(4), y, width=0.62, color=col, zorder=3)
    ax.set_xticks(range(4), labs)
    ax.set_ylabel(lab)
    ax.set_title(f"({'ab'[i]})", loc='left', pad=5)
    ax.axhline(0, color='#555', ls=':', lw=0.65)
    ax.grid(axis='y', color='#DFE3E8', lw=0.4)
    frame(ax)
save(fig, axs, 8)
print('Generated Figs 5, 6 and 8 from archived summary values.')
