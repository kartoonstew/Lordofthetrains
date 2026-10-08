#!/usr/bin/env bash
# Run a Python script in headless Blender with the Bag End package importable.
#   tools/blender.sh path/to/script.py [args for the script...]
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
script=$1; shift
exec "$BLENDER" --background --factory-startup --python-exit-code 1 \
    --python-expr "import sys; sys.path.insert(0, '$PWD/lotr/shire/bag_end/blender')" \
    --python "$script" -- "$@"
