#!/usr/bin/env bash
# Slice STLs with the Centauri Carbon stock profiles and report time and filament.
#   tools/estimate.sh [0.2|0.4] file.stl ...
# 0.2 = 0.2 mm nozzle at 0.10 mm layers (best detail); 0.4 = 0.4 mm nozzle at 0.12 mm.
set -euo pipefail
cd "$(dirname "$0")/.."

ORCA=/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer
nozzle=${1:?usage: tools/estimate.sh [0.2|0.4] file.stl ...}; shift
case $nozzle in
    0.2) process="0.10mm Standard @Elegoo CC 0.2 nozzle" ;;
    0.4) process="0.12mm Fine @Elegoo CC 0.4 nozzle" ;;
    *) echo "nozzle must be 0.2 or 0.4" >&2; exit 1 ;;
esac

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
tools/orca_flatten.py "Elegoo Centauri Carbon $nozzle nozzle" "$work/machine.json"
tools/orca_flatten.py "$process" "$work/process.json"
tools/orca_flatten.py "Elegoo PLA @ECC" "$work/filament.json"

for stl in "$@"; do
    out="$work/$(basename "$stl" .stl)"
    mkdir -p "$out"
    "$ORCA" --slice 0 --load-settings "$work/machine.json;$work/process.json" \
        --load-filaments "$work/filament.json" --outputdir "$out" "$stl" > "$out/log" 2>&1 \
        || { echo "$stl: slice failed"; tail -3 "$out/log"; continue; }
    time=$(sed -n 's/^; estimated printing time (normal mode) = //p' "$out"/*.gcode | head -1)
    grams=$(sed -n 's/^; total filament used \[g\] = //p' "$out"/*.gcode | head -1)
    printf '%-40s %s nozzle  %12s  %6s g\n' "$(basename "$stl")" "$nozzle" "$time" "$grams"
done
