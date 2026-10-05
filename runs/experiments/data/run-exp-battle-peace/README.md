# run-exp-battle-peace (B16, the Offer of peace): data folder

Task: `docs/tasks/battles-b16-peace.md`. **Work stopped early on 2026-10-04 (coordinator's wind-down); the PR is NOT open.**

## Status (2026-10-05): finished; PR "battles: B16 the Offer of peace"
All runs done, committed, pushed; binaries (611) in release `run-exp-battle-peace` (archives `b16-batch1/2/3`, manifests tracked, `SAVES.v3.sha256` one-form hashes; the old `SAVES.sha256` mixes two name forms and is not edited). Claims audit `b16-claims-audit-*.md`: 30 claims, 0 mismatches (the last file written is the one cited; earlier audit files are kept). Finding: `findings/2026-10-05-battle-peace-offer.md`. Nothing is half-finished; no process of mine runs. Not done / not established: see the finding's last section.

## Rework after the PR #45 review (offline, no Wine)
- R1: `b16_numbers.py` (inventory of every numeric token of the finding), `b16_number_map.json` (each prose line: the claims that check it or exempt tokens with reasons), `b16_audit.py` (74 claims, 0 mismatches: tables recomputed cell by cell, cited files and cells, button rectangles, all gate cells on all seeds, extended D-WIN, per-turn treasury/unity). Output files are new each run (`b16-claims-audit-*.md`, `b16-number-map-*.md`); the earlier audit files are kept.
- R2: `b16_fulldiff.py` (`b16-fulldiff-*.json`, `b16-fulldiff-summary-*.md`): before (memory snapshot with the box up) v after (Save As) over the whole decoded save, per branch: Yes changes the two relation words and the news ring (one line in, one out) and nothing else; No changes nothing. The save's tail (calendar, turn order, current seat, pending offer, battle flag) is not in the snapshot.
- R3: `b16_common.PeaceGame` launches with Popen, remembers the pid tree (PPid walk of /proc), refuses to start if the display or prefix is occupied, kills only that tree; no pattern kill anywhere in `b16_*`. (The base `harness/driver.py` `Game.start/kill` still use `pgrep`/`wineserver -k`; the B16 runner does not call them.)
- Corrections found on the way: the re-owned army 12 is Illyria's (nation 9), not Dacia's (the finding, first PR body and README said Dacia); the normal-build click counts are 32 No and 12 Yes with 2 clicks (35 had included hooked runs); the extra bytes between runs of different roles are up to 10 (not 11).
