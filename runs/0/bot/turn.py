"""Run 0 turn runner: play one turn from its autosave in a fresh game process.

    python3 runs/0/bot/turn.py <turn> <orders.json>

- loads AUTO<turn>.SAV (0720: saves/run0-start-AUTO0720-seed12345.SAV) with seed 12345 + (turn - 720);
- takes a full-screen shot at the turn start, issues the orders (each verified from game memory, retried at most twice
  when its effect is absent), takes a shot after the orders, snapshots every army, ends the turn (battles with Computer
  general, each battle's two armies logged before and after), waits for AUTO<turn+1>.SAV;
- copies the new autosave, AUTOSAVE.LOG, SEED.LOG and the shots to ART/<season>/ under unique names (never overwrites),
  appends their SHA-256 to runs/0/SAVES.sha256, records metrics/armies/state for the new save, and writes
  runs/0/turns/<turn>.result.json (the order log, popups, battles).

Order ops (orders.json is a list):
  {"op": "recruit", "row": 1, "city": 85, "type": "hi", "troops": 6000}
  {"op": "fortify", "name": "Arretium", "x": 99, "y": 36, "points": 3}
  {"op": "mercs", "army": 1, "rows": [0]}
  {"op": "supply", "army": 0, "tons": null, "money_100s": 0}
  {"op": "move", "army": 1, "x": 113, "y": 45}
  {"op": "join", "army": 1}
  {"op": "mobilize", "row": 1, "city": 85, "units": [0, 1]}
  {"op": "relation", "nation": 3, "kind": "trade"}
  {"op": "attack", "army": 0, "x": 93, "y": 28}
  {"op": "taxation", "percent": 10}
  {"op": "split", "army": 0, "rows": [0]}
"""
import hashlib
import json
import shutil
import struct
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from harness.driver import MAP, ARMIES, ARMY_LEN, BATTLE_HEADER, G, NATIONS, NATION_LEN, CUR_NATION, DriverError, Game  # noqa: E402
from state import metrics, sav  # noqa: E402

RUN = ROOT / "runs" / "0"
ART = Path("/home/user/ic2-conquest/artifacts/run-0")
START = ROOT / "saves" / "run0-start-AUTO0720-seed12345.SAV"
SEASONS = ["spring", "summer", "autumn", "winter"]
DEFAULT = {"li": 3000, "hi": 1200, "ar": 700, "lc": 1400, "hc": 500}   # battalion / 5, the dialog's default amount


