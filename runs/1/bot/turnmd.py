"""Run 1 helper: write runs/1/turns/<turn>.md from the bot's notes and the turn's result.json + next autosave.

    python3 runs/1/bot/turnmd.py <turn> <notes.md>

notes.md holds the hand-written part (intent, strategy step / principles, expected, surprises); this script appends the
orders as issued (with their verified effect), the battles, and the facts of the next save (Rome's cities, armies,
treasury, unity, mobilization, trades) so expected vs actual can be read side by side.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from state import sav  # noqa: E402
import strength  # noqa: E402
import turn as T  # noqa: E402

RUN = ROOT / "runs" / "1"


def brief(o):
    keep = {k: v for k, v in o.items() if k not in ("order", "attempts", "army_before", "army_after", "new_armies", "path", "texts")}
    if o.get("texts"):
        keep["boxes"] = [t for t in o["texts"]]
    return keep


def unit_str(a):
    return ", ".join("%s %d q%d%s" % (u["type"].upper(), u["troops"], u["quality"], " merc" if u["merc"] else "") for u in a["units"])


def battles_md(res):
    out = []
    for k, b in enumerate(res.get("battles", []), 1):
        if "before" not in b:
            out.append("- battle %d: not logged (%s)" % (k, b.get("error_before")))
            continue
        att, dfn = str(b["attacker"]), str(b["defender"])
        a0, d0 = b["before"][att], b["before"][dfn]
        a1, d1 = b["after"][att], b["after"][dfn]
        gone = lambda x: x["owner"] < 0 or x["troops"] <= 0
        pa, pd, ratio, raw = strength.ratio(a0, d0) if a0["owner"] == 0 else strength.ratio(d0, a0)
        out.append("- **Battle %d** (%s): attacker army %s (%s, %d troops, morale %d) vs defender army %s (%s, %d troops, morale %d)." % (
            k, b.get("windows", [""])[0].strip(), att, sav.NATIONS[a0["owner"]], a0["troops"], a0["morale"], dfn,
            sav.NATIONS[d0["owner"]], d0["troops"], d0["morale"]))
        out.append("  - attacker before: %s" % unit_str(a0))
        out.append("  - defender before: %s" % unit_str(d0))
        out.append("  - attacker after: %s" % ("destroyed" if gone(a1) else "%d troops: %s" % (a1["troops"], unit_str(a1))))
        out.append("  - defender after: %s" % ("destroyed" if gone(d1) else "%d troops: %s" % (d1["troops"], unit_str(d1))))
        out.append("  - P1 (Rome's side first): S %d vs %d, ratio %.2f; raw troop ratio %.2f" % (pa, pd, ratio, raw))
        if b.get("shot") and Path(b["shot"]).exists():
            out.append("  - shot: `%s`" % Path(b["shot"]).name)
    return out


def main(turn, notes):
    res = json.loads((RUN / "turns" / ("%04d.result.json" % turn)).read_text())
    nxt = T.save_path(turn + 1)
    s = sav.load(nxt)
    rome = s["nations"][0]
    lines = [Path(notes).read_text().rstrip(), "", "## Orders as issued (verified from game memory)", ""]
    lines.append("Loaded `%s` (SHA-256 `%s…`), seed %d (`%s`). Boxes at load: %s." % (
        res["save"], res["save_sha256"][:16], res["seed"], res.get("seed_line", ""), res.get("load_popups") or "none"))
    lines.append("")
    lines.append("| # | Order | Result | Detail |")
    lines.append("|---|---|---|---|")
    for k, o in enumerate(res["orders"], 1):
        lines.append("| %d | `%s` | %s | %s |" % (k, json.dumps(o["order"]), o["ok"], json.dumps(brief(o), default=str).replace("|", "/")))
    lines.append("")
    lines.append("End turn boxes: %s." % (res.get("end_turn_texts") or "none"))
    bm = battles_md(res)
    if bm:
        lines += ["", "## Battles", ""] + bm
    lines += ["", "## The next save: `%s` (turn %04d, %s), SHA-256 `%s…`" % (nxt.name, s["turn"], s["date"], res["autosave_sha256"][:16]), ""]
    lines.append("- Rome: %d cities, treasury %d, unity %d, mobilization %d, tax %d %%; trades with %s." % (
        len(sav.owned_cities(s, 0)), rome["treasury"], rome["unity"], rome["mobilization"], rome["tax"],
        ", ".join(k for k, v in rome["relations"].items() if v == 1) or "nobody"))
    for a in sav.live_armies(s, 0):
        lines.append("- Roman army %d at (%d,%d): %d troops, supplies %d/%d, morale %d, purse %d: %s" % (
            a["id"], a["x"], a["y"], a["troops"], a["supplies"], a["troops"] // 100 + 1, a["morale"], a["money"], unit_str(a)))
    lines.append("- Recruitment queue: %s" % ", ".join("%s %d @%d s%d" % (q["type"].upper(), q["troops"], q["city"], q["state"]) for q in rome["recruit_slots"]))
    g = s["nations"][6]
    lines.append("- Gaul: %d cities, %d armies (%d troops), unity %d." % (
        len(sav.owned_cities(s, 6)), len(sav.live_armies(s, 6)), sum(a["troops"] for a in sav.live_armies(s, 6)), g["unity"]))
    news = [n.strip() for n in s["news"] if "Rome" in n or "Gaul" in n]
    if news:
        lines.append("- News naming Rome or Gaul (last 40 lines): " + "; ".join(news[-8:]))
    lines.append("- Artifacts (`artifacts/run-1/`, hashes in `runs/1/SAVES.sha256`): " + ", ".join("`%s`" % p for p in res["artifacts"]))
    (RUN / "turns" / ("%04d.md" % turn)).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2])
