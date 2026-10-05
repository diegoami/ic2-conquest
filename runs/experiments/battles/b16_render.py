#!/usr/bin/env python3
"""Render findings/2026-10-05-battle-peace-offer.md from findings/b16-finding.skeleton.md and the raw data (b16_raw.py), and write a NEW
`b16-facts-<stamp>.json` beside the older ones: one entry per fact (id, value, raw source, the skeleton lines that state it as the sentence template).

    python3 runs/experiments/battles/b16_render.py            # writes the finding and the facts file
    python3 runs/experiments/battles/b16_render.py --check    # exit 1 if the finding differs from the rendering (what the audit checks too)"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b16_raw as R  # noqa: E402
import common as C  # noqa: E402
import b16_common as B  # noqa: E402


def main():
    sk = R.SKELETON.read_text()
    out = R.render(sk)
    if "--check" in sys.argv:
        ok = R.FINDING.read_text() == out
        print("finding equals the rendering:", ok)
        sys.exit(0 if ok else 1)
    V, S = R.values()
    lines = sk.split("\n")
    facts = []
    for k in sorted(V):
        tpl = [l.strip() for l in lines if re.search(r"%%%s(?::[a-z]+)?%%" % re.escape(k), l)]
        if tpl:
            facts.append({"id": k, "value": V[k], "source": S[k], "templates": tpl})
    R.FINDING.write_text(out)
    p = C.write_new(B.DATA, "b16-facts-%s.json" % C.STAMP, json.dumps({"skeleton": "findings/b16-finding.skeleton.md", "facts": facts}, indent=1))
    print(R.FINDING, p, len(facts), "facts")


if __name__ == "__main__":
    main()
