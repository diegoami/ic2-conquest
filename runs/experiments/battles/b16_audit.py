#!/usr/bin/env python3
"""B16 claims audit: every number and every "identical / closed / opened" claim of findings/2026-10-05-battle-peace-offer.md recomputed from the RAW
files (the `.snap.gz` memory snapshots, the Save As / autosave `.SAV` files, the dialog and Battle-ended screenshots, and `trials-b16.jsonl` for the
facts that only the run knows: the seed, the plan, the answer clicked, the box text), written as `b16-claims-audit-<stamp>.md` in the tracked data folder
(never overwritten). Exit 1 on a mismatch.

    python3 runs/experiments/battles/b16_audit.py

Independence: the unity, city count, relation, treasury, army strength, owner and news values are read from the BYTES with `struct` here (nation record
+0x26/0x438/0x440/0x446, army record +4/+14/+16.., the offsets of docs/sav-layout-notes.md); `b16_analyze.py`, `b16_run.strategic`/`rcode`, `state.sav` and
`state.battle` are not used. Shared with the run: the file lists, and the way a snapshot/save is located (memory addresses of the nation and army
tables, the save's block order). The SHA-256 of every binary is checked against `SAVES.v2.sha256` (one form: `<sha256>  <bare file name>`).
"""
import csv
import gzip
import hashlib
import json
import os
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ.setdefault("IC2_WORK", "/nonexistent")
os.environ.setdefault("DISPLAY_IC2", ":640")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import b16_common as B  # noqa: E402
import common as C  # noqa: E402

BASE = 0x45E030
NAT, ARM = 0x474670, 0x47C1EC
WEIGHT = {0: 20, 1: 100, 2: 40, 3: 60, 4: 120}      # unit type index -> power weight (docs/rules-digest.md: li, hi, ar, lc, hc)
rows = []


def norm(x):
    """JSON-comparable form: tuples are lists, sets sorted lists, dict keys strings (so claimed values can live in b16_expect.json)."""
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if isinstance(x, set):
        return sorted((norm(v) for v in x), key=str)
    return x


def claim(doc, text, source, got, want):
    rows.append((doc, text, source, norm(got), norm(want), "y" if norm(got) == norm(want) else "N"))


def i16(b, o):
    return struct.unpack_from("<h", b, o)[0]


def trials():
    return [json.loads(x) for x in (B.DATA / "trials-b16.jsonl").read_text().splitlines() if x.strip()]


def ok_trials():
    last = {}
    for r in trials():
        if r.get("status") == "ok":
            last[r["trial"]] = r
    return last


def snap(name):
    return gzip.decompress((B.ART / "snaps" / name).read_bytes())


# ---- raw readers of a memory snapshot ----------------------------------------------------------------------------------------------------
def s_nation(b, n, off):
    return i16(b, NAT - BASE + n * 1172 + off)


def s_armies(b, owner):
    """Σ over the owner's live armies of (Σ weight*troops//100) // 80 * morale (FUN_0044A8CC), read from the bytes."""
    tot = 0
    for i in range(200):
        r = ARM - BASE + i * 656
        if i16(b, r + 4) != owner:
            continue
        s = 0
        for k in range(20):
            lab, typ, troops, q = struct.unpack_from("<4h", b, r + 16 + 32 * k)
            if troops > 0:
                s += WEIGHT[typ] * troops // 100
        if s:
            tot += s // 80 * i16(b, r + 14)
    return tot


def s_army_alive(b, i):
    r = ARM - BASE + i * 656
    return sum(max(0, i16(b, r + 16 + 32 * k + 4)) for k in range(20)) > 0


# ---- raw readers of a save -------------------------------------------------------------------------------------------------------------------
def v_offsets(b):
    na = i16(b, 100956)
    of = 100956 + 2 + na * 656
    nf = i16(b, of)
    return of + 2 + nf * 26            # nation 0 record


def v_nation(b, n, off):
    return i16(b, v_offsets(b) + n * 1172 + off)


def v_treasury(b, n):
    return struct.unpack_from("<i", b, v_offsets(b) + n * 1172 + 0x438)[0]


