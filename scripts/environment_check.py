#!/usr/bin/env python3
"""Print this computer's environment fingerprint and compare it with docs/environment-baseline.json.

    python3 scripts/environment_check.py [--write-baseline]

Exit 0 when it matches, 1 with a plain-words diff when it differs (a different Wine, font set or exe changes screenshots, OCR and
window geometry: docs/environment.md). Needs Xvfb up for the screen size (the probe records an error otherwise, which also differs).
--write-baseline records the current fingerprint (do it only on purpose: the baseline is the environment evidence is compared to)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harness import environment  # noqa: E402

BASELINE = ROOT / "docs" / "environment-baseline.json"
WHAT = {"wine": "Wine version", "exe.name": "game exe", "exe.sha256": "game exe contents (SHA-256)",
        "xvfb_screen": "Xvfb screen size", "fonts.Book Antiqua": 'the font the Information panel gets for "Book Antiqua"',
        "fonts.MS Sans Serif": 'the host font matching "MS Sans Serif"', "fonts.liberation_count": "number of Liberation fonts on the host",
        "fonts.tahoma_wine": "fonts-wine Tahoma present", "prefix_fonts.sha256_12": "hash of the prefix's font registry",
        "prefix_fonts.count": "number of fonts in the prefix's font registry"}


def flat(d, prefix=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict) and "error" not in v:
            out.update(flat(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def diff(baseline, current):
    """Plain-words lines, one per field that differs (empty list: same)."""
    b, c = flat(baseline), flat(current)
    lines = []
    for k in sorted(set(b) | set(c)):
        if b.get(k) != c.get(k):
            lines.append(f"{WHAT.get(k, k)} differs: baseline {b.get(k)!r}, now {c.get(k)!r}")
    return lines


def main(argv):
    fp = environment.fingerprint(environment_prefix())
    print(json.dumps(fp, indent=2, sort_keys=True))
    if "--write-baseline" in argv:
        BASELINE.write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n")
        print(f"baseline written: {BASELINE}")
        return 0
    if not BASELINE.exists():
        print(f"no baseline at {BASELINE}", file=sys.stderr)
        return 1
    lines = diff(json.loads(BASELINE.read_text()), fp)
    if lines:
        print("\nThe environment differs from docs/environment-baseline.json:", file=sys.stderr)
        for line in lines:
            print("  - " + line, file=sys.stderr)
        return 1
    print("\nSame environment as the baseline.")
    return 0


def environment_prefix():
    from harness.driver import PREFIX
    return PREFIX


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
