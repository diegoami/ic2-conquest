#!/usr/bin/env bash
# Build the battle-lab exes "Imperial Conquest 2 lab s<seed>.exe" (battles plan §3.1) for the given seeds (default 1 2 3): fast + autosave + a
# RandSeed baked in at every battle start and resume + a BATTLEnn.SAV before every half-round (patches/battle_lab.py). Needs setup.sh to have
# run (IC2_WORK/build/patch_exe.py and the game folder). The exes are NOT in git: their SHA-256 are written to
#   runs/experiments/data/run-exp-battle-sweep/EXES-sha256[-<stamp>].txt   (an existing file is never overwritten; a new one is written beside it)
# Usage: setup/build_lab_exes.sh [seed ...]
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IC2_WORK="${IC2_WORK:-$HOME/ic2-work}"
B="$IC2_WORK/build"; G="$IC2_WORK/prefix/drive_c/IC2"
SEEDS=("$@"); [ ${#SEEDS[@]} -gt 0 ] || SEEDS=(1 2 3)
OUT="$HERE/runs/experiments/data/run-exp-battle-sweep"; mkdir -p "$OUT"
F="$OUT/EXES-sha256.txt"; [ ! -e "$F" ] || F="$OUT/EXES-sha256-$(date +%Y%m%d-%H%M%S).txt"
: > "$F"
(cd "$B" && sha256sum "Imperial Conquest 2 fast rollingsave seed.exe") >> "$F"
for s in "${SEEDS[@]}"; do
  (cd "$B" && PYTHONPATH="$B" python3 "$HERE/patches/battle_lab.py" "$s" >/dev/null \
    && mv "IC2 lab.exe" "Imperial Conquest 2 lab s$s.exe" && cp "Imperial Conquest 2 lab s$s.exe" "$G/")
  (cd "$B" && sha256sum "Imperial Conquest 2 lab s$s.exe") >> "$F"
done
echo "built with: PYTHONPATH=\$IC2_WORK/build python3 patches/battle_lab.py <seed>, 'IC2 lab.exe' renamed to 'Imperial Conquest 2 lab s<seed>.exe'; git $(git -C "$HERE" log -1 --format=%h -- patches/battle_lab.py) (last commit touching patches/battle_lab.py)" >> "$F"
cat "$F"