def v_news(b):
    o = v_offsets(b) + 16 * 1172 + 600
    ni = i16(b, o)
    out = []
    for k in range(ni + 1):
        raw = b[o + 2 + 61 * k:o + 2 + 61 * (k + 1)]
        out.append(raw.split(b"\0")[0].decode("latin1"))
    return out


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    T = ok_trials()
    errs = [r for r in trials() if r.get("status") == "error"]
    shas = {}
    sums_file = sorted(B.DATA.glob("SAVES.v*.sha256"), key=lambda q: int(q.stem.split(".v")[1].split("-")[0]))[-1]
    for line in sums_file.read_text().splitlines():
        h, _, n = line.partition("  ")
        shas[n] = h
    # ---- the survey ----------------------------------------------------------------------------------------------------------------------------
    survey = {}
    for r in T.values():
        if r["answer_plan"] == "capture" and r["trial"].split("_")[2] in ("survey", "capture"):
            survey.setdefault((r["cell"], r["seed"]), r)

    def box_from_files(r):         # the box counted from the dialog screenshot file, independent of the record's flag
        return bool(r.get("dialogs")) and (B.ART / "shots" / r["dialogs"][0]["shot"]).exists()
    for cell, seeds in (("loss", range(1, 31)), ("win", range(1, 11))):
        rr = [survey[(cell, s)] for s in seeds if (cell, s) in survey]
        opened = sorted(r["seed"] for r in rr if box_from_files(r))
        claim("finding survey", "%s: %d seeds surveyed; box opened (dialog screenshot present) in seeds %s" % (cell, len(rr), opened), "trials-b16.jsonl + shots/",
              (len(rr), opened, sum(1 for r in rr if r["box_opened"])), EXPECT["survey_" + cell])
        # the strategic state from the snapshot bytes, not from the record
        got = Counter()
        for r in rr:
            b = snap(r["pre_snap"])
            W = 0 if s_army_alive(b, 0) else 6
            L = 6 if W == 0 else 0
            got[(W, s_armies(b, W) < s_armies(b, L), s_nation(b, L, 0x440) > 500, s_nation(b, L, 0x446) > 7, box_from_files(r))] += 1
        claim("finding survey", "%s: counts of (winner nation, armies(W) < armies(L), unity(L) > 500, cities(L) > 7, box opened) recomputed from the %d snapshots" % (cell, len(rr)),
              "*_pre.snap.gz", dict(sorted(got.items())), EXPECT["rcode_" + cell])
    claim("finding survey", "no error record in trials-b16.jsonl", "trials-b16.jsonl", len(errs), EXPECT["errors"])
    # ---- the pairs -----------------------------------------------------------------------------------------------------------------------------
    pairs = []
    for cell in sorted({r["cell"] for r in T.values() if r["answer_plan"] in ("yes", "no")}):
        for seed in sorted({r["seed"] for r in T.values() if r["cell"] == cell}):
            ys = [r for r in T.values() if r["cell"] == cell and r["seed"] == seed and r["answer_plan"] == "yes" and r.get("turns")]
            ns = [r for r in T.values() if r["cell"] == cell and r["seed"] == seed and r["answer_plan"] == "no" and r.get("turns") and r.get("dialogs") and r["dialogs"][0].get("shot")]
            if ys and ns:
                pairs.append((cell, seed, ys[-1], ns[-1]))
    claim("finding pairs", "pairs (cell, seed) with a Yes run and a No run, each with 4 turns", "trials-b16.jsonl", [(c, s) for c, s, _, _ in pairs], EXPECT["pairs"])
    ident, volat = [], []
    for c, s, y, n in pairs:
        a, b = snap(y["pre_snap"]), snap(n["pre_snap"])
        diff = [BASE + i for i in range(len(a)) if a[i] != b[i]]
        ident.append((c, s, len(a) == len(b), len(diff), all(0x45E614 <= d < 0x45E618 for d in diff)))
        sy, sn = B.ART / "shots" / y["dialogs"][0]["shot"], B.ART / "shots" / n["dialogs"][0]["shot"]
        volat.append(sha(sy) == sha(sn))
    claim("finding pairs", "pre-answer snapshots: bytes differing only inside 0x45E614..0x45E617 (0 to 2 bytes), same length; per pair (cell, seed, same length, differing bytes, all inside the two volatile words)",
          "*_pre.snap.gz", ident, EXPECT["identity"])
    claim("finding pairs", "the Offer of peace screenshot (taken before the click) is byte-identical in Yes and No for every pair", "shots/*dialog-Offer_of_peace*.png", volat, [True] * len(pairs))
    clicks = [(y["dialogs"][0]["answer"], n["dialogs"][0]["answer"], y["answer_click"]["closed"], n["answer_click"]["closed"]) for c, s, y, n in pairs]
    claim("finding pairs", "clicked button recorded: Yes in the Yes run, No in the No run, box closed (verified by the driver) in all", "trials-b16.jsonl", set(clicks), {("Yes", "No", True, True)})
    rel = []
    for c, s, y, n in pairs:
        ry, rn = (open(B.ART / r["post_save"], "rb").read() for r in (y, n))
        rel.append((v_nation(ry, 0, 0x26 + 12), v_nation(rn, 0, 0x26 + 12), v_nation(ry, 6, 0x26), v_nation(rn, 6, 0x26)))
    claim("finding pairs", "relation Rome-Gaul in the Save As right after the answer: -18 (Yes), 3 (No), both directions", "post saves", set(rel), EXPECT["rel_after"])
    news = []
    for c, s, y, n in pairs:
        ry, rn = (v_news(open(B.ART / r["post_save"], "rb").read()) for r in (y, n))
        news.append(("Gaul and Rome have agreed to end their war." in ry[-3:] or "Rome and Gaul have agreed to end their war." in ry[-3:], "agreed to end their war" in " ".join(rn[-3:])))
    claim("finding pairs", "news: the Yes save ends with 'Gaul and Rome have agreed to end their war.' (last 3 lines), the No save has no such line", "post saves", set(news), {(True, False)})
    # turns
    for t in range(1, 5):
        got = []
        for c, s, y, n in pairs:
            fy, fn = (B.ART / "turns" / r["turns"][t - 1]["save"] for r in (y, n))
            by, bn = fy.read_bytes(), fn.read_bytes()
            got.append((c, s, v_nation(by, 0, 0x26 + 12), v_nation(bn, 0, 0x26 + 12), v_nation(by, 0, 0x446), v_nation(bn, 0, 0x446), v_nation(by, 6, 0x446), v_nation(bn, 6, 0x446)))
        claim("finding pairs", "turn %d autosave: (cell, seed, relation Yes, relation No, Rome cities Yes, No, Gaul cities Yes, No)" % t, "turns/*.SAV", got, EXPECT["turn%d" % t])
    # No/No noise
    nn = []
    for (c, s), rs in sorted({(r["cell"], r["seed"]): [] for r in T.values()}.items()):
        pass
    nos = defaultdict(list)
    for r in T.values():
        if r["answer_plan"] == "no" and r.get("turns") and r.get("dialogs"):
            nos[(r["cell"], r["seed"])].append(r)
    for k, rs in sorted(nos.items()):
        if len(rs) >= 2:
            a, b = rs[0], rs[1]
            nn.append((k[0], k[1], (B.ART / a["post_save"]).read_bytes() == (B.ART / b["post_save"]).read_bytes(),
                       [(B.ART / "turns" / x["save"]).read_bytes() == (B.ART / "turns" / y["save"]).read_bytes() for x, y in zip(a["turns"], b["turns"])],
                       all(snap(a["pre_snap"])[i] == snap(b["pre_snap"])[i] or 0x45E614 <= BASE + i < 0x45E618 for i in range(len(snap(a["pre_snap"]))))))
    claim("finding No/No", "No v No on the same save and seed (two fresh processes): the post-answer save, each of the 4 End-turn saves and the pre-answer snapshot (outside the two volatile words) are byte-equal", "post and turns saves, snapshots",
          nn, EXPECT["nonoise"])
    # ---- gates ---------------------------------------------------------------------------------------------------------------------------------
    gate = defaultdict(dict)
    for r in T.values():
        if r["cell"].startswith("loss+") and r["answer_plan"] == "capture":
            gate[r["cell"]][r["seed"]] = box_from_files(r)
    claim("finding gate", "gate cells (L1 edit of the loss cell): box opened per seed", "trials-b16.jsonl + shots/", {k: dict(sorted(v.items())) for k, v in sorted(gate.items())}, EXPECT["gate"])
    gv = {}
    for r in T.values():
        if r["cell"].startswith("loss+") and r["answer_plan"] == "capture":
            b = snap(r["pre_snap"])
            gv[(r["cell"], r["seed"])] = (s_nation(b, 0, 0x440), s_nation(b, 0, 0x446), s_armies(b, 0), s_armies(b, 6))
    claim("finding gate", "gate cells: (Rome unity, Rome city count, armies(Rome), armies(Gaul)) in the snapshot before the answer / at the box, seeds 1, 3, 5", "*_pre.snap.gz",
          {k[0]: v for k, v in gv.items() if k[1] == 1}, EXPECT["gatevals"])
    # ---- hashes / counts / files ---------------------------------------------------------------------------------------------------------------
    bins = [p for p in B.ART.rglob("*") if p.is_file() and p.suffix.lower() in (".sav", ".png", ".gz") and "archives" not in p.parts and not p.name.startswith("_tmp")]
    bad = [p.name for p in bins if shas.get(p.name) != sha(p)]
    claim("finding files", "every binary under artifacts/run-exp-battle-peace/ (saves, snapshots, screenshots) has its SHA-256 in the newest SAVES.v<N>.sha256 and it matches (%d files)" % len(bins), "SAVES.v2.sha256", len(bad), 0)
    manifest = set()
    for f in B.DATA.glob("release-manifest-*.json"):
        for a in json.loads(f.read_text())["archives"].values():
            if a.get("uploaded"):
                manifest |= set(a["members"])
    claim("finding files", "every binary is a member of an uploaded release archive listed in a tracked manifest", "release-manifest-*.json", sorted(p.name for p in bins if p.name not in manifest)[:5], [])
    # tests
    import subprocess
    for mod, e in (("test_driver_battle", EXPECT["tests_driver"]), ("test_battle_b16", EXPECT["tests_b16"]), ("test_battle_stage", EXPECT["tests_stage"])):
        out = subprocess.run([sys.executable, "-m", "tests." + mod], capture_output=True, text=True, cwd=C.ROOT).stdout
        claim("results.md", "%s: %d tests pass, 0 fail" % (mod, e), "tests/" + mod + ".py", (out.count("PASS "), out.count("FAIL ")), (e, 0))
    badr = [r for r in rows if r[5] != "y"]
    out = C.write_new(B.DATA, "b16-claims-audit-%s.md" % C.STAMP,
                      "# B16 claims audit\n\n%d claims, %d mismatches.\n\nInputs: raw snapshots, saves and screenshots, read with `struct` in `b16_audit.py`; `trials-b16.jsonl` for the seed, plan, answer clicked and box text. Not used: `b16_analyze.py`, `b16_run.strategic/rcode`, `state.sav`, `state.battle`.\n\n"
                      "| doc | claim | file | value in files | claimed | match |\n|---|---|---|---|---|---|\n" % (len(rows), len(badr))
                      + "\n".join("| %s | %s | `%s` | %s | %s | %s |" % (w, t_, f_, str(v).replace("|", "/"), str(e).replace("|", "/"), m) for w, t_, f_, v, e, m in rows) + "\n")
    print(out, len(rows), "claims,", len(badr), "mismatches")
    for r in badr:
        print("MISMATCH", r[1][:90], "\n   got ", r[3], "\n   want", r[4])
    sys.exit(1 if badr else 0)


EXPECT = json.loads((Path(__file__).resolve().parent / "b16_expect.json").read_text()) if (Path(__file__).resolve().parent / "b16_expect.json").exists() else {}


if __name__ == "__main__":
    main()
