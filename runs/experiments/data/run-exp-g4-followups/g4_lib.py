"""Shared helpers of the g4 follow-up checks (copy of g3_lib) (issue #83): unique stamped names, hashing, OCR, staging, the Balance sheet reader.
Imported by g4_checks.py. One fresh Wine process per case (g4_checks.py <case>); fast rollingsave seed exe, Xvfb :99.
Rule 6: every output goes to a tracked log (g4_checks-<case>-<stamp>.jsonl) and to artifacts/run-exp-g4-followups/ with a unique name."""
import hashlib, json, shutil, struct, subprocess, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "runs/experiments/battles"))
import harness.driver as drv
from harness.driver import Game, G, DriverError, sh, WORK, WINE
from state import sav
import stage

START = R / "saves/run0-start-AUTO0720-seed12345.SAV"
PORT = R / "saves/fleet-port-antium-0734.SAV"
ART = R / "artifacts/run-exp-g4-followups"; ART.mkdir(parents=True, exist_ok=True)
D = Path(__file__).resolve().parent
STAMP = time.strftime("%Y%m%d-%H%M%S")
CASE = sys.argv[1] if len(sys.argv) > 1 else "none"
LOG = D / f"g4_checks-{CASE.replace(':', '_')}-{STAMP}.jsonl"
CUR = [None]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def log(step, **kw):
    kw.update(step=step, t=time.strftime("%H:%M:%S")); print(json.dumps(kw, default=str), flush=True)
    with LOG.open("a") as f: f.write(json.dumps(kw, default=str) + "\n")


def hook_environment():
    from harness import environment as _env
    _env.add_sink(lambda rec: log("environment", **{k: v for k, v in rec.items() if k != "step"}))


def _hash_line(dst):
    with (D / "SAVES.sha256").open("a") as f: f.write(f"{sha(dst)}  {dst.name}\n")


def keep(src, name):
    dst = ART / f"{CASE.replace(':', '_')}_{STAMP}_{name}"
    if dst.exists(): raise SystemExit(f"{dst} exists: names must be unique")
    shutil.copy2(src, dst); _hash_line(dst); return dst.name


AUTO_SEQ = [0]


def keep_auto(name, turn=None, tag=""):
    """Review fix R1(b): keep at once (copy, hash, log) the autosave `name` the game folder holds now, under a case/stamp/turn name, so a later
    New Game or another run can never take the only copy. Returns the kept name."""
    src = G / name
    AUTO_SEQ[0] += 1       # several saves of one run can carry the same AUTO name (one per game opened in the process): a sequence number keeps them apart
    kept = keep(src, f"autosave{AUTO_SEQ[0]:02d}_{tag + '_' if tag else ''}t{turn if turn is not None else 'x'}_{name}")
    log("autosave_kept", autosave=name, turn=turn, seq=AUTO_SEQ[0], tag=tag, kept=kept, sha256=sha(src), size=src.stat().st_size)
    return kept


def save(g, name):
    """File > Save As under a unique name, then keep a copy (never overwrites: Game.save_as refuses an existing file)."""
    return keep(g.save_as(f"g4_{CASE.replace(':', '_')}_{STAMP}_{name}"), name)


def shot(g, name, window="root"):
    p = ART / f"{CASE.replace(':', '_')}_{STAMP}_{name}.png"
    if p.exists(): raise SystemExit(f"{p} exists: image names must be unique")
    g.shot(p, window=window); _hash_line(p); return p.name


def ocr_png(p, psm="6"):
    t = subprocess.run(["tesseract", str(p), "-", "--psm", psm], capture_output=True, text=True).stdout
    return " ".join(t.split())


def ocr_window(g, name, wid):
    f = shot(g, name, window=str(wid)); return f, ocr_png(ART / f)


def windows(g): return [(w[1], w[4], w[5]) for w in g.find_windows(".") if w[4] > 1]


def boxes(g):
    """Every modal box now open: (title, OCR text); the image of each is kept."""
    out = []
    for p in g.popups():
        f = shot(g, f"box_{int(time.time() * 10 % 1000000)}", window=str(p[0])); out.append({"title": p[1], "image": f, "ocr": ocr_png(ART / f)})
    return out


