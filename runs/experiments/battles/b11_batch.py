#!/usr/bin/env python3
"""B11 batch driver (task Work 4): re-run the B5 cells and seeds with the hook, in rounds, on several PRIVATE game folders and displays in parallel.

    python3 runs/experiments/battles/b11_batch.py plan [BASELINE.json]          # the (cell, seed) list = rep 1 of every B5 trial in the baseline file -> pairs-<stamp>.txt
    python3 runs/experiments/battles/b11_batch.py round N [--size 45] [--workers 5] # run round N (pairs [(N-1)*size, N*size)) split over the workers; waits for all
    python3 runs/experiments/battles/b11_batch.py packtags LABEL TAG...         # the same for an explicit list of trial tags
    python3 runs/experiments/battles/b11_batch.py pack N [--size 45]            # tar.gz of round N's saves/shots/raw buffers + a tracked manifest (name, size, SHA-256 of
                                                                                #   the archive and of every member); prints the exact `gh release` command

Worker k runs `b11_run.py run hook --pairs-file ...` with IC2_WORK=<its copy of the game folder> and DISPLAY_IC2=<its display>. The worker table is WORKERS below (the
folders are copies of the prefix; nothing is shared but the tracked data folder and artifacts/). Each worker kills only its own processes, by pid (b11_common.py).
"""
import hashlib
import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

HOME = Path.home()
WORKERS = [(HOME / "ic2-work-b11", ":577"), (HOME / "ic2-work-b11-w2", ":578"), (HOME / "ic2-work-b11-w3", ":579"), (HOME / "ic2-work-b11-w4", ":580"),
           (HOME / "ic2-work-b11-w5", ":581"), (HOME / "ic2-work-b11-w6", ":576")]
ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "runs" / "experiments" / "data" / "run-exp-battle-hook"
ART = ROOT / "artifacts" / "run-exp-battle-hook"
RUN = ROOT / "runs" / "experiments" / "battles" / "b11_run.py"


def opt(a, name, default):
    return int(a[a.index(name) + 1]) if name in a else default


def plan(base=None):
    fs = sorted(DATA.glob("b5-baseline-*.json"))
    base = Path(base) if base else fs[-1]
    cells = json.loads(base.read_text())["baseline"]
    pairs = sorted((v["cell"], v["seed"]) for v in cells.values())
    stamp = time.strftime("%Y%m%d-%H%M%S")
    p = DATA / ("pairs-%s.txt" % stamp)
    p.write_text("".join("%s %d\n" % x for x in pairs))
    print(p.name, len(pairs), "pairs from", base.name)


def pairs_file():
    return sorted(DATA.glob("pairs-*.txt"))[-1]


def round_pairs(n, size):
    lines = [x.split() for x in pairs_file().read_text().splitlines() if x.strip()]
    return [(c, int(s)) for c, s in lines][(n - 1) * size:n * size]


def run_round(n, size, workers):
    prs = round_pairs(n, size)
    ws = WORKERS[:workers]
    procs = []
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for k, (work, disp) in enumerate(ws):
        mine = prs[k::len(ws)]
        if not mine:
            continue
        f = DATA / ("pairs-round%02d-w%d-%s.txt" % (n, k + 1, stamp))
        f.write_text("".join("%s %d\n" % x for x in mine))
        env = dict(os.environ, IC2_WORK=str(work), DISPLAY_IC2=disp, B11_WORKER="-w%d" % (k + 1))
        log = open(DATA / ("round%02d-w%d-%s.out" % (n, k + 1, stamp)), "w")
        procs.append(subprocess.Popen([sys.executable, str(RUN), "run", "hook", "--pairs-file", str(f)], env=env, stdout=log, stderr=subprocess.STDOUT))
        time.sleep(2)
    rc = [p.wait() for p in procs]
    print("round", n, "pairs", len(prs), "workers", len(procs), "exit codes", rc)
    return rc


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pack(n, size):
    prs = round_pairs(n, size)
    return pack_tags("%02d" % n, ["%s_s%d_r1_hook" % (c, s) for c, s in prs])


def pack_tags(label, tags):
    """tar.gz of every artifact whose name starts with one of the trial tags (series, post save, shots, raw buffer) + a tracked manifest."""
    members = []
    for t in tags:
        members += sorted(ART.glob(t + "_*"))
        members += sorted((ART / "shots").glob(t + "_*")) if (ART / "shots").exists() else []
        if (ART / "hookbuf" / (t + ".bin")).exists():
            members.append(ART / "hookbuf" / (t + ".bin"))
    out = ART / "archives"
    out.mkdir(parents=True, exist_ok=True)
    name = "b11-hook-batch-%s.tar.gz" % label
    tgz = out / name
    if tgz.exists():
        name = "b11-hook-batch-%s-%s.tar.gz" % (label, time.strftime("%Y%m%d-%H%M%S"))
        tgz = out / name
    man = []
    with tarfile.open(tgz, "w:gz") as tf:
        for m in members:
            rel = m.relative_to(ART).as_posix()
            tf.add(m, arcname=rel)
            man.append({"name": rel, "bytes": m.stat().st_size, "sha256": sha(m)})
    rec = {"archive": name, "archive_bytes": tgz.stat().st_size, "archive_sha256": sha(tgz), "batch": label, "trials": tags, "members": len(man), "files": man,
           "release": "run-exp-battle-hook"}
    mp = DATA / ("release-manifest-batch%s-%s.json" % (label, time.strftime("%Y%m%d-%H%M%S")))
    mp.write_text(json.dumps(rec, indent=1))
    print(name, rec["archive_bytes"], "bytes", len(man), "members; manifest", mp.name)
    print("gh release %s run-exp-battle-hook %s" % ("upload" if subprocess.run(["gh", "release", "view", "run-exp-battle-hook", "--repo", "diegoami/ic2-conquest"],
                                                                                capture_output=True).returncode == 0 else "create", tgz))
    return tgz, mp


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "plan":
        plan(*a[1:2])
    elif a[0] == "round":
        run_round(int(a[1]), opt(a, "--size", 45), opt(a, "--workers", 5))
    elif a[0] == "pack":
        pack(int(a[1]), opt(a, "--size", 45))
    elif a[0] == "packtags":                                   # packtags LABEL TAG...   (e.g. the inertness batch)
        pack_tags(a[1], a[2:])
