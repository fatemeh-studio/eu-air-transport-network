"""Shared helpers for the European Air Transport Network project.

Centralises project paths, the colour palette used across every notebook, and
small IO/plotting helpers so styling stays consistent and no module hard-codes
an absolute path.

Data vintage: OpenFlights **June 2014** route snapshot. Every figure produced
with these helpers describes 2014 — this is not the current network.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.figure as mfig

# --------------------------------------------------------------------------- #
# Project paths — resolved relative to this file, never hard-coded.
# src/utils.py -> parents[1] is the repo root.
# --------------------------------------------------------------------------- #
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]
DATA_DIR: Path = PROJECT_ROOT / "data"
FIGURES_DIR: Path = PROJECT_ROOT / "figures"
NETWORK_VIZ_DIR: Path = PROJECT_ROOT / "network_viz"
DB_PATH: Path = PROJECT_ROOT / "network.db"

AIRPORTS_DAT: Path = DATA_DIR / "airports.dat"
ROUTES_DAT: Path = DATA_DIR / "routes.dat"

# --------------------------------------------------------------------------- #
# Data provenance — reused in figure titles so every export is dated.
# --------------------------------------------------------------------------- #
DATA_VINTAGE: str = "June 2014"
DATA_SOURCE: str = "OpenFlights"
FIG_CAPTION: str = f"European Air Transport Network · {DATA_VINTAGE} · {DATA_SOURCE}"

# --------------------------------------------------------------------------- #
# Colour palette — defined ONCE, imported everywhere for cross-notebook
# consistency. "Aviation at night" dark theme for the geographic maps.
# --------------------------------------------------------------------------- #
COLORS: dict[str, str] = {
    "bg": "#0d1b2a",         # figure / ocean background
    "land": "#1b263b",       # land fill
    "coastline": "#415a77",  # borders & coastlines
    "route": "#48cae4",      # route lines
    "node_low": "#ffd166",   # low-degree airports
    "node_high": "#ef476f",  # high-degree hubs
    "accent": "#48cae4",
    "vienna": "#ffd60a",     # highlight colour for VIE in later notebooks
    "text": "#e0e1dd",
}

# Continuous colourscale for node degree (any valid Plotly colourscale name).
DEGREE_COLORSCALE: str = "Plasma"

# Categorical palette for discrete series (communities in NB03, etc.).
CATEGORICAL_PALETTE: list[str] = [
    "#48cae4", "#ef476f", "#ffd166", "#06d6a0", "#118ab2",
    "#f78c6b", "#9b5de5", "#00bbf9", "#fee440", "#f15bb5",
]


def ensure_dir(path: Path) -> Path:
    """Create a directory (and parents) if it does not exist.

    Args:
        path: Directory to create.

    Returns:
        The same path, now guaranteed to exist.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_fig_png(fig: mfig.Figure, filename: str, dpi: int = 150) -> Path:
    """Save a matplotlib figure to ``figures/`` as PNG at portfolio resolution.

    Args:
        fig: Matplotlib figure to save.
        filename: File name, with or without the ``.png`` extension.
        dpi: Output resolution; the project standard is 150 dpi.

    Returns:
        Path to the written PNG.
    """
    ensure_dir(FIGURES_DIR)
    if not filename.lower().endswith(".png"):
        filename += ".png"
    out = FIGURES_DIR / filename
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    return out