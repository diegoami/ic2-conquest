#!/usr/bin/env python3
"""Upload what the releases do not hold yet from artifacts/run-exp-battle-sweep/. Never clobbers, never deletes.

Release `run-exp-battle-sweep` hit GitHub's limit of 1000 assets per release (HTTP 422 "file_count limited to 1000 assets per release") during the B5 sweep,
after 479 loose saves of the sweep. From then on:
  * every NEW `.SAV` goes into one `<label>-saves.tar.gz` per call plus a tracked `MANIFEST-<label>.txt`, uploaded to release `run-exp-battle-sweep-2` (created by this script if missing);
    `release-manifest-<stamp>.json` (tracked) lists, per archive, its SHA-256, size and every member with its own SHA-256 (the member names are the bare file
    names the findings cite);
  * every NEW `.png` goes loose to `run-exp-battle-sweep-2` (there are far fewer than 1000).
A file already loose in either release, or a member of an archive in a tracked manifest, is skipped. If a release call is refused the exact command is printed,
the archive stays in artifacts/ and the script exits 3 (CLAUDE.md rule 1: report it, never retry another way).

    python3 runs/experiments/battles/release_sync.py [label] [--dry]
Writes `release-sync-<stamp>.json` (tracked): what was pending, uploaded, refused."""
import json
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

TAG, TAG1B, TAG2 = "run-exp-battle-sweep", "run-exp-battle-sweep-b5", "run-exp-battle-sweep-2"      # -b5 holds the B5 sweep archives (made before the coordinator named -2); new uploads go to -2
EXT = {".sav", ".png"}


def assets(tag):
    r = subprocess.run(["gh", "release", "view", tag, "--json", "assets", "--jq", ".assets[].name"], capture_output=True, text=True)
    return set(r.stdout.split()) if r.returncode == 0 else None


def manifest_members():
    out = set()
    for f in C.DATA.glob("release-manifest-*.json"):
        for a in json.loads(f.read_text()).get("archives", {}).values():
            out |= set(a["members"])
    return out


def pending():
    have = (assets(TAG) or set()) | (assets(TAG1B) or set()) | (assets(TAG2) or set()) | manifest_members()
    seen, files = set(), []
    for f in sorted(C.ART.rglob("*")):
        if f.is_file() and f.suffix.lower() in EXT and not f.name.startswith("_tmp") and f.name not in have and f.name not in seen:
            seen.add(f.name)
            files.append(f)
    return files


def main():
    label = next((a for a in sys.argv[1:] if not a.startswith("--")), "batch")
    files = pending()
    sav = [f for f in files if f.suffix.lower() == ".sav"]
    png = [f for f in files if f.suffix.lower() == ".png"]
    rec = {"tags": [TAG, TAG2], "pending_sav": len(sav), "pending_png": len(png), "uploaded": [], "archives": {}, "refused": None}
    if "--dry" in sys.argv or not files:
        C.write_new(C.DATA, "release-sync-%s.json" % C.STAMP, json.dumps(rec, indent=1))
        print(json.dumps(rec))
        return
    if assets(TAG2) is None:
        r = subprocess.run(["gh", "release", "create", TAG2, "--title", TAG2, "--notes",
                            "Saves (in .tar.gz archives, one per batch, members listed with SHA-256 in the tracked release-manifest-*.json) and screenshots of the battle sweep B5/B8 "
                            "(findings/2026-10-04-tactical-battle-sweep.md). Continues release run-exp-battle-sweep, which reached GitHub's 1000-asset limit."],
                           capture_output=True, text=True)
        if r.returncode:
            rec["refused"] = {"stderr": r.stderr[-300:], "command": "gh release create %s ..." % TAG2}
    if sav and not rec["refused"]:
        arch_dir = C.ART / "archives"
        arch_dir.mkdir(exist_ok=True)
        p = C.write_new(arch_dir, "%s-saves.tar.gz" % label, b"")      # exclusive create in a loop (-<stamp>, -<stamp>-2, ...): an earlier archive is never overwritten
        name = p.name
        with tarfile.open(p, "w:gz") as t:
            for f in sav:
                t.add(f, arcname=f.name)
        C.write_new(C.DATA, "MANIFEST-%s.txt" % label, "".join("%s  %s\n" % (C.sha(f), f.name) for f in sav))
        rec["archives"][name] = {"sha256": C.sha(p), "size": p.stat().st_size, "members": {f.name: C.sha(f) for f in sav}}
        r = subprocess.run(["gh", "release", "upload", TAG2, str(p)], capture_output=True, text=True)
        if r.returncode:
            rec["refused"] = {"stderr": r.stderr[-300:], "command": "gh release upload %s artifacts/%s/archives/%s" % (TAG2, C.NAME, name)}
            rec["archives"][name]["uploaded"] = False
        else:
            rec["archives"][name]["uploaded"] = True
    for i in range(0, len(png), 40):
        if rec["refused"]:
            break
        chunk = png[i:i + 40]
        r = subprocess.run(["gh", "release", "upload", TAG2] + [str(f) for f in chunk], capture_output=True, text=True)
        if r.returncode:
            rec["refused"] = {"stderr": r.stderr[-300:], "command": "gh release upload %s <%d png files from artifacts/%s/>" % (TAG2, len(png) - i, C.NAME)}
            break
        rec["uploaded"] += [f.name for f in chunk]
    if rec["refused"]:                  # an archive that was NOT uploaded must not count its members as held
        rec["archives"] = {k: v for k, v in rec["archives"].items() if v.get("uploaded")}
    C.write_new(C.DATA, "release-sync-%s.json" % C.STAMP, json.dumps(rec, indent=1))
    if rec["archives"]:
        C.write_new(C.DATA, "release-manifest-%s.json" % C.STAMP, json.dumps({"release": TAG2, "archives": rec["archives"]}, indent=1))
    print(json.dumps({k: (len(v) if k == "uploaded" else v) for k, v in rec.items() if k != "archives"}), {k: len(v["members"]) for k, v in rec["archives"].items()})
    sys.exit(3 if rec["refused"] else 0)


if __name__ == "__main__":
    main()
