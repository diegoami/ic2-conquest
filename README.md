# IC2 Conquest: a bot that dominates Imperial Conquest 2

Seed for a new repository, proposed name `diegoami/ic2-conquest`, private.

**Primary goal:** find strategies that dominate the map in the original 1996 game, and **prove it** with a strip of per-turn saves, logs and plans.

**Secondary goal:** exercise every mechanic the game has, and record what each one does.

The bot plays **the original game**, headless under Wine. It does not play the reimplementation. The original is ground truth, and with a fixed random seed it is also its own simulator, as explained below. The reimplementation (`imperial_conquest_2`) and the research repo are inputs, not dependencies.

## Rules this repository keeps

1. **No game file enters git**: no EXE, DAT, SAV, screenshot or recording. The repository holds code, plans, logs and metrics as text. Saves and screenshots of a run go in a GitHub release of this repository, `run-<id>`, and plans cite them by bare filename, as the research repo does.
2. The game files come from `diegoami/imp_conquest_fixtures`:
   - `patch_exe.py`, which builds `Imperial Conquest 2 fast rollingsave.exe`;
   - the DAT, help files and `WAVS`.

   A setup script fetches them and never commits them.
3. Every claim of progress points to a save: "Rome holds 60 cities in 262 BC, `AUTO0912.SAV`, run `r03`".

## Where the bot runs: the original as its own simulator

- **Build:** `fast rollingsave`. Battles are instant, and every human turn autosaves `AUTOnnnn.SAV` with a line in `AUTOSAVE.LOG`. See research report `2026-09-28-autosave-hook-feasibility.md`.
- **Determinism:** the game reseeds `RandSeed` (`0x45E030`) from the clock in its load routine (`0x448AB0` calls `Randomize` at `0x402744`). A small patch that seeds from a value we choose makes a turn **exactly repeatable**. The battle-lab probe proved this for battles (report `2026-09-28-battle-minigame-headless-feasibility.md`); the same trick covers the whole turn.
- **Lookahead is branching:** from one save, try plan A and plan B in parallel Wine instances, end the turn(s), and compare the resulting saves. A turn costs roughly 30–60 s through the UI today, so branch width is limited but exact: 4–8 Xvfb displays in parallel give a few hundred branch-turns an hour.
- **State:** parse the SAV. The layout is fully decoded in the research repo's `decompiled-sav-file-layout.md`; `state/queues.py` is a start.
- **Actions:** an **order driver**, xdotool click maps per dialog, checked by diffing the save after the order. The seed scripts in `harness/` already drive:
  - new game, open save and end turn;
  - the battle screen with *Computer general*;
  - the offer and result dialogs.

  Still to build: move, attack, recruit, mobilise, supply, tax, fleets, embark and disembark, diplomacy.

## Does the bot find strategies by itself, or does player input help?

**Both, but player input is worth a lot early.**

- **Blind search finds tactics, not strategies.** One turn has a huge order space: every army × every target × recruits × tax × diplomacy. Search over it finds good *one-to-three-turn* moves: which city to attack, how much to recruit, where supply runs short.
- **Your Ptolemy example is a strategy.** Build fleets, ship medium armies to distant, lightly held Seleucid cities, avoid the main army. That is a 5–15-turn plan whose payoff comes long after its cost. Blind search almost never stumbles on those.
- **So the bot works from hypotheses.** Strategies live in `strategies/*.md`: written by you, taken from the research, or proposed by the bot from what it observed. The bot's job is to **test them, measure them, refine them, and combine them**. Each strategy gets a trial:
  - the same start save and seed, strategy vs baseline;
  - N turns;
  - metrics compared.
- **The planner is a Claude agent, one decision per turn.** It reads the parsed state, the rules digest and the active strategy, writes a plan, issues orders through the driver, and after the turn writes expected vs actual. It can fork: "try both landings, keep the better".

Coverage (the secondary goal) is a checklist, `coverage.md`, of every order type, dialog, event and mechanic: fleets, sieges, peace terms, rebellions, mercenaries, storms, defection and so on. Each entry records the save where it was first exercised and what happened. The bot schedules experiments for what is still unticked. Anything it learns about the rules goes back to the research repo as a report.

## Proof: what a run leaves behind

A run is `runs/<id>/` in git, plus release `run-<id>`:

| Where | What |
|---|---|
| release | `AUTOnnnn.SAV` every turn, `AUTOSAVE.LOG`, a screenshot per turn |
| `runs/<id>/turns/nnnn.md` | plan (intent, strategy step), orders issued, expected vs actual, surprises |
| `runs/<id>/metrics.csv` | per turn: each nation's cities, troops, fleets, treasury, unity |
| `runs/<id>/summary.md` | the domination curve, key decisions, which strategy won, the final save |

"Dominate" is measured from the save: the share of the 334 cities owned, and the share of all troops. It is plotted per turn from `metrics.csv`.

## Relationship to the other repositories

The dependency runs **one way**. `ic2-conquest` never writes into another repository by itself.

- **Reads:**
  - the research repo, as its rules knowledge, pinned to a commit in `setup/pins.txt`;
  - `imp_conquest_fixtures`, for the game files and `patch_exe.py`, fetched at setup and never committed.
