"""Remake side of the differential harness (#229): translate actions to remake commands and run the adapter.

The adapter (`difftest/remake_adapter`) imports the original start SAV, submits the commands and, after every
action, writes the native save and the state exported to the original format (`aNNN.SAV`), which
`difftest/compare.py` reads with the same parser as the original's own saves.
"""
import json
import os
import subprocess
from pathlib import Path

from difftest.actions import UNIT_TYPES, checkpoint_names

ROOT = Path(__file__).resolve().parents[1]
REMAKE = Path(os.environ.get("IC2_REMAKE", Path.home() / "projects/ic2-remake-v084"))
BUILD = Path(os.environ.get("IC2_DIFF_BUILD", ROOT / "artifacts/diff084-build"))
ADAPTER = BUILD / "adapter/bin/RemakeAdapter/release/RemakeAdapter.dll"
DOTNET = Path.home() / ".dotnet/dotnet"


def command(a):
    op = a["op"]
    if op == "set_tax":
        return f"set-tax {a['percent']}"
    if op == "move":
        return f"move {{army:{a['army']}}} {a['x']} {a['y']}"
    if op == "recruit":
        return f"recruit-standing {{city:{a['city']}}} {UNIT_TYPES[a['type']]} {a['troops']}"
    if op == "end_turn":
        return "end"
    if op == "relation":
        return {"war": "declare-war", "peace": "make-peace", "trade": "propose-trade", "ally": "propose-alliance"}[a["kind"]] \
            + f" {{nation:{a['nation']}}}"
    if op == "fortify":
        return f"order-city {{city:{a['city']}}} fortify {a['points']}"
    if op == "disband_army":
        return f"disband-army {{army:{a['army']}}}"
    if op == "split_army":
        return f"split-army {{army:{a['army']}}} {{newarmy}} {','.join(str(u) for u in a['units'])}"
    if op == "join_armies":
        return f"join-armies {{army:{a['army']}}} {{army:{a['partner']}}}"
    if op == "buy_supply":
        return f"buy {{army:{a['army']}}} {{city:{a['city']}}} {a['tons']}"
    if op == "build_fleet":
        return f"order-fleet {{buildcity}} {a['ships']} {{newfleet}}"
    if op == "disband_slot":
        return f"disband-slot {a['slot']}"
    if op == "hire_mercenary":
        return f"hire-mercenary {{army:{a['army']}}} {a['pool']}"
    if op == "move_fleet":
        return f"move-fleet {{fleet:{a['fleet']}}} {a['x']} {a['y']}"
    if op == "attack_fleet":
        return f"attack-fleet {{fleet:{a['fleet']}}} {{fleet:{a['target']}}}"
    if op == "besiege":
        return f"besiege-city {{army:{a['army']}}} {{city:{a['city']}}}"
    if op == "attack_army":
        return f"attack-army {{army:{a['army']}}} {{army:{a['target']}}}"
    if op == "embark":
        return f"embark-army {{army:{a['army']}}} {{fleet:{a['fleet']}}}"
    if op == "disembark":
        return f"disembark-army {{army:{a['army']}}} {a['x']} {a['y']}"
    if op == "repair_fleet":
        return f"repair-fleet {{fleet:{a['fleet']}}} {a['points']}"
    if op == "scuttle_fleet":
        return f"scuttle-fleet {{fleet:{a['fleet']}}}"
    if op == "split_fleet":
        return f"split-fleet {{fleet:{a['fleet']}}} {{newfleet}} {a['ships']}"
    if op == "join_fleets":
        return f"join-fleets {{fleet:{a['fleet']}}} {{fleet:{a['partner']}}}"
    if op == "transfer_ships":
        return f"fleet-transfer {{fleet:{a['fleet']}}} {{fleet:{a['partner']}}} {a['ships']} 0 0"
    if op == "mobilize":
        return f"mobilize {a['slot']} {{newarmy}}"
    if op == "disband_unit":
        return f"disband-unit {{army:{a['army']}}} {a['unit']}"
    if op == "join_units":
        return f"join-units {{army:{a['army']}}} " + " ".join(str(u) for u in a["units"])
    if op == "transfer_units":
        return f"army-transfer {{army:{a['army']}}} {{army:{a['partner']}}} units={a['unit']}"
    raise ValueError(op)


def commands(actions):
    names = checkpoint_names(actions)
    out = [f"#checkpoint {names[0]}"]
    for a, name in zip(actions, names[1:]):
        out += [command(a), f"#checkpoint {name}"]
    return "\n".join(out) + "\n"


def run(actions, start, out, log=print, seed=None, options=(), template=None):
    """Play the actions from `start` (an original SAV, or a native save written by an earlier run) in the remake;
    checkpoints and receipt.jsonl go to `out`. `template` is the original SAV whose interface settings the exports
    reuse (default: `start`, which must then be a SAV)."""
    template = template or start
    if not str(template).upper().endswith(".SAV"):
        raise ValueError("a native start needs an original SAV as template")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "commands.txt").write_text(commands(actions))
    env = dict(os.environ, DOTNET_ROOT=str(DOTNET.parent))
    with open(out / "receipt.jsonl", "w") as receipt:
        p = subprocess.run([str(DOTNET), str(ADAPTER), str(REMAKE), str(start), str(template), str(out / "commands.txt"), str(out)]
                           + ([f"seed={seed}"] if seed is not None else []) + list(options),
                           stdout=receipt, stderr=subprocess.PIPE, text=True, env=env)
    (out / "stderr.txt").write_text(p.stderr)
    events = [json.loads(l) for l in (out / "receipt.jsonl").read_text().splitlines() if l.strip()]
    if p.returncode or not events or events[-1].get("kind") != "done":
        raise RuntimeError(f"remake adapter failed (exit {p.returncode}): {p.stderr[-2000:]}")
    results = []
    for e in events:
        if e["kind"] == "command":
            results.append({"command": e.get("resolved", e["command"]), "reply": e.get("lines"), "error": e.get("error")})
    log(f"remake: {len(results)} actions, {sum(1 for e in events if e['kind'] == 'checkpoint')} checkpoints in {out}")
    return results
