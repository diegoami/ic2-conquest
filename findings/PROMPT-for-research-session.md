Three rule findings from the ic2-conquest bot are ready to promote into imperial-conquest-2-research/docs/reports/, please review and promote them.

They are drafts in `diegoami/ic2-conquest`, branch `claude/focused-knuth-ci59fz`, folder `findings/`, already in the research repo's report format with saves and code addresses cited. Evidence: headless Wine runs of `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`, built by ic2-conquest's `patches/seed_patch.py` on top of the fixtures' `patch_exe.py`), plus capstone disassembly of the original exe (`9d753d5d…ba31`).

1. `findings/2026-09-29-recruiting-cities-need-fortification-75.md` answers imperial_conquest_2#515.
   - The Army recruits dialog lists an own city when its fortification is at least 75, or when it is the nation's capital (nation +0x444), or when it already holds one of the nation's recruitment slots.
   - For a city with a fortification order in progress (a stored value above 100), the built part `fort mod 100` must be at least 75.
   - Code: the city-list fill at 0x454540–0x4545F3 (city table 0x479590, stride 34, fort at +0x1A). The helper 0x44B8D0 only tests "is any nation's capital", to upper-case the name.
   - On the new-game save (Rome, 270 BC Spring week 1) the dialog lists exactly Luceria (fort 77) and ROME (78, the capital). Arretium (72) is absent.

2. `findings/2026-09-29-loading-a-save-does-not-reseed.md` corrects 2026-09-28-battle-minigame-headless-feasibility.md.
   - Randomize (0x402744) is called at 0x448AB0, which is inside FUN_00448AA4, New Game's leader and turn-order draw. That function is called from TPremierForm_InitialiseForm (0x45A93A, program start) and TPremierForm_NewGame (0x45AA32). It is not the load routine.
   - The load routine FUN_004487C4 never calls Randomize. So RandSeed is seeded at program start and at New Game, and File → Open does not reseed.
   - Observed: a SEED.LOG line per Randomize firing (1 at start, 2 for a new game, 0 on load).
   - With RandSeed fixed at program start, one save plus the same orders gives a byte-identical next autosave (seed 12345 twice: 48857fdd…; seed 999: 592 bytes differ; clock: differs). A scripted move + recruit + End turn repeats byte for byte, and so does a New Game.

3. `findings/2026-09-29-nation-view-origin-and-unit-map-clicks.md` names two nation-record fields.
   - Nation +0x488 / +0x486 are the unit map's view origin (top-left tile x / y), per nation. ptolemaic-player-and-week9.md lists them as unknown.
   - The unit map's click handler (0x446420) computes x = X div 32 + [+0x488] and y = (Y − 30) div 32 + [+0x486]. It then reads the column-major map at 0x45E870 (280 bytes per column) and dispatches on the marker code.
   - A click on the Area map puts the clicked tile at column 6, row 7 of the unit map. This was checked live by reading /proc/<pid>/mem under Wine.

Smaller UI facts, from ic2-conquest's coverage.md:
- Game → End turn runs at once. There is no confirmation box, except an "End turn ?" box when an army needs supplies ("An army of yours needs supplies. If you have not finished your turn click MAKE MORE MOVES. If you are finished moving click END TURN."; findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md); the executable's only End-turn warnings are "An army of yours cannot afford to pay its mercenary units." and "One of your fleets is not docked at its own city."
- A siege on an enemy you are already at war with shows no "Are you sure…" box.
- All 72 message and refusal strings of the executable are catalogued there.
