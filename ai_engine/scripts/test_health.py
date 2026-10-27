#!/usr/bin/env python3
"""Wrapper to run test_health from scripts/ folder."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from test_health import main

if __name__ == "__main__":
    main()