- **Gives back through a gate.** Anything the bot learns about the rules is written as a draft in `findings/` in this repo, in the research repo's report format, with the saves cited. The player (or a research session) promotes a finding into `imperial-conquest-2-research/docs/reports/`. That keeps the research repo's standard of evidence, and the bot cannot pollute it.
- **The build repository is not involved.** Later it can take the bot's plans as test scenarios.

## Exchanging strategies with the player

**A strategy is one markdown file in `strategies/`**; see `strategies/rome-v1.md`. It has:

1. **Front matter:** id, nation, author, status (`proposed → accepted → in-trial → validated | refuted | revised`), start and parent.
2. **The player's intent, verbatim.** The bot never edits it.
3. **Principles:** rules the bot must follow, each with *how it is checked from the save*.
4. **Phases with milestones:** each milestone checked in the save, each with a deadline.
5. **Open questions** for the player.
6. **Bot validation, written by the bot:**
   - how it understood the strategy;
   - what the researched rules support, and the gaps;
   - the test plan.
7. **Trials:** one row per run, linking the debrief.

**Feedback happens at three points. The conversation lives in one GitHub issue per run, and the files hold the decisions.**

| When | The bot posts | The player answers |
|---|---|---|
| **Before** | the strategy's validation section, the first turns' concrete orders, the checkpoint schedule | approve, or edit the strategy and answer the open questions. The run starts only on approval |
| **During** | at each checkpoint (default: every season): metrics, milestone status, principle violations, the next season's plan | nothing (the run continues), or steer: "combine the two Gallic armies", "stop and wait". The bot pauses at a checkpoint only if the strategy says `pause: true` |
| **After** | `debrief.md`: the domination curve, milestones met or missed, what went wrong (each point with the turn and save), proposed changes | agrees or corrects. The next strategy version (`rome-v2`) records its parent and which feedback it applies |

## Runs: pilot first, discussion at the start of each run

- **Run 0 (pilot):** Rome, one game-year (24 turns), `rome-v1`, checkpoints every season. It proves the harness, the order driver, the logs and the feedback loop. **Winning is not its goal.**
- **Each later run starts with a discussion round** on the previous debrief: what happened, what went wrong, what to improve. The agreed changes go into the next strategy version before any turn is played.

## Watching a run

- **Turn strip:** each turn's autosave and a full-screen screenshot (map plus news) go in the release. `runs/<id>/viewer.md` lists the turns with plan, result and screenshot, so a run can be skimmed in minutes.
- **Video:** the Xvfb display is recorded with `ffmpeg -f x11grab` during the run. The mp4 goes in the release, cut per season; seasons flagged in the debrief are listed with timestamps. For watching battles, a replay run on the `watch rollingsave` build from the same save and seed shows the battle at the game's own pace.
- **Your own game:** any `AUTOnnnn.SAV` loads in the real game on your desktop, so you can open the turn where things went wrong and look around yourself.

## Suggested layout

```text
README.md  CLAUDE.md  coverage.md
setup/        fetch game files from imp_conquest_fixtures, build fast rollingsave + seed patch, install wine/xvfb
harness/      Wine/Xvfb session control, per-dialog click maps (the order driver)
state/        SAV parser -> JSON state; metrics extraction
patches/      seed-control patch (built on patch_exe.py)
planner/      the per-turn agent loop: state -> plan -> orders -> verify
strategies/   one file per strategy version (rome-v1.md, ...), in the format above
findings/     rule discoveries drafted in the research repo's report format, awaiting promotion
runs/<id>/    turns/nnnn.md, metrics.csv, checkpoints/, debrief.md, viewer.md (text only)
```

## Phases

0. **Harness.**
   - Setup script; seed patch; start a new game as nation X.
   - The order driver for **move/attack, recruit, end turn**, each verified by save diff.
   - Done when one scripted turn (a move plus a recruit) reproduces the same save twice.
1. **Order driver complete.** Every order type, each with a save-diff test, and `coverage.md` started.
2. **First full game.** One nation, agent-played with no strategy library, to set the baseline domination curve.
3. **Strategy trials.** Your strategies and the bot's, each run against the baseline from the same seed. Keep the winners and combine them.
4. **Domination run.** The best combined strategy played to domination. The strip of saves, logs and plans is the proof.

## What to carry over from the research session (in this seed)

- `harness/*.sh`: Xvfb and Wine environment, open save, end turn, new game (click the Nth nation), and auto-play a battle. **Coordinates are for a 1280×1024 Xvfb screen with the default window layout.** The save stores window positions per nation, so a loaded game keeps its layout.
- `state/queues.py`: SAV and DAT nation-table parsing: army, fleet and nation offsets, and the recruitment slots.
- `patches/battle_lab.py`: the seed-fixing and in-battle snapshot hooks, a pattern for the whole-turn seed patch.

**Container set-up that worked (Ubuntu 24.04):** `dpkg --add-architecture i386`, then `apt-get install --no-install-recommends wine64 wine32:i386 xvfb xdotool imagemagick`. A `libgd3` version clash may need `libgd3=<ubuntu version>` for both architectures. Start Xvfb with `setsid`, because background processes can be reaped between commands. Release assets of `imp_conquest_fixtures` download with plain `curl -L`.
