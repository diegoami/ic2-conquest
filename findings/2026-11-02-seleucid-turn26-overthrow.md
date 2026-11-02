# Seleucid long run, turn 26: the human leader is overthrown in both games; the "freeze" was the end of the game

**Tag:** [confirmed: Wine + native Windows + remake replay] for the overthrow. The frozen battle window is Wine-only and
unexplained.
**Status:** promoted by research PR #176 (merge `4ca6e33`) as `docs/reports/2026-11-02-seleucid-turn26-overthrow.md`. Research
narrowed one claim: "not a harness bug" holds for the turn-26 stop. That the campaign's frozen battle window comes from the
same overthrow is inference. Research's two evidence gaps, answered:
1. **Exe:** sha256 `354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f` for both
   `C:\Users\diego\Documents\ic2-turn26-repro\Imperial Conquest 2 fast rollingsave seed.exe` (native run) and the Wine game
   folder's copy (`turn26-repro/exe-sha256.txt`). `repro_windows.py` now records `exe_sha256` in result.json.
2. **Message text**, read from both screenshots (Wine `wine-v1/after.png`, Windows `windows-v1/after-game-only.png`): "The game
   is over for Darius the leader of Seleucid. Your unpopularity has forced the army to overthrow you." Then "Your short time in
   power in Seleucid produced these changes.": 270 BC population 16,944,000, cities 62, treasury 2,700 talents; 269 BC
   13,767,000, 47, 6,308 (`turn26-repro/end-of-game-text.txt`).

The Windows screenshot first captured the whole desktop. It was replaced in the release by a crop to the game dialog
(`turn26-repro-saves-v2.tar.gz`), and the script now captures only the game's windows.
**Task:** owner 2026-11-02: why the Seleucid long run stops at turn 26, whether it's the original or the remake, and a native
Windows check.

## Result

At the start of turn 26 (Spring week 5, 269 BC) Seleucid, the bot's nation, has unity 402, 48 cities and wars with Ptolemaic,
Bithynia and Galatia (`seleucid-rulebot1-40t-r7/original/t26-a00.SAV`). After its End turn, **both games overthrow the human
leader**:

| Game | From `t26-a00.SAV` | Message |
|---|---|---|
| Original, Wine (`turn26-repro/wine-v1`) | End turn → `AUTO0746.SAV OK` → "End of Game" | "The game is over for Darius the leader of Seleucid. Your unpopularity has forced the army to overthrow you." Cities 62 (270 BC) → 47 (269 BC) |
| Original, **native Windows** (`turn26-repro/windows-v1`, same exe bytes) | End turn → `AUTO0746.SAV OK` → "End of Game" (modal, the other windows disabled), game responsive | the same |
| Remake `11f713e2` (`turn26-repro/remake-11f713e2-v1`) | `end` | "Your unpopularity has forced the army to overthrow you. Seleucid has been overthrown by the army and handed to the AI. Watch mode from here on." The same week and the same news (Sagalassus falls to Galatia) |

So the Seleucid game legitimately ends for the human at turn 26 in both games, and can't run to 40 turns. One presentation
difference: the original ends the game (End of Game), while the remake hands the nation to the AI and continues in watch mode.

## The frozen window in the long runs (Wine, harness)

In the campaign itself (r1–r7, fast and watch builds alike), the same End turn left an unpainted battle window "Ptolemaic v
Seleucid — Seleucid to move units" instead of End of Game:
- battle flag 0, seat 2, all threads idle in the message loop, no hidden window;
- `no_delay` is not the cause: the watch build stops the same way.

The single-turn replays (load `t26-a00`, write the `RandSeed` that the campaign logged before End turn, 3576117115) show no
battle. Two paint routines set `RandSeed` from map coordinates (`patches/seed_patch.py` notes), so a fresh load does not
reproduce the campaign's draws exactly. The likely sequence in the campaign: Ptolemaic attacks the human in the same turn as
the overthrow, and the overthrown human's defending battle is left open, with End of Game never shown. This was not
reproduced exactly; Wine against Windows on that exact sequence remains untested.

**Harness consequence:** a long-run game whose human is overthrown or conquered stops there. The driver's `end_turn` raises
`GameOver` only for an End of Game window that appears before the autosave line; both cases here show it after.

## Tools

- `runs/experiments/turn26/repro_wine.py`: load a save, write `RandSeed`, End turn; then windows, flag, seat, screenshot.
- `runs/experiments/turn26/repro_windows.py`: the same natively, with Windows Python and ctypes. Menus are driven by
  WM_COMMAND, memory through Read/WriteProcessMemory, screenshots with PowerShell. Folder
  `C:\Users\diego\Documents\ic2-turn26-repro`.
- `IC2_LOG_RANDSEED=1` (`difftest/original.py`): `RandSeed` before every action.
- `patches/watch_seed_build.py`: the seeded watch build.
