# run-exp-split-aboard: data

Task `docs/tasks/split-aboard.md`; finding `findings/2026-10-05-split-army-aboard-a-fleet.md`; scripts `runs/experiments/split_aboard/`.

**Answer (2026-10-05):** Split army has no aboard refusal (Join armies does). With the fleet selected the split works: the new army is placed on the last free land tile (map code 2..11) of the 3x3 around the fleet, here (102,47); the rest stays aboard. Played: army 0 (10,700) aboard fleet 2 at (101,46) -> army 0 5,700 aboard, army 14 5,000 on land at (102,47). No free tile: no army and no message [derived].

Files: `code_extract_split_aboard.txt` (decompile, source line numbers), `split.log`, `claims_audit_output*.txt` (newest = current), `MANIFEST-b1.txt`, `SAVES.sha256`. Binaries are in release `run-exp-split-aboard`.
