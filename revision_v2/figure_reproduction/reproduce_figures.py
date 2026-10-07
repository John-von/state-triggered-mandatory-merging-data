"""Reproduce Figures 1 and 3-13; Figure 2 is supplied in figures/."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parent
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
for name in ["replot_legacy.py", "replot_fig3.py", "replot_original.py", "replot.py"]:
    subprocess.run([sys.executable, str(root / name)], env=env, check=True)
