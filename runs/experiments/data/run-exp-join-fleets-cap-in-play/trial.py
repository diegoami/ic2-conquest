"""Three-trial reproduction of the Join-fleets 100-ship boundary (issue: L11).

For each (fleet 2 ships, fleet 5 ships) in [(50,49), (50,50), (50,51)]:

  1. Patch FLEET_SPLIT ('saves/fleet-split-antium-0734.SAV') so Rome's fleet 2
     and fleet 5 have the trial's ship counts. Writes the patched SAV
     as artifacts/run-exp-join-fleets-cap-in-play/trial-NNN-pre.SAV.
  2. Load the patched SAV via harness.driver.Game on a fresh Wine + Xvfb
     sub-process (each trial re-launches the exe to keep state clean).
  3. Call Game.join_fleets(2).  The harness docstring says the gate is
     "< 100 combined" but the decompile reads < 0x65 (= < 101).
     Per-trial pass/fail is decided by the post-state fleet count and
     survivor's ship count.
  4. Save the post-state SAV as artifacts/run-exp-join-fleets-cap-in-play/
     trial-NNN-post.SAV.
  5. Parse both with state.sav.parse; write a per-trial JSON summary
     to runs/experiments/data/run-exp-join-fleets-cap-in-play/results.json.

Each Game() process is short (~30s smoke-test timing). Run with:

    source harness/env.sh
    xvfb-run -a python3 runs/experiments/data/run-exp-join-fleets-cap-in-play/trial.py
"""
import json
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from state.sav import parse as parse_sav, ARMY_OFF, ARMY_LEN, FLEET_LEN

ART = REPO / 'artifacts' / 'run-exp-join-fleets-cap-in-play'
DATA = REPO / 'runs' / 'experiments' / 'data' / 'run-exp-join-fleets-cap-in-play'
ART.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

BASE_SAV = REPO / 'saves' / 'fleet-split-antium-0734.SAV'
TRIALS = [(50, 49), (50, 50), (50, 51)]


def patch_ships(base_bytes, f2_ships, f5_ships):
    """Patch fleet 2 (x=101, y=46, owner=0) and fleet 5 (x=101, y=47, owner=0)
    ships field in the SAV bytes.

    Layout-independent: scan for the 26-byte fleet record matching the
    (x, y, owner) signature, then patch +18 (the ships field within the record).
    The 13-field layout is fixed by the game's record schema:

      +0  x      +6  unk      +12 moves    +18 ships     +24 cell
      +2  y      +8  owner    +14 supplies +20 cond     (or build_city)
      +4  reset  +10 cd.     +16 money    +22 army

    The (x, y, owner) key matches FLEET_SPLIT's Rome fleets 2 and 5 uniquely.
    """
    data = bytearray(base_bytes)
    SHIPS_OFFSET = 18  # offset of `ships` within the 26-byte fleet record

    def find_fleet(x, y, owner):
        for off in range(0, len(data) - 26):
            fields = struct.unpack_from('<13h', data, off)
            if fields[0] == x and fields[1] == y and fields[4] == owner:
                # Also require not-carrying-army (fields[11] == -1) and not-building.
                if fields[11] == -1 and fields[5] < 0:
                    return off
        return None

    off2 = find_fleet(101, 46, 0)
    off5 = find_fleet(101, 47, 0)
    if off2 is None or off5 is None:
        raise RuntimeError(f'cannot find Rome fleets 2/5: off2={off2} off5={off5}')

    struct.pack_into('<h', data, off2 + SHIPS_OFFSET, f2_ships)
    struct.pack_into('<h', data, off5 + SHIPS_OFFSET, f5_ships)
    return bytes(data)


def summarize_fleets(s):
    """Return Rome's fleet id+ships pairs from a parsed SAV."""
    return sorted(
        [(f['id'], f['ships'], f['x'], f['y'], f['moves'])
         for f in s['fleets'] if f['owner'] == 0],
        key=lambda t: t[0],
    )


def run_trial(f2_ships, f5_ships):
    pre_path = ART / f"trial-{f2_ships + f5_ships:03d}-pre.SAV"
    post_path = ART / f"trial-{f2_ships + f5_ships:03d}-post.SAV"
    base = BASE_SAV.read_bytes()
    pre_bytes = patch_ships(base, f2_ships, f5_ships)
    pre_path.write_bytes(pre_bytes)

    # Drive the game in a subprocess so each trial starts clean.
    driver = REPO / 'runs' / 'experiments' / 'data' / 'run-exp-join-fleets-cap-in-play' / 'trial_driver.py'
    cmd = [
        sys.executable, str(driver),
        '--pre', str(pre_path), '--post', str(post_path),
    ]
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
    elapsed = time.time() - t0

    pre_parsed = parse_sav(pre_bytes)
    post_parsed = parse_sav(post_path.read_bytes()) if post_path.exists() else None

    pre_fleets = summarize_fleets(pre_parsed)
    post_fleets = summarize_fleets(post_parsed) if post_parsed else None

    accepted = post_fleets is not None and len(post_fleets) == 1
    if accepted:
        survivor_ships = post_fleets[0][1]
    else:
        survivor_ships = None

    return {
        'trial': f2_ships + f5_ships,
        'pre_fleet_2_ships': f2_ships,
        'pre_fleet_5_ships': f5_ships,
        'pre_path': str(pre_path.relative_to(REPO)),
        'post_path': str(post_path.relative_to(REPO)),
        'pre_rome_fleets': pre_fleets,
        'post_rome_fleets': post_fleets,
        'accepted': accepted,
        'survivor_ships': survivor_ships,
        'driver_rc': proc.returncode,
        'driver_stderr_tail': proc.stderr.splitlines()[-10:] if proc.stderr else [],
        'elapsed_s': round(elapsed, 1),
    }


if __name__ == '__main__':
    out = []
    for f2, f5 in TRIALS:
        r = run_trial(f2, f5)
        out.append(r)
        verdict = 'ACCEPTED' if r['accepted'] else 'REFUSED'
        ships = r['survivor_ships'] if r['survivor_ships'] is not None else 'n/a'
        print(f"trial {r['trial']:3d} = {f2}+{f5}:  pre={r['pre_rome_fleets']}  post={r['post_rome_fleets']}  -> {verdict} (survivor ships={ships})  [{r['elapsed_s']}s]")
    summary = REPO / 'runs' / 'experiments' / 'data' / 'run-exp-join-fleets-cap-in-play' / 'results.json'
    summary.write_text(json.dumps(out, indent=2, default=str))
    # also a SHA-256 file pointing at the SAVs for rule 6
    sha_lines = []
    for p in sorted(ART.glob('*.SAV')):
        h = subprocess.run(['sha256sum', str(p)], capture_output=True, text=True).stdout.split()[0]
        sha_lines.append(f"{h}  {p.name}")
    (REPO / 'runs' / 'experiments' / 'data' / 'run-exp-join-fleets-cap-in-play' / 'SAVES.sha256').write_text('\n'.join(sha_lines) + '\n')
    print(f"\nresults.json -> {summary}")
