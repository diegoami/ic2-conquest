"""Original-side checks 2, 3, 5, 6, 7, 8, 9, 10 of the v0.5.0 gap analysis (rows_g1.md "Original-side checks needed"; issue #78).
Usage: python3 g1_checks.py <case> [args]. One fresh Wine process per case. Cases:
  G2_merc    Balance sheet with a mercenary unit on the payroll (L1-staged merc unit; control: the same save without it)
  G2_fleet   Balance sheet "Fleet" line with a fleet under construction (natural: Build fleet) and with a finished fleet (PORT save)
  G2_debt    Debt limit display rounding at several wealth values (L1-staged wealth)
  G2_depose  Deposition test at the start of the human's turn: unrounded or rounded Debt limit (L1-staged treasury, then End turn)
  G3_cap     Trade refusals (L1-staged relations): own 3-partner cap, target with 3 partners, controls
Staging is L1 and labelled: only named save fields are patched (stage.py ops and g1_lib helpers), army positions never."""
import sys
from g1_lib import *
import g1_lib

hook_environment()
g = Game()


def partner_unit_name(n): return f"{n} Battalion"


try:
    if CASE == "G2_merc":
        g.load(START, seed=12345)
        log("loaded", save=START.name, seed_line=g.seed_line, army0=g.army_state(0))
        balance_sheet(g, "control_no_merc"); save(g, "control_loaded.SAV")
        variants = {"li": ("merc_li3000_q6", add_unit(0, 11, "li", 3000, 6, "Gallic Foot  Battalion")),
                    "hc": ("merc_hc2400_q9", add_unit(0, 35, "hc", 2400, 9, "Egyptian Dragoons  Battalion")),
                    "hi": ("merc_hi4000_q8", add_unit(0, 11, "hi", 4000, 8, "Gallic Guards  Battalion"))}
        for tag, extra in [variants[sys.argv[2]]]:
            src = staged(START, [], tag, extra)
            g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(2)
            log("alive", pid=g.pid, proc=Path(f"/proc/{g.pid}").exists(), windows=windows(g))
            log("opened_staged", tag=tag, save=src.name, army0_slots=[(k, struct.unpack_from("<4h", g.army_rec(0), 16 + 32 * k)) for k in range(20)
                                                                       if struct.unpack_from("<h", g.army_rec(0), 16 + 32 * k + 4)[0] > 0])
            balance_sheet(g, tag)
    elif CASE == "G2_fleet":
        g.load(START, seed=12345)
        log("loaded", save=START.name, seed_line=g.seed_line)
        balance_sheet(g, "before_build")
        log("fleets_before", fleets=[g.fleet_state(i) for i in range(g.i16(0x4A0326))])
        texts = g.build_fleet(2)
        log("build_fleet", texts=texts, notices=g.build_fleet_notices, root=shot(g, "after_build"),
            fleets=[(i, g.fleet_state(i), g.fleet_rec(i).hex()) for i in range(g.i16(0x4A0326))])
        balance_sheet(g, "fleet_under_construction"); save(g, "under_construction.SAV")
        g.open(PORT); g.wait(g.loaded, 20, "loaded"); time.sleep(1)
        log("opened", save=PORT.name, fleets=[(i, g.fleet_state(i), g.fleet_rec(i).hex()) for i in range(g.i16(0x4A0326))])
        balance_sheet(g, "port_save_finished_fleets")
    elif CASE == "G2_debt":
        wealths = [2_577_000, 2_400_000, 2_499_999, 2_500_500, 3_000_000, 6_000_000, 9_999_999, 10_000_000, 12_000_000]
        first = True
        for w in wealths:
            src = staged(START, [], f"wealth{w}", set_wealth(0, w))
            if first: g.load(src, seed=12345); first = False
            else: g.open(src); g.wait(g.loaded, 20, "loaded"); time.sleep(1)
            rd, mem = balance_sheet(g, f"wealth{w}")
            log("debt_summary", wealth=w, displayed=rd["debt_limit"]["value"], unrounded=w // 500, memory_formula=mem["debt_limit_displayed"])
    elif CASE == "G2_depose":
        # treasury relative to the debt line of wealth 2,577,000: unrounded 5154 (deposed below -5154), displayed/rounded 5000 (deposed below -5000)
        tag, treasury = sys.argv[2], int(sys.argv[3])
        src = staged(START, [("treasury", 0, treasury)], tag, set_wealth(0, 2_577_000))
        g.load(src, seed=12345)
        log("loaded", tag=tag, treasury_staged=treasury, memory=balance_from_memory(g))
        balance_sheet(g, tag + "_before")
        try:
            name, texts = g.end_turn()
            log("end_turn_ok", autosave=name, texts=texts, memory_after=balance_from_memory(g), turn=g.turn_number(), root=shot(g, tag + "_after_end_turn"))
        except drv.GameOver as e:
            log("game_over", text=e.text, windows=windows(g), root=shot(g, tag + "_game_over"), memory=balance_from_memory(g))
        except DriverError as e:
            log("end_turn_error", error=repr(e), boxes=boxes(g), windows=windows(g))
    else:
        raise SystemExit("unknown case " + CASE)
    log("done")
except Exception as e:
    log("error", error=repr(e))
    try: log("error_state", shot=shot(g, "error"), boxes=boxes(g))
    except Exception: pass
    raise
finally:
    g.kill()
