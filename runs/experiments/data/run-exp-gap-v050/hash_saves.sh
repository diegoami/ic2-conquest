#!/usr/bin/env bash
# Append the SHA-256 of every artifacts/run-exp-gap-v050 file not yet listed to SAVES.sha256 (append-only).
R=/home/diego/projects/ic2-conquest; D=$R/runs/experiments/data/run-exp-gap-v050; ART=$R/artifacts/run-exp-gap-v050
touch "$D/SAVES.sha256"; cd "$ART" || exit 0
for f in *; do [ -f "$f" ] || continue; grep -q "  $f\$" "$D/SAVES.sha256" || sha256sum "$f" >> "$D/SAVES.sha256"; done
