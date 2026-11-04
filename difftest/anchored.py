"""Anchored replay of a long campaign: the remake re-plays every turn from the ORIGINAL's own state (long runs, v0.9.0).

    python3 -m difftest.anchored CAMPAIGN_DIR [--pin <short>] [--follow]

CAMPAIGN_DIR is a difftest/campaign.py run. For turn k, the remake imports the original's checkpoint from the start
of the turn (t00-start.SAV, else the last checkpoint of turn k-1, which follows its End turn), plays the ORIGINAL's
orders for that turn plus End turn, and its export is compared with the original's checkpoints: the one before End
turn ("human" phase: our orders only) and the one after End turn ("ai" phase: the AI seats, events and random draws
of one turn). So a difference never carries over from an earlier turn, as it does in the free-running campaign.

Per turn, `anchored/turns.jsonl` gets one line (appended; a turn already there is skipped, so a stopped run resumes):
the field and map differences of both phases, and per nation what differs (its nation record, the cities it owns in
either game, its armies and fleets as multisets of (x, y, size)). `--follow` waits for the campaign's next turn
until its summary.json appears.
"""
import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from difftest import actions as act  # noqa: E402
from difftest import pin  # noqa: E402
from difftest.compare import NATION_KEYS, compare, live_armies, live_fleets  # noqa: E402
from state.sav import NATIONS, load  # noqa: E402


def army_key(a):
    return (a["x"], a["y"], a["troops"], tuple(sorted((u["type"], u["troops"]) for u in a["units"])))


def fleet_key(f):
    return (f["x"], f["y"], f["ships"])


def per_nation(a, b):
    """{nation: what differs} for every nation whose own records differ between the parsed saves a and b."""
    out = {}
    for n in range(len(NATIONS)):
        name, d = NATIONS[n], {}
        na, nb = a["nations"][n], b["nations"][n]
        nf = [k for k in NATION_KEYS if json.dumps(na[k], default=str) != json.dumps(nb[k], default=str)]
        if nf:
            d["nation"] = {k: [na[k], nb[k]] for k in nf}
        ca = {c["id"]: c for c in a["cities"]}
        cb = {c["id"]: c for c in b["cities"]}
        owned = {i for i, c in ca.items() if c["owner"] == n} | {i for i, c in cb.items() if c["owner"] == n}
        cd = {i: [k for k in ca[i] if k != "id" and ca[i][k] != cb[i].get(k)] for i in sorted(owned)}
        cd = {i: ks for i, ks in cd.items() if ks}
        if cd:
            d["cities"] = cd
        for kind, live, key in (("armies", live_armies, army_key), ("fleets", live_fleets, fleet_key)):
            xa = Counter(key(r) for r in live(a) if r["owner"] == n)
            xb = Counter(key(r) for r in live(b) if r["owner"] == n)
            if xa != xb:
                d[kind] = {"only_original": sorted((xa - xb).elements())[:12], "only_remake": sorted((xb - xa).elements())[:12],
                           "count": [sum(xa.values()), sum(xb.values())]}
        if d:
            out[name] = d
    return out


def end_checkpoint(orig, k):
    """The original's last checkpoint of turn k (after its End turn), or None while the turn is not finished."""
    names = sorted(orig.glob(f"t{k:02d}-a*.SAV"))
    return names[-1] if names else None


