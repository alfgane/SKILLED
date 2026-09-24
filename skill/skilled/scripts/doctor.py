#!/usr/bin/env python3
"""Verify native ChatGPT authentication, Codex agents, and the Sol xhigh catalog entry."""
from __future__ import annotations

import argparse
import json
import sys

from native_codex import SetupError, default_locations, inspect


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home")
    parser.add_argument("--codex-home")
    parser.add_argument("--profile")
    parser.add_argument("--codex-bin", default="codex")
    args = parser.parse_args()
    try:
        home, codex_home = default_locations(args.home, args.codex_home)
        print(json.dumps(inspect(home, codex_home, args.codex_bin, args.profile), indent=2))
        return 0
    except (SetupError, OSError, ValueError) as exc:
        message = str(exc) if isinstance(exc, SetupError) else f"Local diagnostic error ({type(exc).__name__})."
        print(f"DOCTOR FAILED: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
