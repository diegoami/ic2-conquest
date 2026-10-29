#!/usr/bin/env python3
"""Research #25 (delegated 2026-10-30): which merged tactical fix removed which residual series of the 318-series recorded
corpus? The unchanged #157 corpus replay (runs/experiments/battle-current157/Corpus.cs: GoldenReplay + DrawComparison, strict,
no KnownFailures) is compiled against Main's engine and test helpers at each pin and run on the same private fixtures.

    python3 runs/experiments/tactical25-attrib/run_pins.py --fixtures PRIVATE_CORPUS --version vN

Pins: 257f2d2 (PR1156, the #25 inventory: 282 exact / 36 residual), a99d414 (PR1371's parent: 228 commits later, about
20 tactical files changed), f0cd629 (PR1371 merged: later-pass slot order),
3c18600 (PR1387 merged: captured Walk target + positive-troop shot guard), b593c6e (the #157 audit pin: 318/318).
Sources come from `git archive` of the read-only clone (no checkout); builds go to the ignored artifacts folder. Per-series rows
stay private (artifacts/.../private); the tracked receipt holds counts and the list of series whose pass/fail changes between
consecutive pins (series names only: no fixture bytes, hashes or paths).
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLONE = Path.home() / "projects/ic2-remake-v084"
ART = ROOT / "artifacts/run-exp-tactical25-attrib"
DATA = ROOT / "runs/experiments/data/run-exp-tactical25-attrib"
DOTNET = Path.home() / ".dotnet/dotnet"
PINS = [("257f2d2", "257f2d2cd7510451d229a983553a54b89065b06c", "PR1156: the #25 inventory pin"),
        ("a99d414", "a99d414e5710fccfe674636ef1248282ad100555", "the commit before PR1371 (228 commits after PR1156)"),
        ("f0cd629", "f0cd6296400f132d1387d717d5f767ace6834ad2", "PR1371 merged: later-pass slot order (T206)"),
        ("3c18600", "3c1860079db6dd9b1fb11ceb8b726c7fd95293ac", "PR1387 merged: captured Walk target, positive-troop shot (#1377)"),
        ("b593c6e", "b593c6e28939c1c7154f9a41d0436a8f14f352dc", "the #157 audit pin")]


def run(cmd, log, env=None):
    with open(log, "w") as f:
        return subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, env=env).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", type=Path, required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--pins", nargs="*", help="sha:label pairs to use instead of the default PINS, in order")
    a = ap.parse_args()
    pins = [(p.split(":", 1)[0][:7], p.split(":", 1)[0], p.split(":", 1)[1] if ":" in p else "") for p in a.pins] if a.pins else PINS
    DATA.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, DOTNET_ROOT=str(DOTNET.parent), IC2_FIXTURES_DIR=str(a.fixtures.resolve()))
    results = []
    for short, sha, what in pins:
        base = ART / f"{a.version}-{short}"
        if (base / "rows.jsonl").exists():
            rows = [json.loads(l) for l in (base / "rows.jsonl").read_text().splitlines() if l.strip()]
        else:
            src, tool, harness = base / "src", base / "tool", base / "harness"
            src.mkdir(parents=True, exist_ok=False)
            arc = subprocess.run(["git", "-C", str(CLONE), "archive", sha], capture_output=True, check=True).stdout
            subprocess.run(["tar", "-x", "-C", str(src)], input=arc, check=True)
            tool.mkdir()
            shutil.copy(ROOT / "runs/experiments/battle-current157/Corpus.cs", tool / "Corpus.cs")
            (tool / "Corpus.csproj").write_text(
                '<Project Sdk="Microsoft.NET.Sdk">\n <PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework>'
                '<ImplicitUsings>enable</ImplicitUsings><Nullable>enable</Nullable><EnableDefaultCompileItems>false</EnableDefaultCompileItems>'
                '</PropertyGroup>\n <ItemGroup><Compile Include="Corpus.cs"/><ProjectReference Include="'
                + str(src / "tests/IC2.Engine.Tests/IC2.Engine.Tests.csproj") + '"/></ItemGroup>\n</Project>\n')
            rc = run([str(DOTNET), "build", str(tool / "Corpus.csproj"), "-c", "Debug", "--artifacts-path", str(base / "build")],
                     base / "build.log", env)
            if rc:
                results.append({"pin": short, "sha": sha, "what": what, "build_failed": True})
                continue
            harness.mkdir()
            (harness / "IC2.sln").write_text("# asset-locator marker\n")
            (harness / "data").symlink_to(src / "data", target_is_directory=True)
            shutil.copytree(base / "build/bin/Corpus/debug", harness / "bin")
            rc = run([str(DOTNET), str(harness / "bin/Corpus.dll"), str(base / "rows.jsonl"), str(base / "summary.json")],
                     base / "execution.log", env)
            rows = [json.loads(l) for l in (base / "rows.jsonl").read_text().splitlines() if l.strip()] if (base / "rows.jsonl").exists() else []
        passed = {r["trial"] for r in rows if r["stateEqual"] and r["drawsEqual"]}
        results.append({"pin": short, "sha": sha, "what": what, "trials": len(rows), "exact": len(passed),
                        "state_equal": sum(1 for r in rows if r["stateEqual"]), "draws_equal": sum(1 for r in rows if r["drawsEqual"]),
                        "residual": sorted(r["trial"] for r in rows if not (r["stateEqual"] and r["drawsEqual"]))})
    for prev, cur in zip(results, results[1:]):
        if "residual" in prev and "residual" in cur:
            cur["fixed_since_previous"] = sorted(set(prev["residual"]) - set(cur["residual"]))
            cur["broken_since_previous"] = sorted(set(cur["residual"]) - set(prev["residual"]))
    receipt = {"version": a.version, "corpus_tool_sha256": hashlib.sha256((ROOT / "runs/experiments/battle-current157/Corpus.cs").read_bytes()).hexdigest(),
               "fixtures": "private pinned corpus (revision 6319802a per the #157 receipt); not published", "pins": results}
    out = DATA / f"pins-{a.version}.json"
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.write_text(json.dumps(receipt, indent=1))
    for r in results:
        print(r["pin"], r.get("what"), "BUILD FAILED" if r.get("build_failed") else f"exact {r['exact']}/{r['trials']} residual {len(r['residual'])}",
              f"fixed {len(r.get('fixed_since_previous', []))}" if "fixed_since_previous" in r else "")


if __name__ == "__main__":
    main()
