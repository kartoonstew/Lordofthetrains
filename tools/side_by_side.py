#!/usr/bin/env python3
"""Put a reference photo and a model render side by side at the same height.

    tools/side_by_side.py ref.jpg render.png out.png
"""
import sys

from PIL import Image

HEIGHT = 700
GAP = 20

if len(sys.argv) != 4:
    sys.exit(__doc__)
ref, render = (Image.open(p).convert("RGB") for p in sys.argv[1:3])
ref, render = (im.resize((round(im.width * HEIGHT / im.height), HEIGHT)) for im in (ref, render))
sheet = Image.new("RGB", (ref.width + GAP + render.width, HEIGHT), "white")
sheet.paste(ref, (0, 0))
sheet.paste(render, (ref.width + GAP, 0))
sheet.save(sys.argv[3])