def season_dir(turn):
    return ART / ("%dBC-%s" % (300 - turn // 24, SEASONS[(turn % 24) // 6]))


def save_path(turn):
    if turn == 720:
        return START
    return season_dir(turn) / ("AUTO%04d.SAV" % turn)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def keep(src, dst):
    """Copy src to dst; never overwrite: an existing different file gets a .v<N> name beside it."""
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.read_bytes() == Path(src).read_bytes():
            return dst
        n = 2
        while dst.with_name("%s.v%d%s" % (dst.stem, n, dst.suffix)).exists():
            n += 1
        dst = dst.with_name("%s.v%d%s" % (dst.stem, n, dst.suffix))
    shutil.copy(src, dst)
    return dst


def record_hash(p):
    line = "%s  %s\n" % (sha(p), Path(p).relative_to(ART))
    f = RUN / "SAVES.sha256"
    old = f.read_text() if f.exists() else ""
    if line not in old:
        f.write_text(old + line)


class RunGame(Game):
    """Game with a battle log: every battle played (attack order or AI attack during End turn) records both armies
    from memory before and after."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.battles = []
        self.shot_dir, self.turn_no = None, 0
        self.last_new = None

    def all_armies(self, n_max=200):
        out = {}
        for i in range(n_max):
            r = self.mem(ARMIES + i * ARMY_LEN, ARMY_LEN)
            a = sav.parse_army(r, i)
            if a["owner"] >= 0 and a["troops"] > 0:
                out[i] = a
        return out

    def play_battle(self, shot=None, **kw):
        rec = {"time": time.strftime("%H:%M:%S")}
        try:
            att = struct.unpack("<h", self.mem(BATTLE_HEADER["attacker_army"], 2))[0]
            dfn = struct.unpack("<h", self.mem(BATTLE_HEADER["defender_army"], 2))[0]
            rec["attacker"], rec["defender"] = att, dfn
            rec["before"] = {str(att): self.army_state(att), str(dfn): self.army_state(dfn)}
            rec["windows"] = [w[1] for w in self.find_windows(" v ")]
        except Exception as e:      # the log must never stop the battle
            rec["error_before"] = repr(e)
        if self.shot_dir:
            shot = self.shot_dir / ("battle-%04d-%d-%s.png" % (self.turn_no, len(self.battles) + 1, time.strftime("%H%M%S")))
            rec["shot"] = str(shot)
        res = super().play_battle(shot, **kw)
        try:
            rec["after"] = {k: self.army_state(int(k)) for k in rec.get("before", {})}
            rec["result"] = res
        except Exception as e:
            rec["error_after"] = repr(e)
        self.battles.append(rec)
        return res

    def list_rows_ocr(self, c):
        """The visible rows of list box control c, read by OCR (the list's items are not readable through win_controls).
        Returns [(row index, text)]."""
        import subprocess
        png = Path(G).parent.parent.parent / "shots" / "_list.png"
        png.parent.mkdir(parents=True, exist_ok=True)
        self.shot(png)
        big = png.with_name("_list_big.png")
        subprocess.run(["convert", str(png), "-crop", "%dx%d+%d+%d" % (c["w"] - 4, c["h"] - 4, c["cx"], c["cy"]),
                        "-scale", "400%", "-colorspace", "Gray", "-negate", "-threshold", "50%", "-negate", str(big)], check=True)
        out = subprocess.run(["tesseract", str(big), "-", "--psm", "6"], capture_output=True, text=True).stdout
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        return [(c["top"] + k, t) for k, t in enumerate(lines)]

    def city_row(self, name):
        """Row of city `name` in the Army recruits dialog's city list (the dialog must be open). The list starts with
        "All cities" once more than one city holds queued units, so a fixed row index is not safe."""
        import subprocess
        cs = self.controls("Army recruits")
        lb = self.control(cs, cls="TListBox", index=0)
        ul = self.control(cs, cls="TListBox", index=1)
        n_vis = (lb["h"] - 4) // lb["item_h"]
        seen = []
        key = name.lower().replace(" ", "")[:5]
        png = Path(G).parent.parent.parent / "shots" / "_caption.png"
        png.parent.mkdir(parents=True, exist_ok=True)
        for r in range(lb["top"], lb["top"] + n_vis):
            self.click_list_row(lb, r, pause=0.6)
            self.shot(png)
            big = png.with_name("_caption_big.png")
            # the group box caption "Units at <City>" sits just above the units list ("All cities" shows the capital in the
            # "Create unit at" caption, so that one cannot tell the two rows apart)
            subprocess.run(["convert", str(png), "-crop", "%dx%d+%d+%d" % (ul["w"], 18, ul["x"], ul["y"] - 20),
                            "-scale", "400%", str(big)], check=True)
            txt = " ".join(subprocess.run(["tesseract", str(big), "-", "--psm", "7"], capture_output=True, text=True).stdout.split())
            seen.append((r, txt))
            city = txt.lower().split(" at ")[-1].replace(" ", "")
            if city.startswith(key):
                return r, seen
        raise DriverError("city %r not found in the recruit list (captions %s)" % (name, seen))

    # ---- memory helpers ----
    def rome(self):
        return self.nation_state(0)

    def roman_armies(self):
        return {i: a for i, a in self.all_armies().items() if a["owner"] == 0}


def do_order(g, o, log):
    op = o["op"]
    if o.get("army") == "new":
        o = dict(o, army=g.last_new)
    r = {"order": o, "attempts": 0, "ok": False, "texts": []}
    if o.get("army", 0) is None:
        r["skipped"] = "no army (the order that should have made it failed)"
        log("order %s skipped: %s" % (op, r["skipped"]))
        return r
    if "city_name" in o and op in ("recruit", "mobilize"):
        try:
            g.open_recruit()
            o = dict(o, row=g.city_row(o["city_name"])[0])
            g.close_controls("Army recruits", g.controls("Army recruits"))
            r["order"] = o
        except Exception as e:
            r["errors"] = [repr(e)]
            log("order %s: city row lookup failed: %r" % (op, e))
            try:
                g.dismiss_popups()
                g.close_controls("Army recruits", g.controls("Army recruits"))
            except Exception:
                pass
            return r
    for attempt in range(3):
        r["attempts"] += 1
        try:
            if op == "recruit":
                before = g.rome()["recruit_slots"]
                d = o["troops"] - DEFAULT[o["type"]]
                texts = g.recruit(o["row"], o["type"], thousands=d // 1000, hundreds=(d % 1000) // 100)
                r["texts"] += texts
                after = g.rome()["recruit_slots"]
                new = [q for q in after if q not in before]
                r["new_slots"] = new
                r["treasury"] = g.rome()["treasury"]
                if new:
                    r["ok"] = all(q["type"] == o["type"] and q["troops"] == o["troops"] and q["city"] == o["city"] for q in new)
                    break               # never retry once a slot was added (a retry would add a second one)
                if texts:
                    break               # a refusal box: retrying will not change it
            elif op == "fortify":
                t0 = g.rome()["treasury"]
                r["texts"] += g.fortify(o["name"], o["x"], o["y"], o["points"])
                t1 = g.rome()["treasury"]
                r["cost"] = t0 - t1
                if t1 < t0:
                    r["ok"] = True
                    break
                if r["texts"]:
                    break
            elif op == "mercs":
                gained, texts = g.hire_mercs(o["army"], rows=tuple(o.get("rows", [0])))
                r["texts"] += texts
                r["gained"] = gained
                if gained:
                    r["ok"] = True
                    break
                if texts:
                    break
            elif op == "supply":
                have = g.army_state(o["army"])
                got, texts = g.supply(o["army"], tons=o.get("tons"), money_100s=o.get("money_100s", 0))
                r["texts"] += texts
                after = g.army_state(o["army"])
                r["supplies"] = (have["supplies"], after["supplies"])
                r["money"] = (have["money"], after["money"])
                if got > 0 or after["money"] != have["money"] or after["supplies"] >= after["troops"] // 100:
                    r["ok"] = True
                    break
            elif op == "move":
                p0 = g.army_pos(o["army"])
                pos, texts = g.move(o["army"], o["x"], o["y"])
                r["texts"] += texts
                r["from"], r["to"] = p0, pos
                r["moves_left"] = g.army_state(o["army"])["moves"]
                if tuple(pos) == (o["x"], o["y"]):
                    r["ok"] = True
                    break
                if tuple(pos) != tuple(p0):
                    r["ok"] = "partial"
                    break
            elif op == "goto":
                # a cheapest path (planner/path.py on the live map) cut into straight legs; stops where the moves run out
                from planner import path as P
                m = {"map": struct.unpack("<%dh" % (320 * 140), g.mem(MAP, 320 * 140 * 2))}
                a = g.army_state(o["army"])
                start = (a["x"], a["y"])
                r.setdefault("from", start)
                if "adjacent_to" in o:
                    tx, ty = o["adjacent_to"]
                    if max(abs(start[0] - tx), abs(start[1] - ty)) == 1:
                        r["ok"], r["to"] = True, start
                        break
                    cost, pth = P.path_adjacent(m, start, (tx, ty))
                else:
                    if start == (o["x"], o["y"]):
                        r["ok"], r["to"] = True, start
                        break
                    cost, pth = P.path_to(m, start, (o["x"], o["y"]))
                if not pth:
                    r["error"] = "no path"
                    break
                reach, spent = P.turn_legs(m, pth, a["moves"] - o.get("keep_moves", 0))
                r["path"], r["path_cost"], r["reach_this_turn"] = pth, cost, reach[-1]
                wps = []
                for k in range(1, len(reach)):
                    d = (reach[k][0] - reach[k - 1][0], reach[k][1] - reach[k - 1][1])
                    if k == len(reach) - 1 or (reach[k + 1][0] - reach[k][0], reach[k + 1][1] - reach[k][1]) != d:
                        wps.append(reach[k])
                pos = start
                for wp in wps:
                    pos, texts = g.move(o["army"], *wp)
                    r["texts"] += texts
                    if tuple(pos) != tuple(wp):
                        break
                r["to"] = tuple(pos)
                r["moves_left"] = g.army_state(o["army"])["moves"]
                if tuple(pos) == tuple(pth[-1]):
                    r["ok"] = True
                    break
                if tuple(pos) == tuple(reach[-1]):
                    r["ok"] = "partial (moves ran out)"
                    break
            elif op == "join":
                before = {i: a["troops"] for i, a in g.roman_armies().items()}
                r["texts"] += g.join(o["army"])
                after = {i: a["troops"] for i, a in g.roman_armies().items()}
                r["armies"] = (before, after)
                if len(after) < len(before):
                    r["ok"] = True
                    break
                if r["texts"]:
                    break
            elif op == "mobilize":
                before = set(g.roman_armies())
                r["texts"] += g.mobilize(o["row"], o["units"])
                after = g.roman_armies()
                new = sorted(set(after) - before)
                r["new_armies"] = {i: after[i] for i in new}
                if new:
                    g.last_new = new[-1]
                    r["ok"] = True
                    break
                if r["texts"]:
                    break
            elif op == "relation":
                rel = g.rome()["relations"]
                if o.get("only_if_free_trade_slot") and sum(1 for v in rel.values() if v == 1) >= 3:
                    r["skipped"] = "3 trade slots already filled"
                    r["ok"] = "skipped"
                    break
                if o["kind"] == "trade" and rel.get(sav.NATIONS[o["nation"]]) == 1:
                    r["skipped"] = "already trading"
                    r["ok"] = "skipped"
                    break
                value, texts = g.relation(o["nation"], o["kind"])
                r["texts"] += texts
                r["value"] = value
                r["ok"] = (value == {"trade": 1, "ally": 2, "war": 3}.get(o["kind"], value))
                break
            elif op == "taxation":
                r["texts"] += g.taxation(o["percent"])
                r["tax"] = g.rome()["tax"]
                if r["tax"] == o["percent"]:
                    r["ok"] = True
                    break
            elif op == "attack":
                nb = len(g.battles)
                before = g.army_state(o["army"])
                if before["moves"] <= 0:
                    r["skipped"] = "army has 0 moves: an attack with 0 moves does nothing (0725)"
                    r["ok"] = False
                    break
                r["texts"] += g.attack(o["army"], o["x"], o["y"])
                after = g.army_state(o["army"])
                r["army_before"], r["army_after"] = before, after
                r["battles"] = len(g.battles) - nb
                r["troops"] = (before["troops"], after["troops"])
                r["moves"] = (before["moves"], after["moves"])
                r["ok"] = bool(r["battles"] or after["moves"] != before["moves"] or after["troops"] != before["troops"]
                               or after["owner"] != before["owner"])
                break           # an attack is never retried
            elif op == "split":
                before = set(g.roman_armies())
                r["texts"] += g.split_army(o["army"], unit_rows=tuple(o["rows"]))
                new = sorted(set(g.roman_armies()) - before)
                r["new_armies"] = new
                if new:
                    r["ok"] = True
                    break
            else:
                raise DriverError("unknown op " + op)
        except Exception as e:
            r.setdefault("errors", []).append(repr(e))
            log("order %s attempt %d: %r" % (op, attempt + 1, e))
            try:
                g.dismiss_popups()
                g.reset_ui()
            except Exception:
                pass
    log("order %s -> ok=%s %s" % (op, r["ok"], {k: v for k, v in r.items() if k not in ("order", "army_before", "army_after", "new_armies")}))
    return r


def main(turn, orders_path):
    orders = json.loads(Path(orders_path).read_text())
    seed = 12345 + (turn - 720)
    sd = season_dir(turn)
    sd.mkdir(parents=True, exist_ok=True)
    logf = RUN / "turns" / ("%04d.log" % turn)
    logf.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")

    def log(msg):
        line = time.strftime("%H:%M:%S ") + str(msg)
        print(line, flush=True)
        with logf.open("a") as f:
            f.write(line + "\n")

    nxt = G / ("AUTO%04d.SAV" % (turn + 1))
    if nxt.exists():
        moved = Game.move_aside([nxt])
        log("moved an old %s aside to %s" % (nxt.name, moved))
    g = RunGame(log=log)
    g.shot_dir, g.turn_no = sd, turn
    src = save_path(turn)
    log("turn %04d: load %s (sha %s) seed %d" % (turn, src, sha(src)[:16], seed))
    result = {"turn": turn, "seed": seed, "save": src.name, "save_sha256": sha(src), "stamp": stamp, "orders": []}
    result["load_popups"] = g.load(src, seed=seed)
    result["seed_line"] = getattr(g, "seed_line", "")
    log("seed line %s; popups at load %s" % (result["seed_line"], result["load_popups"]))
    if g.turn_number() != turn:
        raise DriverError("loaded turn %d, expected %d" % (g.turn_number(), turn))
    shot = sd / ("shot-%04d-start-%s.png" % (turn, stamp))
    g.shot(shot)
    for o in orders:
        result["orders"].append(do_order(g, o, log))
    g.dismiss_popups()
    g.reset_ui()
    shot2 = sd / ("shot-%04d-orders-%s.png" % (turn, stamp))
    g.shot(shot2)
    result["rome_before_end"] = {k: v for k, v in g.rome().items() if k not in ("city_list",)}
    result["armies_before_end"] = {i: a for i, a in g.all_armies().items()}
    log("end turn")
    name, texts = g.end_turn(peace=False)
    result["end_turn_texts"] = texts
    result["autosave"] = name
    result["battles"] = g.battles
    log("autosave %s; texts %s; battles %d" % (name, texts, len(g.battles)))
    time.sleep(1)
    new = G / name
    out = season_dir(turn + 1)
    kept = [keep(new, out / name),
            keep(G / "AUTOSAVE.LOG", sd / ("AUTOSAVE-after-%04d-%s.LOG" % (turn, stamp))),
            keep(G / "SEED.LOG", sd / ("SEED-after-%04d-%s.LOG" % (turn, stamp))),
            shot, shot2]
    kept += [Path(b["shot"]) for b in g.battles if b.get("shot") and Path(b["shot"]).exists()]
    for p in kept:
        record_hash(p)
    result["artifacts"] = [str(Path(p).relative_to(ART)) for p in kept]
    result["autosave_sha256"] = sha(kept[0])
    metrics.record(RUN, [kept[0]])
    (RUN / "turns" / ("%04d.result.json" % turn)).write_text(json.dumps(result, indent=1, default=str))
    log("done: %s sha %s" % (kept[0], result["autosave_sha256"][:16]))
    try:
        g.kill()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main(int(sys.argv[1]), sys.argv[2])
    except Exception:
        traceback.print_exc()
        sys.exit(1)
