# run-exp-battle-hook: data folder notes (battles plan B11, the exchange hook)

Task: `docs/tasks/battles-b11-hook.md`. Finding draft: `findings/2026-10-04-battle-exchange-hook.md`. Code: `patches/battle_hook.py` (build; `patches/battle_lab.py <seed> --hook`),
`state/hook_log.py` (reader), `runs/experiments/battles/b11_*.py` (runners and checks), `tests/test_battle_hook_*.py`, `tests/test_battle_exchange.py`.
Everything here is text, written with `common.write_new` (exclusive create; a re-run gets a new name) or append-only; nothing was overwritten. Saves, screenshots and the raw hook buffers are
in the release **`run-exp-battle-hook`** (see the end); their SHA-256 are in `SAVES.sha256` and in the `release-manifest-*.json` files.
The comparison files that the task names under `run-exp-battle-sweep/` are **here** instead (`inertness-*.json|csv`): that folder lives on PR #40's branch (not merged when this was
done) and this task does not write to it.

## File families

| file(s) | what |
|---|---|
| `EXES-sha256*.txt` | SHA-256 of the hooked lab exes. `EXES-sha256.txt` and `-195040` are the first two builds (no zero-initialised control block, then no reseed boundary caves); **`EXES-sha256-20261004-195346.txt` is the build every reported battle ran on** (seed 1 `d805d28f…`, seed 2 `d6fce697…`, seed 3 `feb14400…`). The `git <hash>` label at the end of each is the last commit touching `patches/battle_lab.py` when the build ran: the build used the working tree of this branch (the `--hook` option), not that commit. |
| `rebuild-check-unhooked-lab-exes.txt` | the unhooked lab exes rebuilt with the modified `battle_lab.py` are byte-identical to the ones the B5 sweep used (seeds 1-3): the refactor of the lab build changed nothing without `--hook`. |
| `b11-static-*.json` | the offline checks (`b11_addresses.py static`): the call-site table with the instruction context, the scan of `CODE` for every reference to `Random` (53: 14 inside the battle module and TBattleOver, 39 outside; all `E8`), the list equality, the displaced bytes and the branch-into-displaced check. `-200013` and `-200032` found no function start for the TBattlePols reseed (a scan bug: the loop started at an address not 4-aligned); **`-200058` is the final one**. |
| `b11-live-*.json` | the live address checks (`b11_addresses.py live`, hooked seed-1 exe, cell `ar-ar-one`): header words, flag timeline, RandSeed vs the buffer, Save As block vs memory. `-200201` is a first attempt that ended in an exception (the first use of `win_controls.exe` in that fresh game folder gave no controls for the Offer of peace box); kept. **`-200346` passes.** |
| `b11-semantics-*.json` | task Work 3, first check: slot word 9 and word 8 on the 315 B5 trials (`b11_semantics.py`). `-200513` counted the 60 cases in which an earlier melee of the half-round had removed the target as failures of check B (too strict); **`-200530` is the final** (those 60 are classified, 0 unexplained). |
| `b11-entries-*.json` | the markers fire where the snapshots say a shot / melee happened, on 315 hooked battles (`b11_addresses.py entries`). |
| `trials-b11.jsonl` | append-only, one line per trial attempt (hooked or plain; error lines included; `exe_sha256`, series and post-battle SHA-256, the hook check summary). |
| `hooklog-<trial>.csv` | every record of the hook buffer of that battle (`state/hook_log.py` layout), as read through `/proc/<pid>/mem` after the battle. |
| `hookcheck-<trial>.json` | the seed chain, boundary, formula and site checks of that log (`b11_run.analyze`, written by the runner right after the battle). |
| `chains-*.csv`, `chains-summary-*.json` | one row per hooked battle and the totals of those checks (`b11_chains.py`). |
| `exchanges-<trial>.jsonl`, `exchange-check-<trial>.json` | the rebuilt exchange log of the battle (every shot, melee, rout test, flank and placement draw: actor, target, `n`, draws, predicted loss, morale) and the check against the snapshots (`b11_exchange.py`). The 48 trials of round 1 and the seven inertness-batch trials have two versions: the second (newest by mtime) has the fields added after round 1 ran (`attribution`, `unconfirmed_exchanges`, `half_rounds_with_unaccounted_draws`); the older ones are kept. |
| `inertness-*.json`, `inertness-*.csv` | the byte comparison of hooked battles against unhooked ones (`b11_compare.py inertness`): the first (8 rows) is after the first batch; **the last is the full one: 322 hooked battles**. |
| `b5-baseline-*.json` | what was read from PR #40's branch (`origin/experiment/battle-sweep-b5`, commit `7dea580`): rep 1 of every ok trial: its BATTLEnn and post-battle SHA-256, `loss_rows`, `unambiguous_rows`. |
| `pairs-*.txt`, `round*-w*.out`, `b11-run-*.log|jsonl` | the (cell, seed) list (`pairs-20261004-200824.txt`, 315 lines), each round's split over the six workers, and each worker's log. |
| `sweep-table-b11-*.csv`, `sweep-table-b11-summary-*.json` | the sweep table with the exchange columns (task Work 4). |
| `callsites-*.csv|json` | the call-site table over the 315 battles (`b11_callsites.py`). |
| `b11-aggregates-*.json` | the totals quoted by the finding (`b11_aggregate.py`). |
| `release-manifest-*.json` | per release archive: name, size, SHA-256 of the archive and of every member. |

