from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python convert_png_to_pdf_eps.py <output-base> [dpi]", file=sys.stderr)
        return 2

    out_base = Path(sys.argv[1]).resolve()
    dpi = float(sys.argv[2]) if len(sys.argv) > 2 else 1200.0

    png_path = out_base.with_suffix(".png")
    pdf_path = out_base.with_suffix(".pdf")
    eps_path = out_base.with_suffix(".eps")

    if not png_path.exists():
        print(f"PNG not found: {png_path}", file=sys.stderr)
        return 1

    if shutil.which("pdftops") is None:
        print("pdftops was not found in PATH.", file=sys.stderr)
        return 1

    with Image.open(png_path) as image:
        image.convert("RGB").save(pdf_path, "PDF", resolution=dpi)

    subprocess.run(
        ["pdftops", "-eps", "-level3", pdf_path.name, eps_path.name],
        cwd=out_base.parent,
        check=True,
    )

    print(f"Converted {png_path.name} -> {pdf_path.name} -> {eps_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
