#!/usr/bin/env python3
"""Flatten an OrcaSlicer profile's `inherits` chain into one self-contained JSON.

The Orca CLI doesn't resolve `inherits`, so slicing with a stock or user profile
silently drops most settings. This walks the chain through Orca's system and
user profile folders and writes the merged result.

    tools/orca_flatten.py "Elegoo Centauri Carbon 0.2 nozzle" out.json
"""
import json
import sys
from pathlib import Path

ORCA = Path.home() / "Library/Application Support/OrcaSlicer"


def index_profiles():
    by_name = {}
    for root in (ORCA / "system", ORCA / "user"):
        for path in root.rglob("*.json"):
            try:
                data = json.loads(path.read_text())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(data, dict) and "name" in data:
                by_name.setdefault(data["name"], data)
    return by_name


def flatten(name, profiles):
    if name not in profiles:
        sys.exit(f"profile not found: {name}")
    data = profiles[name]
    parent = data.get("inherits")
    merged = flatten(parent, profiles) if parent else {}
    merged.update(data)
    merged.pop("inherits", None)
    return merged


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    profile = flatten(sys.argv[1], index_profiles())
    Path(sys.argv[2]).write_text(json.dumps(profile, indent=1))
