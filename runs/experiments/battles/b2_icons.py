#!/usr/bin/env python3
"""B2 grid-word <-> icon check (offline, from the screenshots and saves of `b2_probe.py`): for every occupied cell of the three phases, the inner 26 x 26 of the 32 x 32
tile cropped from the screenshot (map origin at window y 28, tiles 32 px) is hashed; the grid word of the same cell is read from the save written at
the same moment (`B2_<phase>.SAV`). Claims checked: (1) every grid word has ONE icon image across all cells and phases (same word -> same tile),
(2) different words have different tile images, (3) the number of distinct words and cells per phase. Written as `b2-icons-<stamp>.json` (tracked).

    python3 runs/experiments/battles/b2_icons.py
"""
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
from state import battle_block as BB  # noqa: E402

# the three phases of the completed run b2-verify-20261004-093834.json
PHASES = [("placement", "b2_placement_window.png", "B2_placement.SAV"),
          ("after_end_turn_1", "b2_after_end_turn_1_window.png", "B2_after_end_turn_1.SAV"),
          ("after_end_turn_2", "b2_after_end_turn_2_window.png", "B2_after_end_turn_2.SAV")]


def rgb(p):
    raw = subprocess.run(["convert", str(p), "-depth", "8", "rgb:-"], capture_output=True).stdout
    w, h = map(int, subprocess.run(["identify", "-format", "%w %h", str(p)], capture_output=True, text=True).stdout.split())
    return w, h, raw


def tile_hash(w, raw, x, y, y0=28, t=32, inset=3):
    """Hash of the tile's INNER pixels (the outer 3 px are the cell border, which shows the neighbours' colour and differs with the position)."""
    rows = b"".join(raw[((y0 + y * t + r) * w + x * t + inset) * 3:((y0 + y * t + r) * w + x * t + t - inset) * 3] for r in range(inset, t - inset))
    return hashlib.sha256(rows).hexdigest()[:12]


def main():
    by_word, per_phase, cells = defaultdict(set), {}, []
    for phase, png, sv in PHASES:
        w, h, raw = rgb(C.ART / png)
        b = BB.from_save(C.ART / sv)
        n = 0
        for y in range(BB.GRID_H):
            for x in range(BB.GRID_W):
                word = b["grid"][BB.cell(x, y)]
                if word == BB.EMPTY:
                    continue
                th = tile_hash(w, raw, x, y)
                by_word[word].add(th)
                cells.append({"phase": phase, "cell": (x, y), "grid_word": word, "tile": th})
                n += 1
        per_phase[phase] = {"png": png, "save": sv, "png_sha256": C.sha(C.ART / png), "save_sha256": C.sha(C.ART / sv), "occupied_cells": n,
                            "distinct_words": len({c["grid_word"] for c in cells if c["phase"] == phase})}
    word_tiles = {str(k): sorted(v) for k, v in sorted(by_word.items())}
    tile_words = defaultdict(set)
    for wd, tiles in by_word.items():
        for t in tiles:
            tile_words[t].add(wd)
    out = {"per_phase": per_phase, "word_to_tiles": word_tiles,
           "every_word_has_one_icon": all(len(v) == 1 for v in by_word.values()),
           "different_words_have_different_icons": all(len(v) == 1 for v in tile_words.values()),
           "distinct_words_total": len(by_word), "cells_total": len(cells),
           "note": "tile hash = sha256 of the inner 26 x 26 pixels of the 32 x 32 cell (the 3 px border shows the neighbouring cell's colour and varies with position); the side colour is part of the icon"}
    p = C.write_new(C.DATA, f"b2-icons-{C.STAMP}.json", json.dumps(out, indent=1, default=str))
    print(p)
    print(json.dumps({k: out[k] for k in ("every_word_has_one_icon", "different_words_have_different_icons", "distinct_words_total", "cells_total")}), per_phase)


if __name__ == "__main__":
    main()
