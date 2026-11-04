"""Multi-turn games played by a rule bot in both games (#232).

    python3 -m difftest.campaign START.SAV artifacts/run-exp-<name>/<run> --turns 5 --seed 12345 [--bot rulebot-1]

Each human turn: the bot decides from each game's OWN state, each game plays its own orders and End turn, and
the two states are compared (in full, and on the acting nation's own records). Orders that differ between the
games mean their visible states already differed. The original stays one process for the whole game (so its
random stream is continuous); the remake is continued from its native save each turn (checked equal to one
continuous session, 2026-10-28). Results: turns.jsonl (one line per turn, written as it goes) and summary.json.
A stopped game can be resumed with --resume (owner 2026-11-04, the 150-turn runs; needs IC2_LOG_RANDSEED=1, which logs
RandSeed after every checkpoint): the original reloads the last completed turn's final checkpoint and gets that RandSeed
written back (loading does not reseed, so its random stream continues exactly); the remake continues from that turn's
native save. Checkpoints and remake folders of the interrupted turn are moved to superseded-<stamp>/ (rule 6).
"""
import argparse
import importlib
import json
import shutil
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
    ap.add_argument("--resume", action="store_true", help="continue an interrupted game in OUT (see the module doc)")
    # Owner 2026-11-04, "we need to get to the later years": the original alone, played by the bot, every order and End
    # turn checkpointed as usual. No free-running remake: the comparison comes from `difftest.anchored`, which replays each
    # turn in the remake from the original's own state, and the checkpoints serve as late-year starts (difftest/late_starts.py).
    ap.add_argument("--original-only", action="store_true", help="play the original alone (no remake, no comparison)")
    # A continuation part after a human-seat handover (difftest/handover.py): START is the edited save, and this is the
    # RandSeed logged after the checkpoint it was made from, so the original's random stream continues.
    ap.add_argument("--start-randseed", type=int, default=None, help="RandSeed written after loading START")
    # Observation mode (owner 2026-11-04): the observation build, every nation played by the original's AI, one row per
    # round (End turn without orders). Implies --original-only.
    ap.add_argument("--observer", action="store_true", help="every nation AI-played (patches/observer_build.py)")
    a = ap.parse_args(argv)
    if a.observer:
        a.original_only = True
    from difftest import original, remake
    bot = importlib.import_module(a.bot)
    out = Path(a.out)
    rlog = lambda *x: None
    rdir = out / "remake"
    tag = f"C{out.name}-{time.strftime('%Y%m%d%H%M%S')}"
    if a.resume:
        o, so, native, sr, done, first = resume(out, a, rdir, tag, rlog)
    else:
        out.mkdir(parents=True, exist_ok=False)
        (out / "run.json").write_text(json.dumps({"start": a.start, "turns": a.turns, "seed": a.seed, "bot": bot.NAME,
                                                  "started": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))
        # The in-game save names must be unique per run (the tag once took the folder name's last 12 characters,
        # identical for every nation's "<nation>-rulebot1-5t", and the driver refused to overwrite, 2026-10-29).
        o = original.OriginalSession(a.start, out / "original", a.seed, tag, log=rlog, start_randseed=a.start_randseed,
                                     observer=a.observer)
        so = o.checkpoint("t00-start")
        if a.original_only:
            native, sr = None, None
        else:
            rdir.mkdir()
            remake.run([], a.start, rdir / "t00", log=rlog)
            native, sr = rdir / "t00" / "a000.native", load(rdir / "t00" / "a000.SAV")
        done, first = 0, None
    game_over = None
    try:
        for k in range(done + 1, a.turns + 1):
            nation = so["current_nation"]
            if a.original_only:
                oo = [] if a.observer else bot.decide(so)
                row = {"turn": k, "date_original": so["date"], "nation": NATIONS[nation], "orders_original": oo,
                       "orders_same": True, "differences": 0, "original_only": True, "observer": a.observer}
                replies = []
                for j, x in enumerate(oo + [end_action(bot, so)]):
                    texts, err = o.act(act.validate(x), f"t{k:02d}-a{j:02d}")
                    replies.append({"op": x["op"], "reply": texts, "error": err})
                so = o.state
                row["replies_original"] = replies
                with open(out / "turns.jsonl", "a") as f:
                    f.write(json.dumps(row, default=str) + "\n")
                print(f"turn {k} {row['nation']} {so['date']}: {len(oo)} orders (original only)", flush=True)
                if o.game_over:
                    print(f"turn {k}: END OF GAME in the original: {o.game_over}", flush=True)
                    game_over = {"turn": k, "text": o.game_over}
                    break
                continue
            oo, orr = bot.decide(so), bot.decide(sr)
            row = {"turn": k, "date_original": so["date"], "date_remake": sr["date"], "nation": NATIONS[nation],
                   "nation_remake": NATIONS[sr["current_nation"]], "orders_original": oo, "orders_remake": orr,
                   "orders_same": oo == orr}
            replies = []
            for j, x in enumerate(oo + [end_action(bot, so)]):
                texts, err = o.act(act.validate(x), f"t{k:02d}-a{j:02d}")
                replies.append({"op": x["op"], "reply": texts, "error": err})
            so = o.state
            names = act.checkpoint_names(orr + [end_action(bot, sr)])
            remake.run([act.validate(x) for x in orr + [end_action(bot, sr)]], native, rdir / f"t{k:02d}", log=rlog, template=a.start)
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
            if o.game_over:
                # End of Game in the original (the human overthrown or conquered): the game cannot go on, so the
                # campaign stops after this turn's row (the remake hands the nation to the AI instead).
                print(f"turn {k}: END OF GAME in the original: {o.game_over}", flush=True)
                game_over = {"turn": k, "text": o.game_over}
                break
    finally:
        o.close()
    (out / "summary.json").write_text(json.dumps({"turns": a.turns, "first_divergence_turn": first, "game_over": game_over,
                                                  "finished": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1))


def end_action(bot, s):
    """The bot's End turn (rulebot-2 accepts post-battle peace: {"op": "end_turn", "peace": true}); plain otherwise."""
    return bot.end_turn(s) if hasattr(bot, "end_turn") else {"op": "end_turn"}


def resume(out, a, rdir, tag, rlog):
    """Reopen an interrupted game: the last turn with a turns.jsonl row is complete in both games."""
    from difftest import original
    rows = [json.loads(l) for l in (out / "turns.jsonl").read_text().splitlines() if l.strip()] \
        if (out / "turns.jsonl").exists() else []
    done = rows[-1]["turn"] if rows else 0
    first = next((r["turn"] for r in rows if not r["orders_same"] or r["differences"]), None)
    odir = out / "original"
    rec = [json.loads(l) for l in (odir / "receipt.jsonl").read_text().splitlines() if l.strip()]
    if done:
        ckpt = sorted(odir.glob(f"t{done:02d}-a*.SAV"))[-1]
    else:
        ckpt = odir / "t00-start.SAV"
    after = [e for e in rec if e.get("kind") == "randseed_after" and e.get("checkpoint") == ckpt.stem]
    if not after:
        raise SystemExit(f"no randseed_after for {ckpt.name}: the game was not run with IC2_LOG_RANDSEED=1, so it cannot be "
                         "resumed exactly")
    # Anything of the interrupted turn is kept aside, never overwritten (rule 6).
    stamp = time.strftime("%Y%m%d-%H%M%S")
    partial = [f for f in odir.glob(f"t{done + 1:02d}-a*") ] + ([rdir / f"t{done + 1:02d}"] if (rdir / f"t{done + 1:02d}").exists() else [])
    if partial:
        aside = out / f"superseded-{stamp}"
        aside.mkdir()
        for f in partial:
            shutil.move(str(f), aside / f"{f.parent.name}-{f.name}")
    with open(out / "resumes.jsonl", "a") as f:
        f.write(json.dumps({"time": stamp, "after_turn": done, "checkpoint": ckpt.name, "randseed": after[-1]["value"],
                            "moved_aside": [str(p.name) for p in partial]}) + "\n")
    o = original.OriginalSession(ckpt, odir, a.seed, tag, log=rlog, resume_randseed=after[-1]["value"],
                                 observer=getattr(a, "observer", False))
    so = load(ckpt)
    o.state = so
    if a.original_only:
        rlast, sr = None, None
    else:
        rlast = sorted((rdir / f"t{done:02d}").glob("a*.native"))[-1]
        sr = load(rlast.with_suffix(".SAV"))
    print(f"resumed after turn {done} from {ckpt.name} (RandSeed {after[-1]['value']}) and {rlast}", flush=True)
    return o, so, rlast, sr, done, first


if __name__ == "__main__":
    main()
