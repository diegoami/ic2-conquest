#!/usr/bin/env bash
# Run the remake's CLI (imperial_conquest_2 v0.5.0, commit 37f3062, read-only clone at /home/diego/projects/ic2-remake-v050) on a script.
#   remake_cli.sh <tag> <seat> <seed> <script> [scenario] [--load <save>]
# The transcript goes to runs/experiments/data/run-exp-gap-v050/cli/<tag>.txt (tracked; a new <tag>.vN.txt if it exists: never overwritten),
# with a header (commit, scenario, seat, seed, script text). In the script, write saves as  save ART/<name>.sav : ART is replaced by
# artifacts/run-exp-gap-v050 (git-ignored; the saves go to the release, their SHA-256 to SAVES.sha256 via hash_saves.sh).
set -euo pipefail
R=/home/diego/projects/ic2-conquest; D=$R/runs/experiments/data/run-exp-gap-v050; ART=$R/artifacts/run-exp-gap-v050
CLONE=/home/diego/projects/ic2-remake-v050
tag=$1; seat=$2; seed=$3; script=$4; scen=${5:-classical-mediterranean}; shift 4; [ $# -gt 0 ] && shift || true
mkdir -p "$D/cli" "$ART"
out="$D/cli/$tag.txt"; k=2; while [ -e "$out" ]; do out="$D/cli/$tag.v$k.txt"; k=$((k+1)); done
tmp=$(mktemp); sed "s#ART/#$ART/#g" "$script" > "$tmp"
export DOTNET_ROOT=$HOME/.dotnet PATH=$HOME/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1
{ echo "# remake v0.5.0 $(git -C $CLONE rev-parse --short HEAD) scenario=$scen seat=$seat seed=$seed extra=[$*] $(date -Is)"
  echo "# script:"; sed 's/^/#   /' "$script"; echo "# ---- transcript"
  cd $CLONE && timeout 900 dotnet src/IC2.Cli/bin/Release/net10.0/IC2.Cli.dll --scenario "$scen" --seat "$seat" --seed "$seed" --script "$tmp" "$@" 2>&1 || echo "# EXIT $?"; } > "$out"
rm -f "$tmp"; echo "$out"
