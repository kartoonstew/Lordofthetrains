#!/usr/bin/env bash
# Export STLs and preview renders for OpenSCAD models (none exist right now).
# Bag End is built in Blender by tools/build_bag_end.sh, not by this script.
#   tools/build.sh            build every OpenSCAD model listed at the bottom
#   tools/build.sh name       build only models whose name matches
set -euo pipefail
cd "$(dirname "$0")/.."

OPENSCAD=${OPENSCAD:-openscad}
filter=${1:-}
built=0

# stl <scad> <name> [-D var=value ...]
stl() {
    local scad=$1 name=$2; shift 2
    [[ -n $filter && $name != *$filter* ]] && return
    local dir; dir=$(dirname "$scad")
    mkdir -p "$dir/stl"
    built=$((built + 1))
    echo "stl     $dir/stl/$name.stl"
    "$OPENSCAD" --quiet -o "$dir/stl/$name.stl" --export-format binstl "$@" "$scad"
}

# png <scad> <name> <camera eye_x,y,z,centre_x,y,z> [-D var=value ...]
png() {
    local scad=$1 name=$2 camera=$3; shift 3
    [[ -n $filter && $name != *$filter* ]] && return
    local dir; dir=$(dirname "$scad")
    mkdir -p "$dir/renders"
    built=$((built + 1))
    echo "render  $dir/renders/$name.png"
    "$OPENSCAD" --quiet --render -o "$dir/renders/$name.png" --imgsize=1400,1050 \
        --colorscheme=Tomorrow --camera="$camera" "$@" "$scad"
}

# Add one stl/png call per OpenSCAD model here, for example:
#   stl lotr/shire/some_piece/some_piece.scad some_piece
#   png lotr/shire/some_piece/some_piece.scad some_piece_front 0,-80,40,0,0,10

if (( built == 0 )); then
    if [[ -n $filter ]]; then
        echo "Nothing built: no OpenSCAD model matches '$filter'. Bag End is built with tools/build_bag_end.sh."
    else
        echo "No OpenSCAD models to build yet. Bag End is built with tools/build_bag_end.sh."
    fi
fi
