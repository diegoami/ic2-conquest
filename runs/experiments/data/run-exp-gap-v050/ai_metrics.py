"""The AI, measured the same way on both sides from idle-Rome games (the human seat only ends turns).

ORIGINAL: the autosaves of run-exp-ai-intercept-hunt (start saves/run0-start-AUTO0720-seed12345.SAV, Rome human; the plain seed exe, or the
inert hook build whose autosaves are byte-identical to it): seeds 12345 (plain, 25 End turns), 2 (plain, 40), 10 (hook, 40), 14 (hook, 39);
read with state/sav.py. Game length (the turn the idle Rome is conquered) also from run-exp-ai-conquest-aboard/idle_watch_seed*.jsonl.
REMAKE v0.5.0: artifacts/run-exp-gap-v050/ai_rome_s<seed>_t<turn>.sav (CLI, classical-mediterranean = classical-faithful, seat rome, seeds
1 2 3 10 11 12 14 12345, 80 End turns), read as JSON.

Per (engine, seed, turn): cities per nation, nations alive, AI armies / troops / units, AI recruitment slots and their troops, AI
mobilisation, AI fortification increases (a city keeping its owner whose fortification code rose since the previous save), city owner
changes, wars (pairs at relation 3), the news lines new since the previous save classified (falls to / fails to capture / defects /
declares war / peace / alliance / trade / destroys army / sinks fleet / conquers / other), and the pending offer to the human.
Writes ai_metrics_turns.jsonl and ai_metrics_summary.json (new files, versioned; never overwritten).
python3 ai_metrics.py"""
import json, re, sys
from collections import Counter
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R))
from state import sav
DATA = R / "runs/experiments/data/run-exp-gap-v050"
OA, RA = R / "artifacts/run-exp-ai-intercept-hunt", R / "artifacts/run-exp-gap-v050"
NAMES = ["Rome", "Carthage", "Seleucid", "Ptolemaic", "Macedonia", "Numidia", "Gaul", "Greece", "Celtiberia", "Illyria", "Dacia",
         "Bithynia", "Galatia", "Armenia", "Media", "Thracia"]
KINDS = [("falls", r" falls to "), ("fails_capture", r" fails to capture "), ("defects", r" defects from "), ("declares_war", r" declares war on "),
         ("peace", r"(end their war|peace)"), ("alliance", r"alliance"), ("trade", r"trade"), ("destroys_army", r" destroys army of "),
         ("sinks_fleet", r" sinks fleet of "), ("conquers", r" conquers "), ("rebels", r"rebel"), ("deposed", r"(depos|overthrow)"),
         ("storm", r"storm")]


def classify(line):
    for k, p in KINDS:
        if re.search(p, line, re.I): return k
    return "header" if re.match(r"\s*(Week|\d+ BC)", line) or not line.strip() else "other"


def new_lines(prev, cur):
    """The lines of `cur` after its overlap with the end of `prev` (both oldest first; rolling windows)."""
    if prev is None: return cur
    for o in range(len(prev) + 1):
        k = len(prev) - o
        if cur[:k] == prev[o:]: return cur[k:]
    return cur


def orig_state(p):
    s = sav.load(str(p))
    cities = {i: (c["owner"], c["fort"]) for i, c in enumerate(s["cities"])}
    arm = [a for a in s["armies"] if a["troops"] > 0]
    rel = sum(1 for i, n in enumerate(s["nations"]) for j, v in enumerate(n["relations"].values()) if v == 3) // 2
    nat = {n["name"]: n for n in s["nations"]}
    return {"cities": {k: (NAMES[o] if 0 <= o < 16 else None, f) for k, (o, f) in cities.items()},
            "armies": [(NAMES[a["owner"]], a["troops"], len(a["units"])) for a in arm],
            "slots": {n: [(x["type"], x["troops"]) for x in nat[n]["recruit_slots"]] for n in NAMES},
            "mob": {n: nat[n]["mobilization"] for n in NAMES}, "wars": rel, "news": s["news"],
            "human_offer": s["pending_offer"] if s["pending_offer"].get("from", -1) >= 0 else None,
            "date": s.get("date")}


def remake_state(p):
    s = json.load(open(p))["save"]["state"]
    nm = {n["id"]: n["name"] for n in s["nations"]}
    cities = {c["id"]: (nm.get(c["owner"]), c["fortificationCode"]) for c in s["cities"]}
    arm = [a for a in s["armies"] if sum(u["troops"] for u in a["units"]) > 0]
    m = s["relations"]["matrix"]
    wars = sum(1 for i in range(len(m)) for j in range(i + 1, len(m)) if m[i][j] == 3)
    sl = s["newsLog"]["slots"]; k = s["newsLog"]["mostRecentSlot"]
    news = [x["text"] for x in (sl[k + 1:] + sl[:k + 1] if len(sl) == 40 else sl)]
    return {"cities": cities, "armies": [(nm[a["nation"]], sum(u["troops"] for u in a["units"]), len(a["units"])) for a in arm],
            "slots": {n["name"]: [(x.get("unitTypeId"), x.get("troops")) for x in n["recruitmentSlots"]] for n in s["nations"]},
            "mob": {n["name"]: n["mobilizedPercent"] for n in s["nations"]}, "wars": wars, "news": news,
            "human_offer": s["pendingOffer"], "date": s["calendar"]}


