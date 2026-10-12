"""Quick look at a g4 log: python3 summ.py <log> [step ...]  (prints one compact line per step; reading helper, changes nothing)."""
import json, sys
steps = set(sys.argv[2:])
for l in open(sys.argv[1]):
    d = json.loads(l)
    if steps and d.get("step") not in steps: continue
    d.pop("t", None); s = json.dumps(d, default=str)
    print(s[:700])
