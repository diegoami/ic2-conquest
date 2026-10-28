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
    raise ValueError(op)


def commands(actions):
    names = checkpoint_names(actions)
    out = [f"#checkpoint {names[0]}"]
    for a, name in zip(actions, names[1:]):
        out += [command(a), f"#checkpoint {name}"]
    return "\n".join(out) + "\n"


def run(actions, start, out, log=print):
    """Play the actions from `start` (an original SAV) in the remake; checkpoints and receipt.jsonl go to `out`."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / "commands.txt").write_text(commands(actions))
    env = dict(os.environ, DOTNET_ROOT=str(DOTNET.parent))
    with open(out / "receipt.jsonl", "w") as receipt:
        p = subprocess.run([str(DOTNET), str(ADAPTER), str(REMAKE), str(start), str(start), str(out / "commands.txt"), str(out)],
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
