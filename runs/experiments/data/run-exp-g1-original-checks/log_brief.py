#!/usr/bin/env python3
"""Print the key steps of one or more g1 logs (read-only helper): python3 log_brief.py <log.jsonl> ..."""
import json, sys
KEYS = ("loaded", "end_turn_ok", "game_over", "end_of_game_closed", "error", "autosave_kept", "end_turn_error", "new_game_form", "new_game_started", "opened_staged", "balance_sheet", "alive")
for f in sys.argv[1:]:
    print("==", f)
    for l in open(f):
        j = json.loads(l)
        if j["step"] in KEYS:
            print(j["step"], {k: j.get(k) for k in ("tag", "deposed", "kept", "error", "closed", "treasury_staged", "texts") if k in j}, (j.get("memory_after") or {}).get("treasury"))
