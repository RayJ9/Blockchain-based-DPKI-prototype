"""Compatibility imports for unmodified request statistics."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from figure_dpki_pki_runtime.sweep_common import *
