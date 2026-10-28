"""Multi-turn games played by a rule bot in both games (#232).

    python3 -m difftest.campaign START.SAV artifacts/run-exp-<name>/<run> --turns 5 --seed 12345 [--bot rulebot-1]

Each human turn: the bot decides from each game's OWN state, each game plays its own orders and End turn, and
the two states are compared (in full, and on the acting nation's own records). Orders that differ between the
games mean their visible states already differed. The original stays one process for the whole game (so its
random stream is continuous); the remake is continued from its native save each turn (checked equal to one
continuous session, 2026-10-28). Results: turns.jsonl (one line per turn, written as it goes) and summary.json.
A stopped game is not resumed in place (the original's random stream would restart); it is re-run in a new folder.
"""
import argparse
import importlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from difftest import actions as act  # noqa: E402
from difftest.compare import compare, scoped  # noqa: E402
from state.sav import NATIONS, load  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("start")
    ap.add_argument("out")
    ap.add_argument("--turns", type=int, default=5)
    ap.add_argument("--seed", type=int, default=12345)
    ap.add_argument("--bot", default="difftest.bot")
    a = ap.parse_args(argv)
    from difftest import original, remake
    bot = importlib.import_module(a.bot)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "run.json").write_text(json.dumps({"start": a.start, "turns": a.turns, "seed": a.seed, "bot": bot.NAME,
                                              "started": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
    rlog = lambda *x: None
    o = original.OriginalSession(a.start, out / "original", a.seed, f"C{out.name[-12:]}", log=rlog)
    so = o.checkpoint("t00-start")
    rdir = out / "remake"
    rdir.mkdir()
    remake.run([], a.start, rdir / "t00", log=rlog)
    native, sr = rdir / "t00" / "a000.native", load(rdir / "t00" / "a000.SAV")
    first = None
    try:
        for k in range(1, a.turns + 1):
            nation = so["current_nation"]
            oo, orr = bot.decide(so), bot.decide(sr)
            row = {"turn": k, "date_original": so["date"], "date_remake": sr["date"], "nation": NATIONS[nation],
                   "nation_remake": NATIONS[sr["current_nation"]], "orders_original": oo, "orders_remake": orr,
                   "orders_same": oo == orr}
            replies = []
            for j, x in enumerate(oo + [{"op": "end_turn"}]):
                texts, err = o.act(act.validate(x), f"t{k:02d}-a{j:02d}")
                replies.append({"op": x["op"], "reply": texts, "error": err})
            so = o.state
            names = act.checkpoint_names(orr + [{"op": "end_turn"}])
            remake.run([act.validate(x) for x in orr + [{"op": "end_turn"}]], native, rdir / f"t{k:02d}", log=rlog, template=a.start)
            last = rdir / f"t{k:02d}" / names[-1]
            native, sr = last.with_suffix(".native"), load(last.with_suffix(".SAV"))
            rec = [json.loads(l) for l in (rdir / f"t{k:02d}" / "receipt.jsonl").read_text().splitlines() if l.strip()]
            d = compare(so, sr)
            own = scoped(d, so, sr, nation)
            row.update(replies_original=replies,
                       replies_remake=[{"command": e.get("resolved", e["command"]), "reply": (e.get("lines") or [])[1:4]}
                                       for e in rec if e["kind"] == "command"],
                       differences=len(d["fields"]) + d["map"]["count"], own_differences=len(own),
                       own_fields=own[:40], first_fields=d["fields"][:25])
            if first is None and (not row["orders_same"] or row["differences"]):
                first = k
            row["diverged"] = first is not None
            with open(out / "turns.jsonl", "a") as f:
                f.write(json.dumps(row, default=str) + "\n")
            print(f"turn {k} {row['nation']}: orders {'same' if row['orders_same'] else 'DIFFER'}, "
                  f"{row['differences']} differences ({row['own_differences']} own)", flush=True)
    finally:
        o.close()
    (out / "summary.json").write_text(json.dumps({"turns": a.turns, "first_divergence_turn": first,
                                                  "finished": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))


if __name__ == "__main__":
    main()
