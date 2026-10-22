#!/usr/bin/env python3
"""usage: run_play.py BATCH ID [ID ...]; a play that raised is logged (its record is kept with status FAILED) and NOT retried here: the caller reads the error first (CLAUDE.md rule 7)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenarios
batch = sys.argv[1]
for pid in sys.argv[2:]:
    try:
        r = scenarios.run(pid, batch); print('RESULT', pid, r['status'], flush=True)
    except Exception as e:
        print('FAILED', pid, repr(e), flush=True)
