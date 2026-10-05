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


TESTS = ["loader_offsets", "unity_and_loyalty_bands", "morale_bands", "quality_relation_tribute_sea", "formatters", "army_cost_formulas",
         "coverage_zero_unaccounted", "claims_audit_when_artifacts_exist"]

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
