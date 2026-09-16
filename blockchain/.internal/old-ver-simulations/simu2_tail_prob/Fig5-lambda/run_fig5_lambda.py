"""Compatibility entry point for the public experiment runner."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[5]
if __name__ == "__main__":
    runpy.run_path(str(ROOT / "experiments/arrival-rate/run_fig5_lambda.py"), run_name="__main__")
