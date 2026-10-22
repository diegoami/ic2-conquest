"""Totals over the latest analysis file of each seed (the last run in each <variant>_s<seed>.jsonl) -> summary.json (new file, versioned).
python3 summarize.py"""
import glob, json, re
from collections import Counter
from pathlib import Path
DATA = Path(__file__).resolve().parent
out = {}
for s in (12345, 2, 10, 14):
    fs = sorted(glob.glob(str(DATA / f"analysis_hook_s{s}*.json")), key=lambda x: (len(x), x))
    d = json.load(open(fs[-1]))
    out[s] = {"file": Path(fs[-1]).name, "records": len(d), "by_site": dict(Counter(c["site"] for c in d)),
              "checks_ok": sum(c.get("checks_ok") is True for c in d), "checks_failed": sum(c.get("checks_ok") is False for c in d),
              "war_declared_this_turn": sum(bool(c.get("war_declared_this_turn")) for c in d),
              "intercept_capital_reasons": dict(Counter(("aboard" if c.get("threat_aboard") else "not at war") for c in d if c["site"] == "intercept_capital")),
              "moved_closer": sum(1 for c in d if c.get("dist_target_after") is not None and c["dist_target_after"] < c["dist_target_before"]),
              "gone_or_unmatched_after": sum(1 for c in d if c.get("dist_target_after") is None),
              "end_turns": max((c["end"] for c in d), default=0)}
tot = Counter()
for v in out.values():
    tot.update(v["by_site"]); tot["checks_ok"] += v["checks_ok"]; tot["checks_failed"] += v["checks_failed"]; tot["records"] += v["records"]
out["total"] = dict(tot)
p = DATA / "summary.json"; k = 1
while p.exists(): k += 1; p = DATA / f"summary.v{k}.json"
p.write_text(json.dumps(out, indent=1, default=str)); print(p.name); print(json.dumps(out, indent=1, default=str))
