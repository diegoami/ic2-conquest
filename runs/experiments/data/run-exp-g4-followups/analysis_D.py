#!/usr/bin/env python3
"""Check D, offline: one line per mobilise arm of the logs g4_checks-D-*, D2-*, D3-*, D4-*, D5-* (`mobilize_pressed` for the human arms, `ai_arm` for the AI arms): what the game did with the
ready queued unit (new army with its position, the unit added to an old army, the refusal box), so the finding cites a tracked table. Output analysis_D.txt (next free version)."""
import json, sys
from pathlib import Path
D = Path(__file__).resolve().parent; sys.path.insert(0, str(D))
from versioned import write_new
L = ["# analysis_D: mobilise arms"]
for f in sorted(D.glob("g4_checks-D*-*.jsonl")) + sorted(p for p in D.glob("g4_checks-D-*.jsonl")):
    pass
files = sorted(set(sorted(D.glob("g4_checks-D-*.jsonl")) + sorted(D.glob("g4_checks-D[2-9]-*.jsonl"))), key=lambda p: p.name)
for f in files:
    L.append(f"== {f.name}")
    for line in open(f):
        d = json.loads(line); st = d.get("step")
        if st == "mobilize_pressed":
            refused = [t for t in d.get("dismissed", []) if "cannot mobilise" in t]
            L.append(f"  {d['tag']}: armies {d['armies_before']} -> {d['armies_after']}; new armies {d['new_armies']}; old armies changed {[(c[0], c[1], c[2][-1]) for c in d['changed_old_armies']]}; queue troops before {d['slot_troops_before'][:4]} after {d['slot_troops_after'][:4]}; refusal box {refused or None}")
        elif st in ("move_try", "move_failed", "army0", "turn1_move", "turn2_start"):
            L.append(f"  {d.get('tag')}: {st} " + json.dumps({k: v for k, v in d.items() if k not in ('step', 't', 'tag', 'queue', 'texts')}, default=str)[:200])
        elif st == "ai_arm":
            L.append(f"  {d['tag']}: AI nation {d['nation']} ({d.get('city')}) staged slot(s) {d.get('staged_slot', d.get('staged_slots'))}; wars with {d.get('wars_with')}; queue after {d['queue_after'][:5]}; armies {d['armies_before']} -> {d['armies_after']}; "
                     f"watched {[(w['army'], 'units %d -> %d' % (len(w['before']), len(w['after'])), w['pos_before'], '->', w['pos_after']) for w in d['watch']]}; new armies {d['new_armies']}")
print(write_new(D / "analysis_D.txt", "\n".join(L) + "\n"))