def staged(src, ops, tag, extra=None):
    """Copy of src with the L1 ops applied (stage.apply) and `extra(bytearray)` for edits stage.py has no op for; stamped unique name."""
    b = bytearray(Path(src).read_bytes()); n0 = len(b); stage.apply(b, ops)
    if extra: extra(b)
    # review fix R3: every staging helper must preserve the save's length (an edit that inserts or drops bytes shifts every later field and
    # corrupts the save; the first hc mercenary staging did exactly that). `extra.grows = True` marks a helper that adds whole records on purpose.
    if len(b) != n0 and not getattr(extra, "grows", False):
        raise SystemExit(f"staging {tag!r} changed the save length {n0} -> {len(b)}: a slice assignment of another size? refusing to write")
    sav.parse(bytes(b))
    # review fix R3 (round 3): exclusive creation, never replace: a name that exists (a repeated tag, or `test:-5100 test:5100` meeting in
    # abs(treasury)) gets a `.vN` suffix before `.SAV`; the log's `dst` names the file actually written.
    base = f"{CASE.replace(':', '_')}_{STAMP}_staged_{tag}_{Path(src).stem}"; n = 0
    while True:
        dst = ART / (f"{base}.SAV" if n == 0 else f"{base}.v{n}.SAV")
        try:
            with open(dst, "xb") as f: f.write(bytes(b))
            break
        except FileExistsError: n += 1
    _hash_line(dst)
    log("staged", src=Path(src).name, src_sha256=sha(src), dst=dst.name, ops=ops, extra=getattr(extra, "__doc__", None))
    return dst


def set_wealth(n, v):
    def f(b):
        """nation %d wealth (+0x430, i32) := %d""" % (n, v)
        struct.pack_into("<i", b, stage._nation(b, n) + 0x430, v)
    f.__doc__ = "nation %d wealth (+0x430, i32) := %d" % (n, v)
    return f


def add_unit(army, label, typ, troops, quality, name):
    """Write a unit into army's first empty slot (label != 0 = mercenary)."""
    def f(b):
        base = stage._army(b, army)
        for k in range(20):
            o = base + 16 + 32 * k
            if struct.unpack_from("<h", b, o + 4)[0] <= 0:
                raw = name.encode("latin1")
                if len(raw) > 23: raise ValueError(f"unit name {name!r} is {len(raw)} bytes: the field holds 23 bytes + NUL (24)")   # R3: ljust(24) of 28 bytes inserted 4
                struct.pack_into("<4h", b, o, label, stage.TYPES[typ], troops, quality); b[o + 8:o + 32] = raw.ljust(24, b"\0"); return
        raise ValueError("army full")
    f.__doc__ = f"army {army}: first empty slot := label {label} {typ} {troops} q{quality} {name!r}"
    return f


# ---- the Balance sheet -----------------------------------------------------------------------------------------------
LEFT_X, RIGHT_X, ROWS = 122, 330, {"r1": 61, "r2": 91, "r3": 121, "r4": 152, "r5": 182, "total": 233, "bottom": 298}


