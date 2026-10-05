#!/usr/bin/env python3
"""B11 pipeline for the B5 re-run (task Work 4): rounds of hooked battles, and after EACH round, in this order: the exchange replay of the round's battles, the
inertness check against the B5 baseline (any difference STOPS the pipeline), the release archive and its upload, and the commit + push of the measurements (rule 6).

    python3 runs/experiments/battles/b11_pipeline.py FIRST LAST [--size 48] [--workers 6]       # rounds FIRST..LAST of the pairs file

Needs the b11_common.py environment variables (IC2_WORK of worker 1, DISPLAY_IC2). A round whose trials did not all end `ok` gets ONE more pass with --redo-errors for those
(a new line is appended; the error lines stay). A failed release call (HTTP 403 or any) is recorded: the exact command is written to `RELEASE-PENDING.txt` in the data folder and
the pipeline goes on; it never retries another way. IC2_RELEASE_TOKEN is not used here (the default gh authentication worked in this session) and is never printed.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b11_batch as BA  # noqa: E402
import b11_common as B  # noqa: E402
import b11_compare as CP  # noqa: E402

C = B.C
HERE = Path(__file__).resolve().parent
ROOT = C.ROOT


def sh(*args, env=None, check=False):
    r = subprocess.run(list(args), cwd=ROOT, env=env or os.environ, capture_output=True, text=True)
    return r


def ok_tags():
    done = set()
    for line in (C.DATA / "trials-b11.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("status") == "ok":
                done.add(r["trial"])
    return done


def one_round(n, size, workers, rep=1):
    prs = BA.round_pairs(n, size)
    tags = ["%s_s%d_r%d_hook" % (c, s, rep) for c, s in prs]
    BA.run_round(n, size, workers, rep)
    missing = [t for t in tags if t not in ok_tags()]
    if missing:
        print("round", n, "not ok:", missing, "- one more pass", flush=True)
        redo = [(c, s) for (c, s), t in zip(prs, tags) if t in missing]
        f = C.DATA / ("pairs-round%02d-redo-%s.txt" % (n, time.strftime("%Y%m%d-%H%M%S")))
        f.write_text("".join("%s %d\n" % x for x in redo))
        env = dict(os.environ, B11_WORKER="-redo")
        subprocess.run([sys.executable, str(HERE / "b11_run.py"), "run", "hook", "--pairs-file", str(f), "--rep", str(rep), "--redo-errors"], cwd=ROOT, env=env)
        missing = [t for t in tags if t not in ok_tags()]
    have = [t for t in tags if t in ok_tags()]
    # 1. exchange replay of the round's battles (tracked outputs)
    r = sh(sys.executable, str(HERE / "b11_exchange.py"), *have)
    print(r.stdout[-600:], r.stderr[-300:], flush=True)
    # 2. inertness against the B5 baseline, in memory: a difference stops everything
    base_f = sorted(C.DATA.glob("b5-baseline-*.json"))[-1]
    base = json.loads(base_f.read_text())["baseline"]
    trials = {}
    for line in (C.DATA / "trials-b11.jsonl").read_text().splitlines():
        if line.strip():
            t = json.loads(line)
            if t.get("status") == "ok":
                trials[t["trial"]] = t
    bad = []
    for t in have:
        rec = trials[t]
        b = base.get("%s_s%d_r1" % (rec["cell"], rec["seed"]))
        if b is None or b["series_sha256"] != [s["sha256"] for s in rec["series"]] or b["post_sha256"] != rec["post_sha256"]:
            bad.append(t)
    print("round", n, "inertness vs B5:", len(have) - len(bad), "identical,", len(bad), "different", bad, flush=True)
    # 3. archive + release
    tgz, man = BA.pack(n, size, rep)
    up = sh("gh", "release", "upload", "run-exp-battle-hook", str(tgz), "--repo", "diegoami/ic2-conquest")
    if up.returncode != 0:
        cmd = "gh release upload run-exp-battle-hook %s --repo diegoami/ic2-conquest" % tgz
        C.write_new(C.DATA, "RELEASE-PENDING-round%02d.txt" % n, "upload failed (%s); run by hand:\n%s\n" % (up.stderr.strip()[:300], cmd))
        print("release upload FAILED, command recorded", flush=True)
    else:
        print("uploaded", tgz.name, flush=True)
    # 4. commit + push the measurements (rule 6)
    a = sh(sys.executable, str(ROOT / "scripts" / "archive_measurements.py"), "run-exp-battle-hook", "--commit", "--trailer", "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
    print(a.stdout[-300:], a.stderr[-300:], flush=True)
    return missing, bad


def main():
    a = sys.argv[1:]
    first, last = int(a[0]), int(a[1])
    size = BA.opt(a, "--size", 48)
    workers = BA.opt(a, "--workers", 6)
    rep = BA.opt(a, "--rep", 1)
    for n in range(first, last + 1):
        t0 = time.time()
        missing, bad = one_round(n, size, workers, rep)
        print("== round", n, "done in", round(time.time() - t0), "s; not ok:", missing, "; not inert:", bad, flush=True)
        if bad:
            print("STOP: a hooked battle differs from its unhooked B5 battle", flush=True)
            sys.exit(3)


if __name__ == "__main__":
    main()
