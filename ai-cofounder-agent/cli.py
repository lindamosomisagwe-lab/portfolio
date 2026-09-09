#!/usr/bin/env python3
"""AI Cofounder Agent -- CLI prototype.

Usage:
  python3 cli.py run                              interactive session, idea typed at the prompt
  python3 cli.py run --idea-file sample_input.md   interactive session, idea read from a file
  python3 cli.py run --idea-file sample_input.md --script sample_run_answers.json
                                                    scripted founder answers, non-interactive demo run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cofounder.io import FounderIO
from cofounder.pipeline import run as run_pipeline
from cofounder.storage import Store


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Cofounder Agent CLI prototype")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Run the full pipeline on an idea")
    run_cmd.add_argument("--idea-file", help="Path to a text/markdown file containing the raw idea")
    run_cmd.add_argument("--script", help="Path to a JSON file of scripted founder answers (for demo runs)")

    args = parser.parse_args()

    if args.command == "run":
        if args.idea_file:
            idea_text = Path(args.idea_file).read_text().strip()
        else:
            print("Describe your idea (end with an empty line):")
            lines = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
            idea_text = "\n".join(lines)

        io = FounderIO(script_path=args.script)
        store = Store()
        run_pipeline(io, idea_text, store)


if __name__ == "__main__":
    main()
