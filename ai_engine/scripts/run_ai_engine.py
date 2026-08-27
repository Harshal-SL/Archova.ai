"""CLI shortcut runner for the Complete AI Engine (REE + SAE)."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_ai_engine_run import main

if __name__ == "__main__":
    main()
