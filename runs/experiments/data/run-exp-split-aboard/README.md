# run-exp-split-aboard: data

Task `docs/tasks/split-aboard.md`; finding `findings/2026-10-05-split-army-aboard-a-fleet.md`; scripts `runs/experiments/split_aboard/`.

**Answer (2026-10-05):** Split army has no aboard refusal (Join armies does). With the fleet selected the split works: the new army is placed on the last free land tile (map code 2..11) of the 3x3 around the fleet, here (102,47); the rest stays aboard. Played: army 0 (10,700) aboard fleet 2 at (101,46) -> army 0 5,700 aboard, army 14 5,000 on land at (102,47). No free tile: no army and no message [derived].

Files: `code_extract_split_aboard.txt` (decompile, source line numbers), `split.log`, `claims_audit_output*.txt` (newest = current), `MANIFEST-b1.txt`, `SAVES.sha256`. Binaries are in release `run-exp-split-aboard`.

## Review rework (PR #48)

The first run (`split_aboard.py` with raw screen-coordinate menu clicks) is kept; the play was re-run with the OCR-calibrated, verified menu steps (`lib.split_army_via_menu`) and reproduced the result (`save_pairs.tsv` lists both runs' saves; the re-run's saves carry `.v2`/`.v3`). The audit (`claims_audit.py`) reads the tracked code extract, not the Ghidra dump; `check_dump_vs_extract.py` is the optional comparison. Paths derive from the script location (`paths.py`). The Rules in the finding are tagged `[derived]`; only the observed fleet-selected case is `[confirmed]`.

## Last review round (PR #48, owner-approved fix 2026-10-05)

Round 3 asked for the embark, the unit selection and the Transfer click to be verified each, with at most two retries. `lib.embark_verified` checks the fleet's carried-army field in memory; `lib.transfer_first_unit` checks the selection by a change of the left list's pixels and the transfer by a change of both lists plus OCR text in the right list. The fourth run (`save_pairs.tsv` row `verified-steps`, batch `rerun3`, `MANIFEST-rerun3.txt`) passed every step at the first attempt (`split.log`, 18:09-18:10) and reproduced the result.