def replay_turn(camp, k, row, out, log, seed=None, attempt=1):
    orig = camp / "original"
    start = orig / "t00-start.SAV" if k == 1 else end_checkpoint(orig, k - 1)
    acts = [act.validate(x) for x in row["orders_original"]] + [{"op": "end_turn"}]
    o_human = orig / f"t{k:02d}-a{len(acts) - 2:02d}.SAV" if len(acts) > 1 else start
    o_ai = orig / f"t{k:02d}-a{len(acts) - 1:02d}.SAV"
    from difftest import remake
    rdir = out / (f"t{k:02d}" if attempt == 1 else f"t{k:02d}-r{attempt}")
    t0 = time.time()
    try:
        replies = remake.run(acts, start, rdir, log=lambda *x: None, seed=seed)
    except Exception as e:  # recorded, never retried blind: the receipt and stderr stay in rdir
        return {"turn": k, "error": str(e)[-1500:]}
    names = act.checkpoint_names(acts)
    so_h, so_a = load(o_human), load(o_ai)
    sr_h, sr_a = load(rdir / f"{names[-2]}.SAV"), load(rdir / f"{names[-1]}.SAV")
    dh, da = compare(so_h, sr_h), compare(so_a, sr_a)
    return {"turn": k, "date": so_a["date"], "nation": row["nation"], "orders": len(acts) - 1,
            "remake_errors": [r for r in replies if r.get("error")],
            "human": {"fields": len(dh["fields"]), "map": dh["map"]["count"], "first": dh["fields"][:15],
                      "nations": per_nation(so_h, sr_h)},
            "ai": {"fields": len(da["fields"]), "map": da["map"]["count"], "first_map": da["map"]["first"][:10],
                   "nations": per_nation(so_a, sr_a)},
            "seconds": round(time.time() - t0, 1)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("campaign")
    ap.add_argument("--pin")
    ap.add_argument("--follow", action="store_true")
    ap.add_argument("--out", default="anchored", help="folder inside the campaign (a recheck on a new pin: anchored-<short>)")
    # The importer gives every imported save the scenario's fixed RandomSeed and TurnIndex 0, so without a seed every anchored
    # turn draws the same per-nation streams: a roll that hits once hits in every turn (2026-11-03, Seleucid's war on Armenia
    # in numidia turns 9-11). --turn-seed B gives turn k the seed B + k, so the turns' draws are independent.
    ap.add_argument("--turn-seed", type=int, default=None, help="base seed: turn k is replayed with seed BASE + k")
    # A turn whose replay failed for the environment's sake (2026-11-04: "Out of memory", exit -6, while other jobs ran) is
    # replayed again into t<k>-r<n>; the error row and its folder are kept (rule 6) and the new row is appended.
    ap.add_argument("--retry-errors", action="store_true", help="replay again only the turns whose rows are all errors")
    a = ap.parse_args(argv)
    if a.pin:
        os.environ.update(pin.env(a.pin))
    camp = Path(a.campaign)
    out = camp / a.out
    out.mkdir(exist_ok=True)
    tj = out / "turns.jsonl"
    prior = [json.loads(l) for l in tj.read_text().splitlines() if l.strip()] if tj.exists() else []
    done = {r["turn"] for r in prior}
    if a.retry_errors:
        good = {r["turn"] for r in prior if "error" not in r}
        for k in sorted(done - good):
            r = next(x for x in [json.loads(l) for l in (camp / "turns.jsonl").read_text().splitlines() if l.strip()] if x["turn"] == k)
            attempt = 1 + sum(1 for x in prior if x["turn"] == k)
            res = replay_turn(camp, k, r, out, print, seed=None if a.turn_seed is None else a.turn_seed + k, attempt=attempt)
            res["attempt"] = attempt
            with open(tj, "a") as f:
                f.write(json.dumps(res, default=str) + "\n")
            print(f"turn {k} attempt {attempt}: {'ERROR ' + res['error'][:200] if 'error' in res else 'ok'}", flush=True)
        return
    while True:
        rows = [json.loads(l) for l in (camp / "turns.jsonl").read_text().splitlines() if l.strip()] \
            if (camp / "turns.jsonl").exists() else []
        todo = [r for r in rows if r["turn"] not in done and end_checkpoint(camp / "original", r["turn"])]
        for r in todo:
            res = replay_turn(camp, r["turn"], r, out, print,
                              seed=None if a.turn_seed is None else a.turn_seed + r["turn"])
            with open(tj, "a") as f:
                f.write(json.dumps(res, default=str) + "\n")
            done.add(r["turn"])
            if "error" in res:
                print(f"turn {r['turn']}: remake ERROR {res['error'][:200]}", flush=True)
            else:
                print(f"turn {r['turn']} {res['date']}: human {res['human']['fields']} fields; ai {res['ai']['fields']} fields, "
                      f"{res['ai']['map']} map cells, nations {sorted(res['ai']['nations'])}", flush=True)
        if not a.follow or (camp / "summary.json").exists() and not todo:
            break
        time.sleep(30)


if __name__ == "__main__":
    main()
