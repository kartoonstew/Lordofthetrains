#!/usr/bin/env bash
# Build Bag End in Blender (.blend + renders), then put each render next to its reference photo.
#   tools/build_bag_end.sh [--no-render]
set -euo pipefail
cd "$(dirname "$0")/.."
DIR=lotr/shire/bag_end
tools/blender.sh $DIR/blender/build.py "$@" > /dev/null
[[ " $* " == *" --no-render "* ]] && exit 0
for pair in 01_door_elevation_broad:ref01 02_door_closeup_ross:ref02 03_front_with_oak_hall:ref03 \
            04_garden_party_sign_pd:ref04 05_door_and_window_bay_lumoplank:ref05; do
    ref=${pair%%:*}
    cam=${pair##*:}
    tools/side_by_side.py $DIR/refs/$ref.jpg $DIR/renders/render_$cam.png $DIR/renders/compare_$cam.png
    echo "compare $DIR/renders/compare_$cam.png"
done
