"""Shared helpers of the g1 original-side checks (issue #78): unique stamped names, hashing, OCR, staging, the Balance sheet reader.
Imported by g1_checks.py. One fresh Wine process per case (g1_checks.py <case>); fast rollingsave seed exe, Xvfb :99.
Rule 6: every output goes to a tracked log (g1_checks-<case>-<stamp>.jsonl) and to artifacts/run-exp-g1-original-checks/ with a unique name."""
import hashlib, json, shutil, struct, subprocess, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[4]; sys.path.insert(0, str(R)); sys.path.insert(0, str(R / "runs/experiments/battles"))
import harness.driver as drv
from harness.driver import Game, G, DriverError, sh, WORK, WINE
from state import sav
import stage

START = R / "saves/run0-start-AUTO0720-seed12345.SAV"
PORT = R / "saves/fleet-port-antium-0734.SAV"
ART = R / "artifacts/run-exp-g1-original-checks"; ART.mkdir(parents=True, exist_ok=True)
D = Path(__file__).resolve().parent
STAMP = time.strftime("%Y%m%d-%H%M%S")
CASE = sys.argv[1] if len(sys.argv) > 1 else "none"
LOG = D / f"g1_checks-{CASE.replace(':', '_')}-{STAMP}.jsonl"
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


def save(g, name):
    """File > Save As under a unique name, then keep a copy (never overwrites: Game.save_as refuses an existing file)."""
    return keep(g.save_as(f"g1_{CASE.replace(':', '_')}_{STAMP}_{name}"), name)


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
    b = bytearray(Path(src).read_bytes()); stage.apply(b, ops)
    if extra: extra(b)
    dst = ART / f"{CASE.replace(':', '_')}_{STAMP}_staged_{tag}_{Path(src).stem}.SAV"; dst.write_bytes(bytes(b)); _hash_line(dst)
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
                struct.pack_into("<4h", b, o, label, stage.TYPES[typ], troops, quality); b[o + 8:o + 32] = name.encode("latin1").ljust(24, b"\0"); return
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
