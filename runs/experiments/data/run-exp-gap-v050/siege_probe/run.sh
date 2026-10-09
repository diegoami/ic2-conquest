#!/usr/bin/env bash
# Build the probe outside the repository (scratch copy) and run it over one idle-Rome game: run.sh <save prefix> <out jsonl> [first turn (11)] [last turn (80)]
set -euo pipefail
P=$(cd "$(dirname "$0")" && pwd); B=${TMPDIR:-/tmp}/siege_probe_build; mkdir -p "$B"; cp "$P/SiegeProbe.csproj" "$P/Program.cs" "$B/"
export DOTNET_ROOT=$HOME/.dotnet PATH=$HOME/.dotnet:$PATH DOTNET_CLI_TELEMETRY_OPTOUT=1
dotnet build "$B" -c Release -o "$B/out" -v q -nologo > "$B/build.log" 2>&1 || { tail -30 "$B/build.log"; exit 1; }
dotnet "$B/out/SiegeProbe.dll" /home/diego/projects/ic2-remake-v050/data "$1" "${3:-11}" "${4:-80}" > "$2"