def runs():
    for seed, kind, n in ((12345, "plain", 25), (2, "plain", 40), (10, "hook", 40), (14, "hook", 39)):
        files = [R / "saves/run0-start-AUTO0720-seed12345.SAV"] + [OA / f"{kind}_s{seed}_AUTO{720 + t:04d}.SAV" for t in range(1, n + 1)]
        yield "original", seed, [f for f in files if f.exists()], orig_state
    for seed in (1, 2, 3, 10, 11, 12, 14, 12345):
        files = [RA / f"ai_rome_s{seed}_t{t:03d}.sav" for t in range(0, 81)]
        yield "remake", seed, [f for f in files if f.exists()], remake_state


def main():
    rows, summ = [], {}
    for eng, seed, files, read in runs():
        prev, tot = None, Counter()
        rome_gone = None
        for t, f in enumerate(files):
            st = read(f)
            owners = Counter(o for o, _ in st["cities"].values() if o)
            ai_arm = [a for a in st["armies"] if a[0] != "Rome"]
            row = {"engine": eng, "seed": seed, "turn": t, "file": f.name, "date": st["date"],
                   "rome_cities": owners.get("Rome", 0), "nations_alive": len(owners), "ai_armies": len(ai_arm),
                   "ai_troops": sum(a[1] for a in ai_arm), "ai_units": sum(a[2] for a in ai_arm),
                   "ai_slots": sum(len(v) for n, v in st["slots"].items() if n != "Rome"),
                   "ai_slot_troops": sum((x[1] or 0) for n, v in st["slots"].items() if n != "Rome" for x in v),
                   "ai_mob_mean": round(sum(v for n, v in st["mob"].items() if n != "Rome") / 15, 1), "wars": st["wars"],
                   "human_offer": st["human_offer"]}
            if prev:
                row["owner_changes"] = sum(1 for k, (o, _) in st["cities"].items() if prev["cities"].get(k, (o,))[0] != o)
                row["ai_fortify_rises"] = sum(1 for k, (o, fc) in st["cities"].items()
                                              if o and o != "Rome" and prev["cities"].get(k, (None, None))[0] == o and fc % 100 > prev["cities"][k][1] % 100)
                nl = new_lines(prev["news"], st["news"])
                row["news"] = dict(Counter(classify(x) for x in nl if classify(x) != "header"))
                tot.update(row["news"]); tot["owner_changes"] += row["owner_changes"]; tot["ai_fortify_rises"] += row["ai_fortify_rises"]
                tot["turns_with_human_offer"] += bool(st["human_offer"])
            if rome_gone is None and row["rome_cities"] == 0: rome_gone = t
            rows.append(row); prev = st
        last = rows[-1]
        summ[f"{eng}_s{seed}"] = {"turns": len(files) - 1, "rome_conquered_at": rome_gone, "end": {k: last[k] for k in (
            "rome_cities", "nations_alive", "ai_armies", "ai_troops", "ai_slots", "ai_slot_troops", "ai_mob_mean", "wars")},
            "start": {k: rows[-len(files)][k] for k in ("rome_cities", "nations_alive", "ai_armies", "ai_troops", "ai_slots", "ai_mob_mean", "wars")},
            "totals": dict(tot)}
    # the original's game lengths from the idle-watch runs
    lengths = {}
    for p in sorted((R / "runs/experiments/data/run-exp-ai-conquest-aboard").glob("idle_watch_seed*.jsonl")):
        for l in p.read_text().splitlines():
            d = json.loads(l)
            if "game_over" in d: lengths[d["seed"]] = d["end"]
    summ["original_idle_rome_game_over_end_turn"] = lengths
    def new(name):
        p = DATA / name; k = 1
        while p.exists(): k += 1; p = DATA / (Path(name).stem + f".v{k}" + Path(name).suffix)
        return p
    p1 = new("ai_metrics_turns.jsonl"); p1.write_text("".join(json.dumps(r, default=str) + "\n" for r in rows))
    p2 = new("ai_metrics_summary.json"); p2.write_text(json.dumps(summ, indent=1, default=str))
    print(p1.name, p2.name)


if __name__ == "__main__":
    main()
