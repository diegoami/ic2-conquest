#!/usr/bin/env python3
"""run-exp-sav-rebellion107: native check of the rebellion and revival rule (issue #107, increments 8 and 10).

    python3 runs/experiments/sav-inert107/rebellion.py craft SRC   # SRC = 1_rome_270_winter_11.sav (release run-exp-battle-probe)
    python3 runs/experiments/sav-inert107/rebellion.py run
    python3 runs/experiments/sav-inert107/rebellion.py analyse STAMP

The crafted copy changes only city loyalties (CASES). `run` loads the plain and the crafted copy (seed build, seed 12345)
and ends the turn once each; the week-11 turn's end runs the quarterly loop. `analyse` writes a receipt of owners,
nation records and relations (indices and fields only). Logs: runs/experiments/data/run-exp-sav-rebellion107/;
saves: artifacts/run-exp-sav-rebellion107/ (unique names, never deleted; CLAUDE.md rule 6).
"""
import hashlib
import json
import shutil
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import sav_atlas_coverage as cov  # noqa: E402

DATA = ROOT / "runs/experiments/data/run-exp-sav-rebellion107"
BASE = ROOT / "artifacts/run-exp-sav-rebellion107"
GALATIA, SELEUCID, CARTHAGE = 12, 2, 1
REVIVAL = (211, 215, 218, 227, 232, 233, 239, 242)        # the 8 cities of allegiance Galatia (all held by Seleucid)
CASES = {**{c: 20 for c in REVIVAL}, 98: 5, 3: 5, 72: 5}  # + Agrigentum (R1), Ebora (R2), Carthage's capital (control)


def i16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def craft(src):
    out = BASE / "inputs"
    out.mkdir(parents=True, exist_ok=True)
    b = bytearray(Path(src).read_bytes())
    c0 = {r: o for r, o, _ in cov.frame(bytes(b))[0]}["city"]
    for c, loy in CASES.items():
        struct.pack_into("<h", b, c0 + 34 * c + 0x16, loy)
    for name, data in (("RB0_plain_1_rome_270_winter_11.SAV", Path(src).read_bytes()), ("RB1_crafted_loyalty.SAV", bytes(b))):
        cov.frame(data)
        with open(out / name, "xb") as fh:
            fh.write(data)
        print(name, hashlib.sha256(data).hexdigest())


def summary(b):
    blocks, facts = cov.frame(b)
    pos = {r: o for r, o, _ in blocks}
    c0, n0 = pos["city"], pos["nation"]
    city = {c: dict(zip(("x", "y", "owner", "allegiance", "loyalty", "supplies", "fort", "pop", "max_pop", "tribute"),
                        struct.unpack_from("<10h", b, c0 + 34 * c + 14))) for c in range(334)}
    nat = {}
    for n in range(16):
        o = n0 + 1172 * n
        nat[n] = dict(unity=i16(b, o + 0x440), mobilization=i16(b, o + 0x442), capital=i16(b, o + 0x444),
                      cities=i16(b, o + 0x446), tax=i16(b, o + 0x44A), tax_base=i16(b, o + 0x44C), conqueror=i16(b, o + 0x44E),
                      treasury=struct.unpack_from("<i", b, o + 0x438)[0], wealth=struct.unpack_from("<i", b, o + 0x430)[0],
                      relations=[i16(b, o + 0x26 + 2 * k) for k in range(16)],
                      leader=b[o + 0xB:o + 0x26].split(b"\0", 1)[0].decode("latin1"))
    mark = lambda c: i16(b, 2 * (city[c]["x"] * 140 + city[c]["y"]))
    return city, nat, mark


