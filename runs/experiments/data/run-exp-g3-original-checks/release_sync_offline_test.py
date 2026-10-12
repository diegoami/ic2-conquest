#!/usr/bin/env python3
"""Offline test (R1): three records with the same second-resolution name never overwrite each other. Uses a temp dir; no gh call."""
import sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from versioned import write_new
with tempfile.TemporaryDirectory() as t:
    n = f"release-sync-{time.strftime('%Y%m%d-%H%M%S')}.json"
    ps = [write_new(Path(t) / n, x) for x in "ABC"]
    assert len({p.name for p in ps}) == 3 and [p.read_text() for p in ps] == list("ABC"), ps
    print("OK", [p.name for p in ps])
