# Running notes: g4-followups (issue #83)

Implementer: Claude Sonnet subagent (the owner's choice; reviewer openai/gpt-5.6-luna, chosen by the owner). Branch `experiment/g4-followups`, worktree `.claude/worktrees/g4`.
Data: `runs/experiments/data/run-exp-g4-followups/`; binaries in `artifacts/run-exp-g4-followups/` (git-ignored), release `run-exp-g4-followups`.

## Plan
Order F, C, B, A, D, G, H, I, K, J, L, E (issue #83 letters), each its own case of `g4_checks.py <case>` (library `g4_lib.py`, a copy of g3_lib), one fresh Wine process per case, fast rollingsave seed exe, seed 12345, Xvfb :99. Review fixes of g1 and g3 applied from the start: every autosave kept (`keep_auto`, `Game.supersede_autosaves()` before any New Game), a positive control in the SAME process for every "nothing happened", L1 staging with asserted length and exclusive creation, versioned outputs (`versioned.write_new`), claims cite a tracked output or a line of a tracked extract (`code_extract_g4.txt` from the pinned dump), frequencies with trial counts and independence stated, controls found from window controls.
- F (0x4a0334 save flag): static (the one clear is `mov byte [0x4a0334],0` at 0x448ac3, inside `func_0x00448aa4`, called by `TPremierForm_NewGame` and the form's create) plus a memory poller (20 ms) in one process around Open, Save as, File > New (No, then Yes) with the UI events time-stamped.
- C: the deposition disjuncts year 250, unity < 400, cities > 333 (human Rome, End turn; control in the same process).
- B: trade refusals for allied / at-war targets (relations dialog).
- A: a mercenary hired in play (army 1 beside Heraclea), Balance sheet before and after.
- D: mobilise with no free tile around the city (map words staged, L1) and the flag-0 branch if reachable faithfully.
- G, H: storm roll away from an own city (fleet moved by play); rebellion with two war armies within 9 tiles.
- I, K, J: AI quarter income (all 15 AI nations, predicted from the code vs observed); trade/alliance offer eligibility per roll (relations and partner counts of every nation at each roll); Greece's -8 relations.
- L: a rough-sea cell painted by the weather (replay of a deterministic seed to put a fleet where the weather will paint).
- E: a real X-button click: xfwm4 is installed (no root); run on a separate Xvfb display with the window manager.
- Rule 6: commit and push each batch; `scripts/archive_measurements.py run-exp-g4-followups --commit`; `release_sync.py` after every batch.

## Progress
- F batch 1: static (`static_flag_xrefs.txt`: the only clear is `mov byte [0x4a0334],0` at 0x448ac3 in the new-game initialiser 0x448aa4, called from 0x45a93a (form create) and 0x45aa32 (`TPremierForm_NewGame`)) and dynamic (`g4_checks-F-20261012-103825.jsonl`, 10 ms poller, 4,678 samples: 0 at start, 1 during File>Open, still 1 through File>New+No, 0 at 0.43 s after the Yes click, before the leaders form is up, 0 afterwards and at File>Save). Release `run-exp-g4-followups` created (8 assets).
- C batch 2: `g4_checks-C-20261012-104019.jsonl` (9 cases, one process): treasury -5200 (positive control) and unity 399 deposed, unity 400 not; year 250 deposed, year 251 not; natural roll 251 -> 250 deposed, 252 -> 251 not; cities word 334 deposed (staged word only), 333 not. `g4_checks-C_real-<stamp>.jsonl`: Rome given all 334 cities (give_cities) deposed with the conquest text, 333 (Numidia keeps its capital) not. Four distinct End of Game texts.
