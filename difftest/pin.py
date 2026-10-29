"""Pinned remake builds for re-checks (owner, 2026-10-30): build any remake commit or tag beside the v0.8.4 build, without
touching it.

    python3 -m difftest.pin build <ref>        # e.g. main, v0.8.5, 6d11e93f
    python3 -m difftest.pin show <short>       # the pin record

A pin is `~/projects/ic2-remake-pin-<short>` (cloned from the bare mirror `~/projects/ic2-remake-pins.git` of the remake's
GitHub repository, detached at the ref's commit, push URL DISABLED; the ref is resolved as a tag, then a branch, then a commit) and `artifacts/diffpin-<short>-build/` (IC2.Cli and the adapter, as in
difftest/README.md), where <short> is the commit's first 8 hex digits. `pin.json` in the build folder records the ref, the
full commit and the paths. The harness uses a pin through IC2_REMAKE and IC2_DIFF_BUILD (`env(short)`).
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_CLONE = Path.home() / "projects/ic2-remake-v084"
DOTNET = Path.home() / ".dotnet/dotnet"


def sh(*cmd, cwd=None, log=None):
    p = subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True,
                       env=dict(os.environ, DOTNET_ROOT=str(DOTNET.parent)))
    if log:
        Path(log).write_text(p.stdout + p.stderr)
    if p.returncode:
        raise SystemExit(f"{' '.join(map(str, cmd))} failed ({p.returncode}): {(p.stdout + p.stderr)[-1500:]}")
    return p.stdout.strip()


def paths(short):
    return Path.home() / f"projects/ic2-remake-pin-{short}", ROOT / f"artifacts/diffpin-{short}-build"


MIRROR = Path.home() / "projects/ic2-remake-pins.git"


def resolve(ref):
    """The commit of `ref` in a local bare mirror of the remake's GitHub repository, fetched first: a tag, then a branch,
    then a commit id. (`git ls-remote <ref>` also matches branches named like a tag, e.g. release-prep/v0.8.4.)"""
    origin = sh("git", "-C", BASE_CLONE, "remote", "get-url", "origin")
    if not MIRROR.exists():
        sh("git", "clone", "--quiet", "--mirror", origin, MIRROR)
        sh("git", "-C", MIRROR, "remote", "set-url", "--push", "origin", "DISABLED")
    sh("git", "-C", MIRROR, "fetch", "--quiet", "--prune", "origin")
    for cand in (f"refs/tags/{ref}", f"refs/heads/{ref}", ref):
        p = subprocess.run(["git", "-C", str(MIRROR), "rev-parse", "--verify", "-q", f"{cand}^{{commit}}"], capture_output=True, text=True)
        if p.returncode == 0:
            return p.stdout.strip(), origin
    raise SystemExit(f"{ref}: no such tag, branch or commit in {MIRROR}")


def build(ref):
    full, origin = resolve(ref)
    short = full[:8]
    clone, out = paths(short)
    if not clone.exists():
        sh("git", "clone", "--quiet", "--no-checkout", MIRROR, clone)
        sh("git", "-C", clone, "remote", "set-url", "origin", origin)
        sh("git", "-C", clone, "remote", "set-url", "--push", "origin", "DISABLED")
    sh("git", "-C", clone, "checkout", "--quiet", "--detach", full)
    out.mkdir(parents=True, exist_ok=True)
    sh(DOTNET, "build", clone / "src/IC2.Cli/IC2.Cli.csproj", "-c", "Release", "--artifacts-path", out / "build",
       log=out / "build-cli.log")
    sh(DOTNET, "build", ROOT / "difftest/remake_adapter", "-c", "Release",
       f"-p:RemakeBuild={out / 'build/bin/IC2.Cli/release'}", "--artifacts-path", out / "adapter", log=out / "build-adapter.log")
    rec = {"ref": ref, "commit": full, "short": full[:8], "remake_dir": str(clone), "build_dir": str(out),
           "subject": sh("git", "-C", clone, "log", "-1", "--format=%s"), "built": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (out / "pin.json").write_text(json.dumps(rec, indent=1))
    return rec


def record(short):
    return json.loads((paths(short)[1] / "pin.json").read_text())


def env(short):
    """The environment that points the harness (difftest/remake.py) at the pin."""
    r = record(short)
    return {"IC2_REMAKE": r["remake_dir"], "IC2_DIFF_BUILD": r["build_dir"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "show"])
    ap.add_argument("ref")
    a = ap.parse_args()
    print(json.dumps(build(a.ref) if a.cmd == "build" else record(a.ref), indent=1))


if __name__ == "__main__":
    sys.exit(main())