def balance_from_memory(g):
    """The nine figures TBalanceSheet_PaintBalance (0045376c, dump lines 55409-55562) computes, recomputed from the running game's memory."""
    me = g.i16(drv.CUR_NATION); n = g.mem(drv.NATIONS + me * drv.NATION_LEN, drv.NATION_LEN)
    i16 = lambda o: struct.unpack_from("<h", n, o)[0]; i32 = lambda o: struct.unpack_from("<i", n, o)[0]
    tdiv = lambda a, b: int(a / b)                                  # C division truncates toward zero
    price = lambda t: struct.unpack("<h", g.mem(0x478fd4 + t * 40, 2))[0]
    out = {"nation": me, "tax_rate": i16(0x44a), "tax_base": i16(0x44c), "wealth": i32(0x430), "treasury": i32(0x438), "ncities": i16(0x446)}
    out["taxes"] = tdiv(i16(0x44c) * i16(0x44a), 100); out["tribute"] = tdiv(i16(0x44c), 4)
    out["administration"] = tdiv(i32(0x430), 20000) + i16(0x446) * 7
    fl = 0
    for k in range(g.i16(0x4A0326)):
        r = g.fleet_rec(k)
        if struct.unpack_from("<h", r, 8)[0] == me: fl += struct.unpack_from("<h", r, 18)[0] * 3
    out["fleet"] = fl
    rq = 0
    for k in range(40):
        tr = i16(0x2e8 + 8 * k)
        if tr > 0: rq += tdiv(tr, 200) * price(i16(0x2e6 + 8 * k))
    out["army_recruit"] = rq
    reg = mer = 0
    for a in range(g.i16(0x4A0324)):
        r = g.army_rec(a)
        if struct.unpack_from("<h", r, 4)[0] != me: continue
        for k in range(20):
            lab, typ, tr, q = struct.unpack_from("<4h", r, 16 + 32 * k)
            if tr > 0:
                c = tdiv(tr, 200) * price(typ)
                if lab == 0: reg += c
                else: mer += tdiv(q * c, 5)
    out["regular_units"] = reg; out["mercenary_units"] = mer
    out["expenditure_total_if_all_five"] = out["administration"] + fl + rq + reg + mer
    c = min(tdiv(i32(0x430), 500), 20000)
    out["debt_limit_unrounded_wealth_div_500"] = tdiv(i32(0x430), 500)
    out["debt_limit_displayed"] = c - c % 100 if c < 5001 else c - c % 500 if c - 5001 < 5000 else c - c % 1000 if c - 10001 < 10000 else c
    return out


def read_number(png, x0, y, w=70):
    """OCR one value box of the Balance sheet image: crop, enlarge 4x, digits only."""
    c = png.with_name(png.stem + f"_crop_{x0}_{y}.png")
    subprocess.run(["convert", str(png), "-crop", f"{w}x24+{x0}+{y - 12}", "+repage", "-resize", "400%", "-colorspace", "Gray", str(c)], check=True)
    _hash_line(c)
    tries = {}
    for psm in ("7", "8", "13"):          # a value that psm 7 misses (seen: "18" in the Mercenary line) is retried; every attempt is kept
        t = subprocess.run(["tesseract", str(c), "-", "--psm", psm, "-c", "tessedit_char_whitelist=-,0123456789"], capture_output=True, text=True).stdout.strip()
        tries[psm] = t
        if t.replace(",", "").lstrip("-").isdigit(): break
    t = tries[psm]; s = t.replace(",", "")
    return {"ocr": t, "value": int(s) if s.lstrip("-").isdigit() else None, "crop": c.name, "ocr_attempts": tries}


def balance_sheet(g, tag):
    """Strategy > Balance sheet (toolbar): open, photograph, read every box by OCR, close with OK. Returns the OCR readings and the memory recomputation."""
    g.dismiss_popups()
    for _ in range(3):
        g.tool("balance", pause=1.5)
        if g.find_windows("^Balance sheet$"): break
    w = g.find_windows("^Balance sheet$")
    if not w: raise DriverError("Balance sheet did not open")
    g.raise_window(w[0][0]); time.sleep(0.8)
    f, full_ocr = ocr_window(g, f"balance_{tag}", w[0][0]); png = ART / f
    rd = {"revenue": {}, "expenditure": {}}
    for key, y in (("taxes", ROWS["r1"]), ("tribute", ROWS["r2"]), ("trade", ROWS["r3"]), ("total", ROWS["total"])): rd["revenue"][key] = read_number(png, LEFT_X, y)
    for key, y in (("administration", ROWS["r1"]), ("fleet", ROWS["r2"]), ("army_recruit", ROWS["r3"]), ("regular_units", ROWS["r4"]),
                   ("mercenary_units", ROWS["r5"]), ("total", ROWS["total"])): rd["expenditure"][key] = read_number(png, RIGHT_X, y)
    rd["balance"] = read_number(png, LEFT_X, ROWS["bottom"]); rd["debt_limit"] = read_number(png, RIGHT_X, ROWS["bottom"])
    mem = balance_from_memory(g)
    cs = g.controls("Balance sheet")
    for _ in range(3):
        g.click_control(g.control(cs, text="OK"), pause=1.0)
        if not g.find_windows("^Balance sheet$"): break
    log("balance_sheet", tag=tag, image=f, full_ocr=full_ocr, readings=rd, memory=mem, closed=not g.find_windows("^Balance sheet$"))
    return rd, mem


