#!/usr/bin/env python3
"""The Information-window model (runs/experiments/info_window/panel_model.py) and its checks: the word bands as the code and the DAT give them,
the number formatters, the army cost formulas on a tracked save, the coverage check (0 unaccounted, and it does catch a missing row), and,
when the local capture artifacts exist, the claims audit (0 mismatches).

Needs the game's DAT (IC2_DAT or ~/ic2-work/prefix/drive_c/IC2/Imperial Conquest 2.dat); without it every test reports SKIP.
    python3 -m tests.test_info_window
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runs" / "experiments" / "info_window"))
DATp = os.environ.get("IC2_DAT", str(Path.home() / "ic2-work/prefix/drive_c/IC2/Imperial Conquest 2.dat"))


class Skip(Exception):
    pass


def model():
    if not os.path.exists(DATp):
        raise Skip("no DAT at " + DATp)
    import panel_model as M  # noqa: E402
    return M


def test_loader_offsets():
    M = model()
    assert M.DAT_START == 0x1F2F0
    assert M.TABLES[0x47938C][0] == 0x1F6CA and M.TABLES[0x4793FC][0] == 0x1F738 and M.TABLES[0x4794C8][0] == 0x1F800
    return "DAT_0047938C <- 0x1F6CA, DAT_004793FC <- 0x1F738, DAT_004794C8 <- 0x1F800 from the loader's read sizes"


def test_unity_and_loyalty_bands():
    M = model()
    u = {0: "very low", 499: "very low", 500: "low", 599: "low", 600: "normal", 699: "normal", 700: "high", 799: "high", 800: "very high",
         899: "very high", 900: "excellent", 999: "excellent", 1000: "", 1100: ""}
    for v, w in u.items():
        assert M.unity_word(v) == w, (v, M.unity_word(v))
    lo = {0: "very low", 49: "very low", 50: "low", 59: "low", 60: "normal", 69: "normal", 70: "high", 79: "high", 80: "very high", 89: "very high",
          90: "excellent", 99: "excellent", 100: "", 109: "", -9: "very low", -10: "ite"}
    for v, w in lo.items():
        assert M.loyalty_word(v) == w, (v, M.loyalty_word(v))
    return "unity edges 500/600/700/800/900/1000, loyalty edges 50/60/70/80/90/100, loyalty -10 reads 'ite' (previous table's tail)"


def test_morale_bands():
    M = model()
    m = {48: "very low", 50: "very low", 51: "very low", 54: "very low", 55: "low", 58: "low", 59: "normal", 62: "normal", 63: "high", 66: "high",
         67: "very high", 70: "very high", 71: "excellent", 74: "excellent", 75: ""}
    for v, w in m.items():
        assert M.morale_word(v) == w, (v, M.morale_word(v))
    return "morale edges 55/59/63/67/71/75 (a sixth tier 'excellent' 71-74, blank from 75)"


def test_quality_relation_tribute_sea():
    M = model()
    q = ["not ready"] * 4 + ["very poor", "poor", "average", "good", "very good", "elite", "", ""]
    assert [M.quality_word(i) for i in range(12)] == q
    assert [M.relation_word(v) for v in (-1, 0, 1, 2, 3, 4)] == ["", "", "trade", "ally ", "war  ", ""]
    t = {0: "poor", 10: "poor", 11: "moderate", 30: "moderate", 31: "rich", 100: "rich", 101: "very rich", 10000: "very rich", 10001: None, 65535: None}
    for v, w in t.items():
        assert M.tribute_word(v) == w, (v, M.tribute_word(v))
    return "quality 0-9 index, relation words only for 1-3 (peace blank), tribute word edges 11/31/101/10001"


def test_formatters():
    M = model()
    assert M.f_commas(1234567) == "1,234,567" and M.f_commas(-1500) == "- 1,500" and M.f_commas(0) == "0"
    assert M.f_pop(-5000).strip() == "5,000" and len(M.f_pop(5)) == 12
    assert M.cdiv(-1, 10) == 0 and M.cdiv(-10, 10) == -1 and M.cdiv(-1, 100) == 0
    return "thousands formatters: negative treasury is '- 1,500' (minus, blank, digits); population drops the sign; div truncates toward zero"


def test_army_cost_formulas():
    M = model()
    p = ROOT / "saves" / "run0-start-AUTO0720-seed12345.SAV"
    raw = M.Raw(str(p))
    for i, (reg, merc) in {0: (232, 0), 2: (54, 304), 3: (42, 182), 4: (156, 151)}.items():     # shown in the panels of A4_army_0{0,2,3,4}_left.png (same units)
        lines = dict((c.strip(), v.strip()) for c, v in M.army_lines(raw, i, raw.p["armies"][i]["owner"]))
        assert lines["Regulars cost"].startswith("%d " % reg) and lines["Mercenary pay"].startswith("%d " % merc), (i, lines["Regulars cost"], lines["Mercenary pay"])
    return "Regulars cost and Mercenary pay of armies 0, 2, 3, 4 equal the numbers read in the game"


def test_coverage_zero_unaccounted():
    model()
    import coverage_check as C
    res, bad, _ = C.check()
    assert bad == 0 and len(res) > 200, (bad, len(res))
    res2, bad2, _ = C.check([r for r in C.FR.ROWS if r["id"] not in ("N06", "C05")])
    assert bad2 > 0
    return "%d items, 0 unaccounted; with rows N06 and C05 removed it reports %d unaccounted" % (len(res), bad2)


def test_claims_audit_when_artifacts_exist():
    model()
    import audit
    from iw_lib import ART
    if not os.path.isdir(ART + "saves"):
        raise Skip("no local capture artifacts")
    assert audit.main(False) == 0
    return "claims audit: 0 mismatches over the local captures"


def test_cost_formula_16_bit_narrowing():
    M = model()
    # with a (synthetic) price large enough, trunc(troops/200) x price leaves signed 16 bits: the store into `short sVar4` (F:41084) wraps it
    r, m = M.unit_cost(32000, 500, 0, 0)            # 160 x 500 = 80000 -> i16 = 14464
    ru, mu = M.unit_cost_unrestricted(32000, 500, 0, 0)
    assert (r, ru) == (14464, 80000) and r != ru
    r2, m2 = M.unit_cost(32000, 500, 3, 7)          # mercenary: trunc((14464 x 7) / 5) on the NARROWED value
    r2u, m2u = M.unit_cost_unrestricted(32000, 500, 3, 7)
    assert m2 == 20249 and m2u == 112000 and m2 != m2u, (m2, m2u)
    # negative product wraps the other way; division truncates toward zero
    assert M.unit_cost(-32000, 500, 0, 0)[0] == -14464 and M.unit_cost(1000, 3, 5, 9)[1] == (5 * 3 * 9) // 5
    # real DAT prices (1-4): the narrowing never changes a result
    assert all(M.unit_cost(t, p, 0, 0) == M.unit_cost_unrestricted(t, p, 0, 0) for t in (0, 199, 200, 32767) for p in (1, 2, 3, 4))
    return "narrowed 14464 vs unrestricted 80000; merc 20249 vs 112000; with prices 1-4 identical"


def test_rowcompare_negative_cases():
    import rowcompare as RC
    base = ["Army of Rome", "Regulars cost 232 talents per quarter", "Mercenary pay 0 talents per quarter", "Morale very high"]
    ocr = ["{information"] + base
    assert all(s in ("OK",) for s, _, _ in RC.compare(base, ocr))
    def fails(exp, got, clip=None):
        return any(s in ("MISMATCH", "MISSING", "EXTRA") for s, _, _ in RC.compare(exp, got, clip))
    assert fails(base, ["Army of Rome", "Regulars cost 233 talents per quarter", base[2], base[3]]), "changed number must fail"
    assert fails(base, [base[0], base[1], base[2], "Morale very low"]), "changed adjective must fail"
    assert fails(base, base[:3]), "missing row must fail"
    assert fails(base, base + ["Terrain Plain"]), "extra row must fail"
    assert fails(base, [base[0], base[1], base[2], "Morale very"]), "a clipped word is a mismatch outside a list"
    exp = ["1st Foot Light infantry 4,800 very good"]
    ev = {0: "right"}
    assert RC.compare(exp, ["lst Foot Light infantry 4,800 very"], ev)[0][0] == "CLIPPED-right"
    assert RC.compare(exp, ["lst Foot Light infantry 4,800 very"])[0][0] == "MISMATCH", "no pixel evidence for the row: no clipping"
    assert RC.compare(exp, ["lst Foot Light infantry 4,900 very"], ev)[0][0] == "MISMATCH", "a number inside a clipped row must still match"
    # round-2 counterexamples (Sol): a short header cut to 'Army', and a full-length changed word
    assert RC.compare(["Army of Rome"], ["Army"], {0: "right"})[0][0] == "MISMATCH", "a short row is never a clip"
    assert RC.compare(["Army of Rome"], ["Army"])[0][0] == "MISMATCH"
    assert RC.compare(["Light infantry 1,500 elite"], ["Light infantry 1,500 elitX"], {0: "right"})[0][0] == "MISMATCH", "equal-length changed word"
    assert RC.compare(["Light infantry 1,500 elite"], ["Light infantry 1,500 elitX"])[0][0] == "MISMATCH"
    assert "SCROLLBAR-ARTIFACT" in [s for s, _, _ in RC.compare(["Light infantry 1,500 very poor"], ["Light infantry 1,500 very poor", "<j >|"], {0: "right"})]
    return "changed number, changed adjective, missing row, extra row, clipped word outside a list all fail; clip and ordinal tolerances are narrow"


def test_call_extraction():
    model()
    import coverage_check as C
    body = 'x = FUN_00401000 (a);\n y = FUN_004498b0\t(b, c);\n z = LocalAlloc(0,4); if (x) { while (y) { } } q = "FUN_dead(1)"; v = (short)(w + 1); '
    got = C.calls_of(body, "own")
    assert got == {"FUN_00401000", "FUN_004498b0", "LocalAlloc"}, got
    assert C.calls_of("a = some_helper (1); b = _under_score(2); c = Class_Method(3);", "own") == {"some_helper", "_under_score", "Class_Method"}
    assert "<indirect call>" in C.calls_of("(**(code **)(*piVar1 + 4))(piVar1,&DAT_00479590,0x2c5c);", "own")
    assert C.calls_of("void own(int a) { own2(a); }", "own") == {"own2"}
    for form in ("(*callback)();", "(*callback)(0);", "(*cb)((1 + 2));", "tbl[3](x);", "(f)(0);", "(*vt[2])();"):
        assert C.calls_of(form, "own") == {"<indirect call>"}, form
    assert C.calls_of("x = (short)(a + 1); y = (char *)(p + 2); z = (undefined4 *)0x45; if (a) (b); while (c) { }", "own") == set()
    for n, d in C.load().items():
        assert "<indirect call>" not in d["call"], n          # none of the seven routines has an indirect call
    return "spaced, tabbed, differently named and indirect calls are extracted; keywords, casts and literals are not"


def test_audit_statuses_each_discrepancy_is_counted():
    model()
    import audit, csv
    from iw_lib import ART, DATA
    if not os.path.isdir(ART + "saves"):
        raise Skip("no local capture artifacts")
    rows, excl, occ, gd, ext, scroll = audit.load_inputs()
    base = next(r for r in rows if r["png"] == "A4_army_02_left.png")             # own army with mercenaries: Moves 6, Morale very low, Mercenary pay 304
    raws = {}
    lr = lambda s: raws.get(s) or raws.setdefault(s, audit.M.Raw(audit.find_save(s)))
    def run(mut, kind=None, ex=None, oc=None, g=None, extents=None, sc=None):
        r = dict(base); r["png"] = "INJECT.png"; r["ocr"] = mut(base["ocr"])
        if kind: r["kind"] = kind
        out, cnt, _ = audit.evaluate([r], lr, ex or {}, oc or {}, g or {}, extents or {}, sc or {})
        return cnt
    assert run(lambda o: o)["OK"] > 5 and not any(k in run(lambda o: o) for k in audit.FAILING_STATUSES)
    assert run(lambda o: o.replace("Mercenary pay 304", "Mercenary pay 305")).get("MISMATCH") == 1
    assert run(lambda o: o.replace("Morale very low", "Morale low")).get("MISMATCH") == 1
    assert run(lambda o: o.replace(" | Money 39 talents", "")).get("MISSING", 0) >= 1
    assert run(lambda o: o + " | No. of cats 4").get("EXTRA") == 1
    cnt = run(lambda o: o, kind="bogus_kind"); assert cnt == {"NOT-MODELLED": 1}, cnt          # an unmodelled kind is counted as failing
    assert audit.FAILING_STATUSES == ("MISMATCH", "MISSING", "EXTRA", "NOT-MODELLED")
    assert run(lambda o: o + " | <j >|").get("EXTRA") == 1                                      # a scroll-bar row that is not listed is an extra row
    assert run(lambda o: o + " | <j >|", sc={"INJECT.png": {"<j >|"}}).get("SCROLLBAR-ARTIFACT") == 1
    assert run(lambda o: o, ex={"INJECT.png": "x"}) == {"EXCLUDED-listed": 1}
    ocr_bad = lambda o: o.replace("Morale very low", "Morale very lcw")
    assert run(ocr_bad, oc={"INJECT.png": [("Morale very low", "Morale very lcw")]}).get("CORRECTED-OCR") == 1
    assert run(ocr_bad, g={"INJECT.png": [("Morale very low", "Morale very lcw")]}).get("NOT-MODELLED-OUTPUT") == 1
    assert run(lambda o: o.replace("Morale very low", "Morale very lcw")).get("MISMATCH") == 1
    return "each kind of discrepancy lands in its own counted status; the failing ones are MISMATCH, MISSING, EXTRA, NOT-MODELLED"


def test_audit_clipping_needs_pixel_evidence():
    model()
    import audit
    from iw_lib import ART
    if not os.path.isdir(ART + "saves"):
        raise Skip("no local capture artifacts")
    rows, excl, occ, gd, ext, scroll = audit.load_inputs()
    base = next(r for r in rows if r["png"] == "A6_army0_right.png")
    raw = audit.M.Raw(audit.find_save(base["save"]))
    r = dict(base); r["png"] = "INJECT2.png"; r["ocr"] = base["ocr"].replace("not ready", "not")             # cut the last word of one row
    out, cnt, _ = audit.evaluate([r], lambda s: raw, {}, {}, {}, {}, {})
    assert cnt.get("MISMATCH", 0) >= 1 and "CLIPPED-right" not in cnt, cnt                                      # no extent evidence: mismatch
    return "a shortened row without row_extents evidence is a MISMATCH"


TESTS = ["loader_offsets", "unity_and_loyalty_bands", "morale_bands", "quality_relation_tribute_sea", "formatters", "army_cost_formulas",
         "audit_statuses_each_discrepancy_is_counted", "audit_clipping_needs_pixel_evidence", "cost_formula_16_bit_narrowing", "rowcompare_negative_cases", "call_extraction", "coverage_zero_unaccounted", "claims_audit_when_artifacts_exist"]

if __name__ == "__main__":
    bad = 0
    for n in sys.argv[1:] or TESTS:
        try:
            print(f"PASS {n}: {globals()['test_' + n]()}")
        except Skip as e:
            print(f"SKIP {n}: {e}")
        except Exception as e:  # noqa: BLE001
            bad += 1
            print(f"FAIL {n}: {type(e).__name__}: {e}")
    sys.exit(1 if bad else 0)
