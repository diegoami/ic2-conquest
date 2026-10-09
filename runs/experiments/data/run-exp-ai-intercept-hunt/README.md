# run-exp-ai-intercept-hunt

AI checks 3 (homeland intercept dispatch, research report `2026-10-07-strategic-ai-turn.md` §3.1) and 4 (fleet hunt vs port, §4), asked by the
player on 2026-10-09. Finding: `findings/2026-10-09-ai-intercept-and-fleet-hunt-in-play.md`.

## Method

- **The hook build** (`patches/ai_hook.py`; stubs tested under unicorn by `tests/test_ai_hook.py`). The seed exe with the AI's decision calls
  re-pointed to logging stubs:
  - `intercept_capital` 0x44F2E7 and `intercept_army` 0x44F2F9 (the two `FUN_0044dba8` calls of `FUN_0044efc8`);
  - `fleet_hunt` 0x44F69A and `fleet_port` 0x44F6BE (the two `FUN_0044e1fc` calls of `FUN_0044f608` after the hunt scorer);
  - `fleet_stored_dest` 0x44F667 (v4 only).

  Each stub appends a record to an in-memory buffer and jumps on to the original target. The record holds the site, the unit, the target xy, the nation, the caller's locals (scores, distances, chosen indices) and, from v2, the decision-time records of the unit and of the other unit. The runner reads the buffer through `/proc/<pid>/mem` after each End turn. Versions and SHA-256: `EXES-sha256.txt`. The first line of that file is v1; the second is the plain seed exe.
- **Natural runs** (`watch.py`): from `saves/run0-start-AUTO0720-seed12345.SAV` (Rome human, nothing edited), the human only ends turns.
  - `hook_s12345.jsonl`: v1 for 3, then 25 End turns; then v2 for 25.
  - `plain_s12345.jsonl`: the unhooked control, 25.
  - `hook_s2.jsonl`: v2 for 40, then v3 for 40.
  - `plain_s2.jsonl`: the control, 40.
  - `hook_s10.jsonl` (v2, 40) and `hook_s14.jsonl` (v2, 39: the game ended at End turn 40).
  - The `run_*.out` files are the console logs.
- **Inertness:** every hooked run's autosaves are byte-identical to the plain run's at the same seed: v1 25/25 and v2 25/25 at seed 12345, v2 40/40 and v3 40/40 at seed 2. v4 was used only for one staged run and adds one site.
- **Staged run** (`staged_hunt.py`, L1, labelled): `saves/fleets-adjacent-at-sea-0723.SAV` with Carthage's human flag (+0x490) set to 0.
  - Seeds 1-3 ran on v3, and seed 1 again on v4.
  - Log: `staged_hunt.jsonl`.
  - Start save: `staged_hunt_start_carthage_ai.SAV`.
- **Analysis:**
  - `analyze.py` → `analysis_hook_s<seed>*.json`. It checks each record against the decision-time state, versioned. Earlier versions are kept: `analysis_hook_s12345.json` is v1's run, before the decision-time checks; `analysis_hook_s2.v2.json` is empty, because it was written while the v3 run was the latest.
  - `hunt_bounds.py` → `hunt_bounds_hook_s<seed>*.json`. It recomputes each hunt score from the disassembled `FUN_0044f4f8` / `FUN_0044aa54` / `FUN_0044a930`. Its versions record the corrections: `hunt_bounds_hook_s2.json` used the report's formula; later versions add the distance back, then the decision-time records, the jitter rounding, the exact match and the morale. The last version, `.v7`, is the one cited.
  - `summarize.py` → `summary.json`.
- **Disassembly** (capstone, read-only): `FUN_0044efc8.asm`, `FUN_0044f4f8_f608.asm`, `FUN_0044aa54.asm`, `FUN_0044a930.asm`, `FUN_0044e9a8.asm`, `FUN_0044e5dc.asm`, `FUN_0044d9a8.asm` (cut at 0x44da22) and `FUN_0044d9a8.v2.asm` (whole, to its `ret`), `around_44db8b.asm`, `FUN_0044dba8_head.asm` (the aboard-army branch), `FUN_0044cd08.asm` (whole: the two stores through its pointer arguments at 0x44ceb4 / 0x44cebc).
- **Binaries:** release `run-exp-ai-intercept-hunt`, one `run-exp-ai-intercept-hunt-saves.tar.gz`.
  - Members: `MANIFEST-saves.txt`, whose last line is the tarball's SHA-256.
  - Every member's SHA-256: `SAVES.sha256`.
