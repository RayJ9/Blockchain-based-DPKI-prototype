"""Compatibility imports for the shared prototype runner."""
from pathlib import Path
import runpy

SOURCE = Path(__file__).resolve().parent.parent / "simu2-8-packaged/real_sweep_figures.py"
globals().update({key: value for key, value in runpy.run_path(str(SOURCE)).items() if not key.startswith("__")})
