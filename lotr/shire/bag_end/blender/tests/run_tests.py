"""Run every test_* function in tests/test_*.py inside Blender; exit 1 on any failure.

    tools/blender.sh lotr/shire/bag_end/blender/tests/run_tests.py [test_module ...]
"""
import importlib.util
import pathlib
import sys
import traceback

here = pathlib.Path(__file__).parent
only = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ran = failed = 0
for path in sorted(here.glob("test_*.py")):
    if only and path.stem not in only:
        continue
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in sorted(n for n in dir(module) if n.startswith("test_")):
        ran += 1
        try:
            getattr(module, name)()
            print(f"PASS {path.stem}.{name}")
        except Exception:
            failed += 1
            print(f"FAIL {path.stem}.{name}")
            traceback.print_exc()
print(f"{ran - failed}/{ran} passed")
sys.exit(1 if failed or not ran else 0)