# ---- g3 helpers kept in g4: calendar staging, memory snapshots, diffs, one End turn round ------------------------------------------------
CITY_MEM, NEWS_MEM = 0x479590, 0x49f994
CITY_FIELDS = ("x", "y", "owner", "allegiance", "loyalty", "stock", "fort", "pop", "max_pop", "tribute")


def set_calendar(week=None, season=None, year=None):
    """Staging helper (L1): the save tail's week (+40), year BC (+42) and season (+44) words (state/sav.py: tail 23 shorts from `tail_off`)."""
    def f(b):
        t = sav.parse(bytes(b))["tail_off"]
        if week is not None: struct.pack_into("<h", b, t + 40, week)
        if year is not None: struct.pack_into("<h", b, t + 42, year)
        if season is not None: struct.pack_into("<h", b, t + 44, season)
    f.__doc__ = f"calendar: week={week} season={season} year_bc={year} (save tail +40/+44/+42)"
    return f


def chain(*fs):
    """Compose staging helpers into one `extra` (docstrings joined)."""
    def f(b):
        for x in fs: x(b)
    f.__doc__ = "; ".join(x.__doc__ or "?" for x in fs)
    f.grows = any(getattr(x, "grows", False) for x in fs)
    return f


def set_cities(ids, field, value):
    """city records `ids` field := value (CITY_FIELDS of stage.py, one i16 each)."""
    def f(b):
        for c in ids: stage.set_city(b, c, {field: value})
    f.__doc__ = f"cities {list(ids)}: {field} := {value}"
    return f


def set_city_stock_to_pop_cap(ids):
    """city record `ids` stock (+0x18) := 10 x its population (the cap the round applies, FUN_004514ec: min(stock, pop*10))."""
    def f(b):
        for c in ids:
            o = sav.CITY_OFF + c * sav.CITY_LEN
            struct.pack_into("<h", b, o + 24, struct.unpack_from("<h", b, o + 28)[0] * 10)
    f.__doc__ = f"cities {list(ids)}: stock := 10 x population"
    return f


def news_mem(g):
    out = []
    for i in range(40):
        raw = g.mem(NEWS_MEM + i * 0x3d, 0x3d); ln = raw.find(b"\0")
        out.append(raw[:ln].decode("latin1") if ln > 0 else "")
    return out