def run():
    from harness import driver
    stamp = time.strftime("%Y%m%d-%H%M%S")
    DATA.mkdir(parents=True, exist_ok=True)
    art = BASE / stamp
    art.mkdir(parents=True, exist_ok=True)
    fh = open(DATA / f"run-{stamp}.jsonl", "x")

    def log(step, **kw):
        rec = dict(t=time.strftime("%H:%M:%S"), step=step, **kw)
        fh.write(json.dumps(rec) + "\n"); fh.flush(); print(json.dumps(rec)[:300], flush=True)

    g = driver.Game(log=lambda *a: None)
    log("start", exe=driver.EXE, stamp=stamp)
    for tag, name in (("RB0", "RB0_plain_1_rome_270_winter_11.SAV"), ("RB1", "RB1_crafted_loyalty.SAV")):
        texts = g.load(BASE / "inputs" / name, seed=12345)
        log("loaded", tag=tag, save=name, seed_line=g.seed_line, texts=texts)
        log("end_turn", tag=tag, texts=str(g.end_turn(strict_confirm=True)))
        line = (driver.G / "AUTOSAVE.LOG").read_text().splitlines()[-1]
        dst = art / f"{tag}_after_end_turn_autosave.SAV"
        shutil.copyfile(driver.G / line.split()[1], dst)
        log("kept", file=dst.name, sha256=hashlib.sha256(dst.read_bytes()).hexdigest())
    g.kill()
    log("done")


def analyse(stamp):
    art = BASE / stamp
    pre = summary((BASE / "inputs" / "RB1_crafted_loyalty.SAV").read_bytes())
    ctl_pre = summary((BASE / "inputs" / "RB0_plain_1_rome_270_winter_11.SAV").read_bytes())
    post = summary((art / "RB1_after_end_turn_autosave.SAV").read_bytes())
    ctl = summary((art / "RB0_after_end_turn_autosave.SAV").read_bytes())
    pc, pn, _ = pre
    qc, qn, qmark = post
    cc, cn, _ = ctl
    changed = sorted(c for c in range(334) if qc[c]["owner"] != pc[c]["owner"])
    ctl_changed = sorted(c for c in range(334) if cc[c]["owner"] != ctl_pre[0][c]["owner"])
    gal = qn[GALATIA]
    out = dict(
        stamp=stamp,
        owner_changes_crafted={c: [pc[c]["owner"], qc[c]["owner"]] for c in changed},
        owner_changes_plain_control={c: [ctl_pre[0][c]["owner"], cc[c]["owner"]] for c in ctl_changed},
        revival=dict(galatia_before={k: pn[GALATIA][k] for k in ("unity", "capital", "cities")},
                     galatia_after={k: gal[k] for k in ("unity", "mobilization", "capital", "cities", "tax", "tax_base",
                                                       "conqueror", "treasury")},
                     galatia_relations_after=gal["relations"],
                     relations_toward_galatia_after={n: qn[n]["relations"][GALATIA] for n in range(16)},
                     relations_toward_galatia_before={n: pn[n]["relations"][GALATIA] for n in range(16)},
                     wealth_unchanged=gal["wealth"] == pn[GALATIA]["wealth"],
                     leader_changed=gal["leader"] != pn[GALATIA]["leader"],
                     revival_cities_owned_by_galatia=[c for c in REVIVAL if qc[c]["owner"] == GALATIA],
                     capital_marker_is_owner_plus_84=(gal["capital"] >= 0 and qmark(gal["capital"]) == GALATIA + 84)),
        r1_agrigentum=dict(before=[pc[98]["owner"], pc[98]["allegiance"]], after_owner=qc[98]["owner"]),
        r2_ebora=dict(before=[pc[3]["owner"], pc[3]["allegiance"]], after_owner=qc[3]["owner"], loyalty_after=qc[3]["loyalty"]),
        control_carthage_capital=dict(owner_before=pc[72]["owner"], owner_after=qc[72]["owner"]),
        files={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(art.glob("*.SAV"))})
    with open(DATA / f"analysis-{stamp}.json", "x") as fh:
        json.dump(out, fh, indent=1); fh.write("\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    craft(sys.argv[2]) if cmd == "craft" else run() if cmd == "run" else analyse(sys.argv[2])
