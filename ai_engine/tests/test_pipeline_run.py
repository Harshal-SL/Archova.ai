"""Root test wrapper forwarding to app/sae/tests/test_pipeline_run.py."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
venv_python = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
    import subprocess
    proc = subprocess.run([str(venv_python), str(PROJECT_ROOT / "app" / "sae" / "tests" / "test_pipeline_run.py")] + sys.argv[1:])
    sys.exit(proc.returncode)

sys.path.insert(0, str(PROJECT_ROOT))
from app.sae.tests.test_pipeline_run import main

if __name__ == "__main__":
    main()