## Things to know

- **The first hooked trial `hi-hi-one_s1_r1_hook`** ran on the first hooked build (no reseed boundary caves) and with the first version of the end-of-battle check, so its `hookcheck` says `pass: false`
  (no end pin is possible on that build). It is **kept as written** and it is byte-identical to B5's `hi-hi-one_s1_r1`; the B5 re-run's representative for that cell and seed is `hi-hi-one_s1_r2_hook`
  (final build; `stands_in_for` in the sweep table). Its other 321 siblings pass.
- **A deleted launch log.** The first launch of round 1 (`b11_batch.py round 1`) failed at once on every worker (`ValueError: cell 'ar-hc-half-three' is not <type>-<type>-<half|one|three>`: the
  size-matrix cells exist only in PR #40's `trials.py`; `b11_run.py` now repeats that small parse). Its six `round01-w*.out` files held only that traceback; **I removed them by mistake
  (rule 6: a measured output must never be deleted)** before they were committed. No trial had started; the surviving `pairs-round01-w*-20261004-200825.txt` are that launch's split.
- The second launch picked the wrong pairs file (`pairs_file()` globbed `pairs-*.txt`, which also matches the per-worker lists) and ran 8 pairs; they are valid hooked trials (rep 1) and are
  counted in round 1. Fixed (`pairs-[0-9]*.txt`) before the real rounds.
- `b11-run-hook-20261004-195006…195555` are the development runs of the first hours (one failure: the control block was initialised with the 0xCC filler; the reader caught it and the build now zero-fills it).
- The development exchange files made before the final analysis are kept beside the final ones (newest by mtime = final).
- Game folders: six private copies of the prefix (`~/ic2-work-b11`, `-w2` … `-w6`) and six displays (:577, :578, :579, :580, :581, :576); a worker kills only the pids of its own display and prefix.

## Where the saves and the raw buffers are

Release **`run-exp-battle-hook`**, one `.tar.gz` per batch (GitHub's limit is 1000 assets per release): `b11-hook-batch-01 … 07.tar.gz` (48 battles each, the last 27), `b11-hook-batch-inertness.tar.gz`
(the hooked and unhooked battles of the inertness check and the live run's saves) and `b11-hook-batch-misc.tar.gz` (start saves, the FLD-RG fixture, stray saves). Each holds the `BATTLEnn` series, the
post-battle save, the screenshots and `hookbuf/<trial>.bin` (the raw buffer; its SHA-256 is in the trial's line in `trials-b11.jsonl`). The manifests list every member with its SHA-256.

## Build generations (rework after the review of PR #42)

- **First build (v1)** = every output made before the rework: `EXES-sha256-20261004-195346.txt` (exes `d805d28f…`, `d6fce697…`, `feb14400…`), the trials with `_r1_`, `_r2_`, `_r3_` in `trials-b11.jsonl` (the B5 re-run is the `_r1_` set), and the files derived from them: `inertness-20261004-200737.*`, `inertness-20261004-211341.*`, `chains-20261004-211415.*`, `sweep-table-b11-20261004-211342.*`, `callsites-20261004-211351.*`, `b11-aggregates-20261004-211529.json`, `b11-entries-20261004-211355.json`, `b11-mutation-*.json`, `tests-b11-20261004-211824.txt`, `b11-static-20261004-200058.json`, the release archives `b11-hook-batch-01..07`, `-inertness`, `-misc`. They are kept as measured and describe the first build: its scan compared the operand of `FF 15`/`FF 25` with Random's address (review R1) and its caves used one global saved-ESP and one private stack with no re-entry guard (review R2).
- **Second build (v2)** = `EXES-sha256-20261004-212732.txt` (seed 1 `58c683da…`, seed 2 `ca1cbf10…`, seed 3 `3ef20b4c…`): the scan resolves the pointer behind `FF 15`/`FF 25` and refuses an unresolved one inside the two modules; every cave tests a BUSY flag without touching a register or flag, and a cave entered while busy sets REENTERED, logs nothing and runs the original code. Its trials are the `_r5_` ones (`mix-rg` seeds 1-3 and the whole B5 re-run, rounds 1-7), and its outputs are the files stamped after 21:27 (`b11-static-20261004-212751.json`, the v2 `inertness-*`, `chains-*`, `sweep-table-b11-*`, `callsites-*`, `b11-aggregates-*`, `tests-b11-*`, `release-manifest-batchv2-*`, release archives `b11-hook-batch-v2-01..07`). The unhooked reference for the v2 inertness check is the unhooked lab runs of the first batch (`_plain` trials; the unhooked exes did not change).

## PR #42 review round 2
- `patches/battle_hook.py` `resolve_pointer`: a pointer outside every section, or one whose four bytes cross the end of the mapped (`vsize`) and file-backed (`raw size`) part of its section, is unresolved (it was ignored, or read across the boundary). The scan is the only thing that changed; the hooked exes are byte-identical, so the v2 battle outputs stand.
- New static scan `b11-static-20261004-223128.json` (`-212751` kept): inside the two modules still the 14 hooked `E8` sites only; outside them 27 unresolved (21 `FF15?`, 6 `FF25?`; 18 before).
- Made by the main session (Claude), with `IC2_WORK=~/ic2-work` (read-only use of the original exe) and capstone in a scratch venv.
