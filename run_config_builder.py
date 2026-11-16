
import os
import sys
import runpy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

os.chdir(PROJECT_ROOT)

sys.path.insert(0, str(PROJECT_ROOT))

runpy.run_module(
    "config_builder.ui",
    run_name="__main__"
)
