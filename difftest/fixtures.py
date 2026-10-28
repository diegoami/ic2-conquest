"""Start saves built once in the original for the differential tests (#233, #232).

    python3 -m difftest.fixtures siege-felsina OUT.SAV

siege-felsina: BASE.SAV (Rome, 270 BC), seed 12345; army 0 to (99,34), End turn, then toward Felsina (Gaul, at
war) until adjacent, as tests/test_orders.py test_attack does; saved before the siege. Both games then start the
siege from this same save. The fixture is written once (an existing OUT is refused) and its receipt is
OUT with .json.
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from harness.driver import G, Game  # noqa: E402
from state.sav import load  # noqa: E402

BASE = Path.home() / "ic2-work/fixtures/BASE.SAV"


def siege_felsina(out):
    g = Game()
    moved = g.move_aside(sorted(G.glob("AUTO*")))
    log = {"start": str(BASE), "seed": 12345, "moved_aside": str(moved) if moved else None, "steps": []}
    log["popups"] = g.load(BASE, seed=12345)
    felsina = next(c for c in load(BASE)["cities"] if c["name"] == "Felsina")
    pos, texts = g.move(0, 99, 34)
    log["steps"].append({"move": [99, 34], "to": pos, "texts": texts})
    name, texts = g.end_turn()
    log["steps"].append({"end_turn": str(name), "texts": texts})
    for step in [(99, 33), (99, 32)]:
        x, y = g.army_pos(0)
        if max(abs(x - felsina["x"]), abs(y - felsina["y"])) == 1:
            break
        pos, texts = g.move(0, *step)
        log["steps"].append({"move": list(step), "to": pos, "texts": texts})
    x, y = g.army_pos(0)
    if max(abs(x - felsina["x"]), abs(y - felsina["y"])) != 1:
        raise SystemExit(f"army 0 at {x},{y} is not next to Felsina")
    saved = g.save_as(f"FIX-siege-felsina-{time.strftime('%Y%m%d-%H%M%S')}.SAV")
    shutil.copy(saved, out)
    s = load(out)
    log.update(saved=str(saved), date=s["date"], army0={k: s["armies"][0][k] for k in ("x", "y", "moves", "troops", "supplies")})
    Path(out).with_suffix(".json").write_text(json.dumps(log, indent=1, default=str))
    g.kill()
    return log


if __name__ == "__main__":
    kind, out = sys.argv[1], Path(sys.argv[2])
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    print(json.dumps({"siege-felsina": siege_felsina}[kind](out), default=str)[:600])
