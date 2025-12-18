from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.pdf_report import markdown_to_pdf  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate OpenSky project PDF report from Markdown template.")
    parser.add_argument(
        "--input",
        default=str(Path("reports") / "opensky_project_report_fr.md"),
        help="Input Markdown file",
    )
    parser.add_argument(
        "--output",
        default=str(Path("reports") / "opensky_project_report_fr.pdf"),
        help="Output PDF file",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    md = input_path.read_text(encoding="utf-8", errors="replace")
    markdown_to_pdf(md, output_path)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