def snap(g):
    cm = g.mem(CITY_MEM, 334 * 34)
    cities = []
    for c in range(334):
        o = c * 34
        cities.append((cm[o:o + 14].split(b"\0")[0].decode("latin1"),) + struct.unpack_from("<10h", cm, o + 14))
    nations = [g.nation_state(n) for n in range(16)]
    armies = [g.army_state(i) for i in range(g.i16(0x4A0324))]
    fleets = [(i, g.fleet_rec(i).hex()) for i in range(g.i16(0x4A0326))]
    mp = g.mem(drv.MAP, 320 * 140 * 2); rough = [(i // 140, i % 140) for i in range(320 * 140) if mp[2 * i] == 1 and mp[2 * i + 1] == 0]
    return {"cal": g.calendar(), "cur": g.i16(drv.CUR_NATION), "rough_cells": len(rough), "rough_sample": rough[:40], "cities": cities, "nations": nations, "armies": armies, "fleets": fleets, "news": news_mem(g), "news_count": g.i16(0x4a031e)}


NATION_KEYS = ("unity", "treasury", "wealth", "mobilization", "capital", "cities_count", "tax", "tax_base", "conquered_by", "human", "leader", "alive")


def nat_brief(n): return {k: n[k] for k in NATION_KEYS}


def diff(a, b):
    """What changed between two snaps: cities (any field), nations (NATION_KEYS, relations, city_list), armies (by index, compact), new news lines."""
    d = {"cities": [], "nations": [], "armies": [], "fleets": []}
    for c in range(334):
        if a["cities"][c] != b["cities"][c]:
            d["cities"].append({"id": c, "name": a["cities"][c][0], "before": dict(zip(CITY_FIELDS, a["cities"][c][1:])), "after": dict(zip(CITY_FIELDS, b["cities"][c][1:]))})
    for n in range(16):
        x, y = a["nations"][n], b["nations"][n]
        ch = {k: (x[k], y[k]) for k in NATION_KEYS if x[k] != y[k]}
        rel = {k: (x["relations"][k], y["relations"][k]) for k in x["relations"] if x["relations"].get(k) != y["relations"].get(k)}
        if ch or rel or x["city_list"] != y["city_list"]:
            d["nations"].append({"id": n, "name": sav.NATIONS[n], "changed": ch, "relations": rel, "cities_gained": sorted(set(y["city_list"]) - set(x["city_list"])), "cities_lost": sorted(set(x["city_list"]) - set(y["city_list"]))})
    ab = lambda r: (r["owner"], r["x"], r["y"], r["moves"], r["supplies"], r["money"], r["morale"], tuple((u["slot"], u["type"], u["troops"], u["quality"], u["merc"], u["name"]) for u in r["units"]))
    for i in range(max(len(a["armies"]), len(b["armies"]))):
        x = ab(a["armies"][i]) if i < len(a["armies"]) else None; y = ab(b["armies"][i]) if i < len(b["armies"]) else None
        if x != y: d["armies"].append({"id": i, "before": x, "after": y})
    d["fleets"] = [{"id": i, "before": a["fleets"][i][1] if i < len(a["fleets"]) else None, "after": b["fleets"][i][1] if i < len(b["fleets"]) else None}
                   for i in range(max(len(a["fleets"]), len(b["fleets"]))) if (a["fleets"][i] if i < len(a["fleets"]) else None) != (b["fleets"][i] if i < len(b["fleets"]) else None)]
    return d


def new_lines(before, after):
    """New news lines between two buffer reads (lists of 40 strings, "" = unused slot). The buffer scrolls when full, so index comparison is wrong
    (the first Q1ab..Q1d logs used it: their `news_new` is unreliable once the buffer holds 40 lines; `news_all` in the log is complete and the analysis
    recomputes). Returns the lines of `after` that follow the longest overlap: smallest shift s with before[s:] == after[:len(before)-s]."""
    b = [t for t in before if t != ""]; a = [t for t in after if t != ""]
    for s_ in range(len(b) + 1):
        k = len(b) - s_
        if b[s_:] == a[:k]: return a[k:]
    return a


def new_news(a, b): return new_lines(a["news"], b["news"])


def round_(g, tag, src, first, turns=1, seed=12345):
    """Open the staged save `src` (first: Game.load with the seed in a fresh process; later: File > Open in the same process, the RNG goes on), snapshot,
    End turn `turns` times keeping every autosave (keep_auto) and snapshotting after each. Returns (before, afters, diffs)."""
    if first: texts_open = g.load(src, seed=seed)
    else:
        texts_open = g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
    before = snap(g)
    log("round_open", tag=tag, save=Path(src).name, saved_news=sav.parse(Path(src).read_bytes())["news"], note_news="`news` is the memory buffer right after File>Open (it can still hold the previous game's lines); `saved_news` is the opened save's own news list",
        pid=g.pid, open_boxes=texts_open, cal=before["cal"], cur=before["cur"],
        nations={sav.NATIONS[n["id"]]: nat_brief(n) for n in before["nations"]}, news=before["news"], root=shot(g, f"{tag}_opened"))
    afters, diffs, prev = [], [], before
    for t in range(turns):
        rec = {"tag": tag, "turn_click": t + 1}
        try:
            name, texts = g.end_turn(); time.sleep(2)
            rec.update(autosave=name, texts=texts, kept=keep_auto(name, g.turn_number(), tag), eog=bool(g.find_windows("^End of Game$")))
            rec["autosave_news"] = sav.parse((ART / rec["kept"]).read_bytes())["news"]       # the autosave's own news list: the memory buffer can keep stale tail lines after a File>Open (seen in Q1c seven_control)
        except drv.GameOver as e:
            rec.update(game_over=e.text)
        after = snap(g); d = diff(prev, after)
        rec.update(cal=after["cal"], turn=g.turn_number(), news_new=new_news(prev, after), news_all=after["news"], diff=d, boxes=boxes(g), root=shot(g, f"{tag}_after{t + 1}"))
        log("round_done", **rec)
        afters.append(after); diffs.append(d); prev = after
        if rec.get("game_over") or rec.get("eog"): break
    return before, afters, diffs


def set_map(x, y, v):
    """map cell (x, y) := v (save offset (x*140+y)*2, u16): the overlay's own write (FUN_004511bc paints code 1 onto a code-0 cell)."""
    def f(b):
        struct.pack_into("<H", b, (x * 140 + y) * 2, v)
    f.__doc__ = f"map cell ({x},{y}) := {v}"
    return f


def set_fleet(i, **kw):
    """fleet record i fields (save fleet table, 26-byte records, docs/sav-layout-notes.md): cond (+20), supplies (+14), cell (+24, the covered map code)."""
    offs = {"cond": 20, "supplies": 14, "cell": 24, "moves": 12}
    def f(b):
        na = struct.unpack_from("<h", b, sav.ARMY_OFF)[0]; o = sav.ARMY_OFF + 2 + na * sav.ARMY_LEN + 2 + i * sav.FLEET_LEN
        for k, v in kw.items(): struct.pack_into("<h", b, o + offs[k], v)
    f.__doc__ = f"fleet {i}: " + ", ".join(f"{k} := {v}" for k, v in kw.items())
    return f


def light_round(g, tag, src, first, seed=12345, extra=None):
    """open `src` (first: fresh process load; later File > Open), End turn once keeping the autosave, return (autosave Path, texts, before-snapshot-lite, after).
    Logs one `light_round` line: texts of the boxes, the kept autosave's pending offer / relations / news tail, Rome's relations, fleets (raw), rough-cell count."""
    if first: g.load(src, seed=seed)
    else:
        g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
    fl0 = [g.fleet_rec(i).hex() for i in range(g.i16(0x4A0326))]
    rel0 = [g.i16(drv.NATIONS + 0x26 + 2 * k) for k in range(16)]
    n0 = news_mem(g)
    rec = {"tag": tag, "save": Path(src).name, "pid": g.pid, "cal_before": g.calendar(), "fleets_before": fl0, "rome_rel_before": rel0}
    try:
        name, texts = g.end_turn(); time.sleep(2)
        kept = keep_auto(name, g.turn_number(), tag)
        s_ = sav.parse((ART / kept).read_bytes())
        rec.update(autosave=name, kept=kept, texts=texts, cal_after=g.calendar(), pending_offer=s_["pending_offer"], rome_rel_after=[g.i16(drv.NATIONS + 0x26 + 2 * k) for k in range(16)],
                   fleets_after=[g.fleet_rec(i).hex() for i in range(g.i16(0x4A0326))], news_new=new_lines(n0, news_mem(g)), cur_after=g.i16(drv.CUR_NATION))
        mp = g.mem(drv.MAP, 320 * 140 * 2); rec["rough_cells_after"] = sum(1 for i in range(320 * 140) if mp[2 * i] == 1 and mp[2 * i + 1] == 0)
    except drv.GameOver as e:
        rec.update(game_over=e.text)
    if extra: rec.update(extra(g))
    log("light_round", **rec)
    return rec


def give_cities(frm, to, ids, kill_frm=False):
    """L1: city `ids` change owner frm -> to (city +0x12), both nations' city lists (+0x48, -1 terminated) and count words (+0x446) are kept consistent;
    allegiance, loyalty and everything else of the cities stay. kill_frm: nation `frm` also gets unity 0 and capital -1 (+0x444): a nation eliminated the way
    the game leaves it (alive = unity > 0 and capital != -1, state/sav.py)."""
    def lst(b, n):
        o = stage._nation(b, n) + 0x48; v = []
        for k in range(334):
            c = struct.unpack_from("<h", b, o + 2 * k)[0]
            if c < 0: break
            v.append(c)
        return v
    def put(b, n, v, old_len):
        o = stage._nation(b, n) + 0x48
        for k in range(max(len(v), old_len) + 1):
            struct.pack_into("<h", b, o + 2 * k, v[k] if k < len(v) else -1)
        struct.pack_into("<h", b, stage._nation(b, n) + 0x446, len(v))
    def f(b):
        a, t = lst(b, frm), lst(b, to); la, lt = len(a), len(t)
        for c in ids:
            a.remove(c); t.append(c); stage.set_city(b, c, {"owner": to})
        put(b, frm, a, la); put(b, to, t, lt)
        if kill_frm:
            struct.pack_into("<h", b, stage._nation(b, frm) + 0x440, 0); struct.pack_into("<h", b, stage._nation(b, frm) + 0x444, -1)
    f.__doc__ = f"cities {list(ids)}: owner {frm} -> {to}, city lists and counts kept consistent" + ("; nation %d unity 0, capital -1" % frm if kill_frm else "")
    return f


# ---- g4 additions -------------------------------------------------------------------------------------------------------------
import os, threading


class Poller:
    """Check F: a thread that reads `size` bytes at `addr` of the game's memory (/proc/<pid>/mem, read only) every `dt` seconds and records every CHANGE with
    the time (time.time()), plus the sample count and the largest gap between two samples; `mark(label)` records a UI event on the same clock."""
    def __init__(self, pid, addr, size=1, dt=0.01):
        self.fd = os.open(f"/proc/{pid}/mem", os.O_RDONLY); self.addr, self.size, self.dt = addr, size, dt
        self.changes, self.marks, self.samples, self.max_gap = [], [], 0, 0.0
        self._stop = threading.Event(); self.last = None; self._t = None
        self.th = threading.Thread(target=self._run, daemon=True)

    def read(self): return os.pread(self.fd, self.size, self.addr)

    def _run(self):
        prev_t = None
        while not self._stop.is_set():
            try: v = self.read()
            except OSError: break
            t = time.time(); self.samples += 1
            if prev_t is not None: self.max_gap = max(self.max_gap, t - prev_t)
            prev_t = t
            if v != self.last: self.changes.append((t, v.hex())); self.last = v
            time.sleep(self.dt)

    def start(self): self.th.start(); return self
    def mark(self, label): self.marks.append((time.time(), label, self.read().hex()))
    def stop(self):
        self._stop.set(); self.th.join(timeout=2)
        try: os.close(self.fd)
        except OSError: pass
        return {"samples": self.samples, "max_gap_s": round(self.max_gap, 4), "interval_s": self.dt,
                "changes": [(round(t, 3), v) for t, v in self.changes], "marks": [(round(t, 3), l, v) for t, l, v in self.marks]}


def set_offer(frm, typ):
    """Staging helper (L1): the pending-offer words of the save tail (`from` = tail short 16 = DAT_0049f008, `type` = short 17 = DAT_0049f00a; state/sav.py `pending_offer`)."""
    def f(b):
        t = sav.parse(bytes(b))["tail_off"]
        struct.pack_into("<h", b, t + 32, frm); struct.pack_into("<h", b, t + 34, typ)
    f.__doc__ = f"pending offer: from {frm} type {typ} (save tail shorts 16/17)"
    return f


def relations_dialog(g):
    """International Relations: open (toolbar), return (window id, controls, the 64 radio buttons sorted by row/column: nation * 4 + kind)."""
    g.dismiss_popups()
    for _ in range(3):
        g.tool("relations", pause=1.5)
        if g.find_windows("^International Relations$"): break
    w = g.find_windows("^International Relations$"); g.raise_window(w[0][0])
    for _ in range(8):
        try: cs = g.controls("International Relations"); break
        except DriverError: time.sleep(1)
    radios = sorted((c for c in cs if c["cls"] == "TRadioButton"), key=lambda c: (c["y"], c["x"]))
    if len(radios) != 64: raise DriverError("expected 64 radios, found %d" % len(radios))
    return w[0][0], cs, radios


def rel(g, a, b): return g.i16(drv.NATIONS + a * drv.NATION_LEN + 0x26 + 2 * b)


def set_queue(n, slot, **kw):
    """Staging helper (L1): nation n's recruit-queue slot (8-byte records at nation +0x2e4: state, type, troops, city; names as in the Balance sheet reader)."""
    offs = {"state": 0, "type": 2, "troops": 4, "city": 6}
    def f(b):
        o = stage._nation(b, n) + 0x2e4 + 8 * slot
        for k, v in kw.items(): struct.pack_into("<h", b, o + offs[k], v)
    f.__doc__ = f"nation {n} queue slot {slot}: " + ", ".join(f"{k} := {v}" for k, v in kw.items())
    return f
