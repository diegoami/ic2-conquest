#!/usr/bin/env python3
"""Run the plays of the refusal-text experiment: run_play.py BATCH ID [ID ...]. Scenario definitions are in scenarios.py (one function per id)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from play_lib import *
import scenarios
batch = sys.argv[1]
for pid in sys.argv[2:]:
    sc = scenarios.SC[pid]
    try:
        r = play(pid, batch, sc['src'], sc.get('ops', []), sc['act'], sc['note'], fixture_note=sc.get('fixture_note', ''), pre=sc.get('pre'), post=sc.get('post'))
        print('RESULT', pid, [(b['title'], b['text']) for b in r['boxes']], r['diff_ctl_after'].get('equal'), flush=True)
    except Exception as e:
        log('play_%s' % batch, '[%s] FAILED: %r' % (pid, e)); print('FAILED', pid, repr(e), flush=True)
