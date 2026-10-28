"""Play one action script in one game (#229).

    python3 -m difftest.run original SCRIPT START.SAV OUT_DIR --seed 12345
    python3 -m difftest.run remake   SCRIPT START.SAV OUT_DIR

OUT_DIR must not exist (a re-run writes a new folder; nothing measured is overwritten). It receives one
original-format save per checkpoint (aNNN.SAV), receipt.jsonl, and run.json with the inputs' hashes.
Compare two runs with `python3 -m difftest.report`.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from difftest import actions as act  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("side", choices=["original", "remake"])
    ap.add_argument("script")
    ap.add_argument("start")
    ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=12345, help="original: startup RandSeed (the remake's stream comes from the import)")
    ap.add_argument("--tag", help="original: prefix of the in-game save names (default: out folder name)")
    a = ap.parse_args(argv)
    header, actions = act.load(a.script)
    out = Path(a.out)
    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    if a.side == "original":
        from difftest import original
        results = original.run(actions, a.start, out, a.seed, a.tag or out.name)
        from harness.driver import EXE, G
        pins = {"exe": str(EXE), "exe_sha256": sha(G / EXE)}
    else:
        from difftest import remake
        results = remake.run(actions, a.start, out)
        pins = {"remake": str(remake.REMAKE), "remake_commit": subprocess.run(
            ["git", "-C", str(remake.REMAKE), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
            "adapter_sha256": sha(remake.ADAPTER)}
    run = {"side": a.side, "script": a.script, "script_sha256": sha(a.script), "header": header,
           "start": a.start, "start_sha256": sha(a.start), "seed": a.seed if a.side == "original" else None,
           "conquest_commit": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
           "pins": pins, "started": started, "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "actions": len(actions), "errors": sum(1 for r in results if r.get("error"))}
    (out / "run.json").write_text(json.dumps(run, indent=1, default=str))
    print(json.dumps({k: run[k] for k in ("side", "actions", "errors", "finished")}))


if __name__ == "__main__":
    main()
