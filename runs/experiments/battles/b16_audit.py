#!/usr/bin/env python3
"""B16 claims audit. Writes a NEW `b16-claims-audit-<stamp>.md` in the tracked data folder (older ones are kept); exit 1 on any mismatch.

    python3 runs/experiments/battles/b16_audit.py

WHAT IT CHECKS
  1. The finding equals the rendering of `findings/b16-finding.skeleton.md` with every `%%name%%` value computed by `b16_raw.py` from the raw data (a number edited
     by hand, or not computed from the raw data, makes the two differ); the skeleton states no measured number literally (`b16_raw.literal_numbers`).
  2. Raw invariants (booleans computed from the raw data, e.g. "the pre-answer snapshots of every pair differ only inside the volatile words").
  3. Claims about the answer itself, from the post-answer saves and the box-up snapshots: the clicked button, the news line, money/unity/city count unchanged.
  4. The full before/after diff (news included) and the repeat comparisons are recomputed HERE (`b16_raw.fulldiff_raw`, `b16_raw.repeat_raw`); the analysers' files
     are only COMPARED with them (`compare_with_analyser`), never used.
  5. Every file or cell cited by the finding exists; every binary has its SHA-256 in the newest SAVES.v<N>.sha256 and is in an uploaded release archive; the test suites pass.

INPUTS (the complete list; the `test_audit_reads_only_raw_inputs` test greps this file for any other data file name)
  raw         artifacts/run-exp-battle-peace/**  (snapshots, saves, screenshots)                      via b16_raw
  run record  runs/experiments/data/run-exp-battle-peace/trials-b16.jsonl, hooklog-*.csv              via b16_raw (written by the runner at run time)
  raw         findings/b16-finding.skeleton.md, findings/2026-10-05-battle-peace-offer.md, harness/driver.py
  manifest    SAVES.v<N>.sha256 (hashes the audit recomputes and COMPARES), release-manifest-*.json (members the audit COMPARES with the files on disk)
  analyser    the full-diff and repeat JSON files of the analysers: opened ONLY inside `compare_with_analyser`, to compare with the audit's own numbers
NOT read: the pairs, survey-table, hook-table and facts files, b16_expect.json, b16_number_map.json (the last two no longer exist)."""
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b16_raw as R  # noqa: E402
import b16_common as B  # noqa: E402
import common as C  # noqa: E402

rows = []


def claim(doc, text, source, got, want):
    rows.append((doc, text, source, got, want, "y" if got == want else "N"))


def check_finding(text=None, skeleton=None):
    """(ok, detail): the finding text against the rendering of the skeleton from the raw data. `text` lets a test feed an edited copy."""
    text = R.FINDING.read_text() if text is None else text
    out = R.render(R.SKELETON.read_text() if skeleton is None else skeleton)
    if text == out:
        return True, ""
    a, b = text.split("\n"), out.split("\n")
    for i in range(max(len(a), len(b))):
        if i >= len(a) or i >= len(b) or a[i] != b[i]:
            x, y = (a[i] if i < len(a) else "<missing>"), (b[i] if i < len(b) else "<missing>")
            k = next((j for j in range(min(len(x), len(y))) if x[j] != y[j]), min(len(x), len(y)))
            return False, "line %d differs at character %d:\n  finding : ...%s\n  rendered: ...%s" % (i + 1, k, x[max(0, k - 80):k + 80], y[max(0, k - 80):k + 80])
    return False, "differs"


def compare_with_analyser(raw_fd, raw_rp, fd_path=None, rp_path=None):
    """The ONLY place that opens an analyser file. Returns the list of disagreements between the audit's own numbers (`raw_fd` = b16_raw.fulldiff_raw(), `raw_rp` =
    b16_raw.repeat_raw()) and the analysers' JSON files. The analyser output is compared, never used."""
    fd_path = fd_path or sorted(B.DATA.glob("b16-fulldiff-2*.json"))[-1]
    rp_path = rp_path or sorted(B.DATA.glob("b16-repeat-*.json"))[-1]
    fd = json.loads(Path(fd_path).read_text())
    rp = json.loads(Path(rp_path).read_text())
    bad = []
    mine = {r["trial"]: r for r in raw_fd["runs"]}
    theirs = {r["trial"]: r for r in fd["runs"]}
    if set(mine) != set(theirs):
        bad.append("fulldiff: runs differ: %s" % sorted(set(mine) ^ set(theirs)))
    for t in sorted(set(mine) & set(theirs)):
        m, a = mine[t], theirs[t]
        for key, mv, av in (("fields", len(m["fields"]), len(a["fields"])), ("map", m["map"], a["map_cells_changed"]), ("added", m["added"], a["news_added"]), ("dropped", m["dropped"], a["news_dropped"])):
            if mv != av:
                bad.append("fulldiff %s %s: audit %r analyser %r" % (t, key, mv, av))
    if len(raw_rp) != len(rp):
        bad.append("repeat: %d comparisons v analyser %d" % (len(raw_rp), len(rp)))
    mine_r = {(x["a"], x["b"]): x for x in raw_rp}
    for x in rp:
        m = mine_r.get((x["a"], x["b"]))
        if m is None:
            bad.append("repeat: pair %s/%s not in the audit's comparisons" % (x["a"], x["b"]))
            continue
        extra = sum(o[1] for o in x["pre_differing_offsets"] if not R.VOLATILE[0] <= int(o[0], 16) < R.VOLATILE[1])
        if m["regions_equal"] != x["pre_named_regions_equal"] or len(m["outside_volatile"]) != extra:
            bad.append("repeat %s/%s: audit (regions %s, extra bytes %d) analyser (regions %s, extra bytes %d)" % (x["a"], x["b"], m["regions_equal"], len(m["outside_volatile"]), x["pre_named_regions_equal"], extra))
    return bad


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def treasury(snapshot, n):
    return struct.unpack_from("<i", snapshot, R.NAT - R.BASE + n * 1172 + 0x438)[0]


