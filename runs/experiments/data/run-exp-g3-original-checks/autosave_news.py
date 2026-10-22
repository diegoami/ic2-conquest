"""Rule 6 helper: for every kept autosave named in the g3_checks logs, parse it (read-only, from the git-ignored artifacts folder / release) and write
the tracked autosave_news-<stamp>.jsonl with its date, news list and pending offer. The report uses these news lists (the memory buffer can hold stale tail
lines after a File>Open, so `news_all` of the earliest logs is not reliable for the new lines; the first mismatch seen is Q1c seven_control)."""
import hashlib, json, sys, time
from pathlib import Path
D = Path(__file__).resolve().parent; R = D.parents[3]; sys.path.insert(0, str(R)); sys.path.insert(0, str(D))
from state import sav
from versioned import write_new
ART = R / "artifacts/run-exp-g3-original-checks"
out = []
seen = set()
for f in sorted(D.glob("g3_checks-*.jsonl")):
    for l in open(f):
        r = json.loads(l)
        if r.get("step") in ("autosave_kept",):
            k = r["kept"]
            if k in seen or not (ART / k).exists(): continue
            seen.add(k); b = (ART / k).read_bytes(); s = sav.parse(b)
            out.append({"kept": k, "sha256": hashlib.sha256(b).hexdigest(), "date": s["date"], "turn": s["turn"], "pending_offer": s["pending_offer"], "news": s["news"], "log": f.name})
p = write_new(D / f"autosave_news-{time.strftime('%Y%m%d-%H%M%S')}.jsonl", "".join(json.dumps(o) + "\n" for o in out))
print(p.name, len(out))