def main():
    T, nerr = R.trials()
    V, S = R.values()
    sk = R.SKELETON.read_text()
    ok, detail = check_finding()
    claim("finding", "the finding equals the rendering of the skeleton with every value computed from the raw data (%d placeholders, %d distinct values)" % (len(R.placeholders(sk)), len(set(R.placeholders(sk)))), "findings + raw data", detail or "equal", "equal")
    claim("finding", "the skeleton states no number literally outside registered literals (references and quoted rules)", "findings/b16-finding.skeleton.md", R.literal_numbers(sk), [])
    claim("finding", "every placeholder of the skeleton has a computed value", "b16_raw.py", sorted(set(R.placeholders(sk)) - set(V)), [])
    for name in ("btn_same_size", "cityword_ok", "ext_readbacks_consistent", "ext_weak_same", "win_cell_same", "ext_tests_all", "loss_tests_all", "snap_lens_equal", "id_all_volatile", "id_regions_equal",
                 "id_png_equal", "rep_regions_equal", "nn_post_equal", "nn_turns_equal", "g_ok", "hook_rule", "reseed_only_open", "rs_unique"):
        claim("invariant", "%s (source: %s)" % (name, S[name]), "raw data", V[name], "True")
    claim("invariant", "win_tests_any is False: the plain D-WIN tests fail in every seed (source: %s)" % S["win_tests_any"], "raw data", V["win_tests_any"], "False")
    for name in ("clicks_other", "turn_errors", "hook_gate_open", "hook_gate_draws", "win_open", "fd_no_fields", "fd_map"):
        claim("invariant", "%s is 0 (source: %s)" % (name, S[name]), "raw data", V[name], "0")
    normal = [r for r in T.values() if r["build"] == "normal"]
    opened = [r for r in normal if r["answer_plan"] in ("capture", "yes", "no") and R.boxed(r)]
    pairs = R.pairs_of(T)
    claim("answer", "clicked button recorded from the click: Yes in every Yes run, No in every No run, box closed, in all pairs", "trials-b16.jsonl",
          sorted({(y["answered"], n["answered"], y["answer_click"]["closed"], n["answer_click"]["closed"]) for _, _, y, n in pairs}), [("Yes", "No", True, True)])
    head = lambda r: "After defeating you in battle Gaul are willing to end their war" if R.state(r)["W"] == 6 else "After losing to you in battle Gaul are willing to end their war"
    claim("answer", "every opened run's box text has the wording of the report that fits its winner (human defeat 'After defeating you', human victory 'After losing to you') and the honourable-peace, YES and NO lines",
          "trials-b16.jsonl box_text", sorted({(head(r) in re.sub("[‘’]", "", r["box_text"]) and "honourable peace with no reparations" in r["box_text"] and "click YES" in r["box_text"] and "click NO" in r["box_text"]) for r in opened}), [True])
    news, chg = [], []
    for c_, sd, y, n in pairs:
        by, bn = (R.rd(B.ART / r["post_save"]) for r in (y, n))
        W, L = ("Gaul", "Rome") if R.state(y)["W"] == 6 else ("Rome", "Gaul")
        news.append(("%s and %s have agreed to end their war." % (W, L) in R.v_news(by)[-3:], "agreed to end their war" in " ".join(R.v_news(bn)[-3:])))
        sn = R.snap(y["pre_snap"])
        pre = [(treasury(sn, k), R.s_nation(sn, k, 0x440), R.s_nation(sn, k, 0x446)) for k in (0, 6)]
        for b_ in (by, bn):
            chg.append(pre == [(R.v_treasury(b_, k), R.v_nation(b_, k, 0x440), R.v_nation(b_, k, 0x446)) for k in (0, 6)])
    claim("answer", "the Yes post save ends with '<Winner> and <Loser> have agreed to end their war.' and the No post save has no such line (every pair)", "post saves", sorted(set(news)), [(True, False)])
    claim("answer", "treasury, unity and city count of Rome and Gaul in each post-answer save equal the box-up snapshot's (no money, unity or city change at the answer, either branch)", "snapshots + post saves", sorted(set(chg)), [True])
    fd, rp = R.fulldiff_raw(), R.repeat_raw()
    claim("analysers", "the analysers' full-diff and repeat files agree with the audit's own recomputation (never used by it): %d diff runs, %d repeat comparisons" % (len(fd["runs"]), len(rp)), "analyser JSON files", compare_with_analyser(fd, rp), [])
    text = R.FINDING.read_text()
    spans = set(re.findall(r"`([^`]*(?:\.(?:png|SAV|csv|json|jsonl|md|py|gz|sha256|txt|log|sh)\b)[^`]*)`", text))
    research = Path.home() / "projects" / "imperial-conquest-2-research" / "docs" / "reports"
    sums = sorted(B.DATA.glob("SAVES.v*.sha256"), key=lambda q: int(q.stem.split(".v")[1].split("-")[0]))[-1]
    shas = {}
    for line in sums.read_text().splitlines():
        h, _, nme = line.partition("  ")
        shas[nme] = h
    missing = []
    for sp in sorted(spans):
        base = sp.split()[0]
        if base.startswith("."):
            continue
        if base.startswith("docs/reports/") or base.endswith("-paths.md"):
            if not (research / Path(base).name).exists():
                missing.append(sp)
        elif "/" in base:
            if not (any(C.ROOT.glob(base)) if "*" in base else (C.ROOT / base).exists()):
                missing.append(sp)
        elif "{" in base or "<" in base:
            continue
        elif "*" in base:
            if not (any(B.DATA.glob(base)) or any(B.ART.rglob(base)) or any(C.ROOT.glob("**/" + base))):
                missing.append(sp)
        elif not ((B.DATA / base).exists() or any(B.ART.rglob(base)) or any(C.ROOT.glob("**/" + base)) or base in shas):
            missing.append(sp)
    claim("files", "every file name or glob cited in a code span of the finding exists (%d distinct spans)" % len(spans), "findings + data", missing, [])
    cells = {c_.split(" ")[0] for c_ in re.findall(r"`((?:loss|win)\+[^`]*)`", text)}
    claim("files", "every cell expression cited in the finding is a cell of trials-b16.jsonl", "trials-b16.jsonl", sorted(cells - {r["cell"] for r in normal}), [])
    bins = [p for p in B.ART.rglob("*") if p.is_file() and p.suffix.lower() in (".sav", ".png", ".gz") and "archives" not in p.parts and not p.name.startswith("_tmp")]
    claim("files", "every binary under artifacts/run-exp-battle-peace/ (%d) has its SHA-256 in %s and it matches" % (len(bins), sums.name), sums.name, sorted(p.name for p in bins if shas.get(p.name) != sha(p))[:5], [])
    members = set()
    for f in B.DATA.glob("release-manifest-*.json"):
        for a in json.loads(f.read_text())["archives"].values():
            if a.get("uploaded"):
                members |= set(a["members"])
    claim("files", "every binary is a member of an uploaded release archive listed in a tracked manifest", "release-manifest-*.json", sorted(p.name for p in bins if p.name not in members)[:5], [])
    for mod in ("test_driver_battle", "test_battle_b16", "test_battle_stage"):
        out = subprocess.run([sys.executable, "-m", "tests." + mod], capture_output=True, text=True, cwd=C.ROOT).stdout
        claim("tests", "%s: no failure (%d pass)" % (mod, out.count("PASS ")), "tests/%s.py" % mod, out.count("FAIL "), 0)
    badr = [r for r in rows if r[5] != "y"]
    out = C.write_new(B.DATA, "b16-claims-audit-%s.md" % C.STAMP,
                      "# B16 claims audit\n\n%d claims, %d mismatches.\n\nThe finding is checked against the rendering of its skeleton from the raw data (first claim); the inputs and what is only compared are listed in the header of `b16_audit.py`. The analysers' files are only compared (claim `analysers`).\n\n"
                      "| doc | claim | source | value in raw data | claimed | match |\n|---|---|---|---|---|---|\n" % (len(rows), len(badr))
                      + "\n".join("| %s | %s | `%s` | %s | %s | %s |" % (w, t_, f_, str(v).replace("|", "/").replace("\n", " ")[:400], str(e).replace("|", "/")[:200], m) for w, t_, f_, v, e, m in rows) + "\n")
    print(out, len(rows), "claims,", len(badr), "mismatches")
    for r in badr:
        print("MISMATCH", r[1][:120], "\n   got ", str(r[3])[:600], "\n   want", str(r[4])[:200])
    sys.exit(1 if badr else 0)


if __name__ == "__main__":
    main()
