# Opening prompt for the ic2-conquest session

---

You are working in `diegoami/ic2-conquest`: a project whose only purpose is to find strategies that **dominate the map** in the original 1996 game *Imperial Conquest 2*, and to prove it with a strip of per-turn saves, logs and plans. Its secondary purpose is to exercise every mechanic the game has.

**Read `README.md` first, then `strategies/rome-v1.md`.** They are the design and the first strategy, agreed with the player.

## Context you can rely on

- **Rules knowledge:** `diegoami/imperial-conquest-2-research`, read only. `docs/reports/` has around 70 reports. The ones you need first:
  - `decompiled-sav-file-layout.md` (the save format);
  - `2026-09-28-autosave-hook-feasibility.md` (the rollingsave build, and how the game was run headless);
  - `2026-09-28-battle-minigame-headless-feasibility.md` (seed control, battle snapshots);
  - `2026-09-29-new-game-recruitment-queues-come-from-the-dat.md`;
  - the supply, upkeep, morale and combat reports.

  Pin the commit you read in `setup/pins.txt`.
- **Game files:** `diegoami/imp_conquest_fixtures`. On `main`:
  - `patch_exe.py`, which builds `Imperial Conquest 2 fast rollingsave.exe` (battles instant; every human turn writes `AUTOnnnn.SAV` plus a line in `AUTOSAVE.LOG` beside the exe);
  - the DAT, the help files and `WAVS/`.

  Release assets download with plain `curl -L https://github.com/diegoami/imp_conquest_fixtures/releases/download/<tag>/<file>`. The research repo's `docs/evidence-index.md` maps save names to releases.
- **The seed in this repository:**
  - `harness/*.sh`: Xvfb and Wine environment, open save, end turn, new game (tick the Nth nation), and auto-play a battle with *Computer general*. Click coordinates assume a 1280×1024 Xvfb screen.
  - `state/queues.py`: SAV and DAT nation parsing.
  - `patches/battle_lab.py`: the pattern for seed-fixing hooks.

## Hard rules

1. **No game file in git:** no EXE, DAT, SAV, screenshot or video. Saves, screenshots and videos of a run go in a GitHub release of this repository (`run-<id>`), cited by bare filename. Everything in git is text: code, plans, logs, metrics. If you cannot create releases in your environment, keep the artifacts in a gitignored `artifacts/` folder, say so in the run's issue, and ask the player to upload them.
2. **Never write to another repository.** Rule discoveries go to `findings/` here, in the research repo's report format, with the saves cited. The player promotes them.
3. **The player's words in a strategy file are never edited.** The bot writes only in its own sections.
4. **No run starts before the player approves it** in the run's GitHub issue.
5. **Every claim of progress cites a save**, as run, file and turn.

## Environment set-up that worked before (Ubuntu 24.04 container)

- `dpkg --add-architecture i386`, then `apt-get install --no-install-recommends wine64 wine32:i386 xvfb xdotool imagemagick ffmpeg`. If a PPA's `libgd3` blocks the i386 package, pin both architectures to the Ubuntu version.
- The Wine binary is `/usr/lib/wine/wine`; use a 32-bit prefix (`WINEARCH=win32 wineboot -i`).
- Start Xvfb with `setsid`: plain background processes can be reaped between commands.
- The game loads, starts new games, plays turns and fights battles under Wine 9.0.
- Known headless facts:
  - loading a save reseeds the random generator from the clock (`0x448AB0` calls `Randomize` at `0x402744`, seed at `0x45E030`), so turns differ between runs unless seeded;
  - *Computer general* runs a whole battle inside one loop, so battle hooks must sit at `0x439D06`;
  - the autosave also fires at new-game start.

## Your first job: phases 0 and 1, then the pilot proposal (run 0)

1. **Bootstrap.** Write `setup/`, `CLAUDE.md` (these rules, condensed) and `coverage.md`. Setup fetches the game files, builds `fast rollingsave`, and installs Wine, Xvfb and ffmpeg.
2. **Seed patch.** Add an option to the build, following `patch_exe.py`'s style, that makes `RandSeed` come from a file beside the exe instead of the clock. Prove it: load one save twice with the same seed, end the turn, and get byte-identical autosaves.
3. **Order driver.** Build it for **move, attack, recruit, end turn** first. Each order gets a test that issues it headless and checks the save diff. Record every dialog's layout, and every refusal text, in `coverage.md`.
4. **State and metrics.** Parse each autosave to JSON. Write `runs/<id>/metrics.csv` per turn: for every nation, cities, troops by type, armies, fleets, treasury, unity, and army supply and morale.
5. **Pilot proposal.** Open a GitHub issue "Run 0: Rome pilot (rome-v1, 24 turns)" containing:
   - your validation section for `rome-v1` (how you understood it, what the researched rules support, the gaps; the fortification level needed to recruit is still unknown, imperial_conquest_2#515);
   - the concrete orders for the first two turns;
   - the checkpoint schedule: every season, and Autumn week 11 for the winter check.

   **Then stop and wait for the player's approval.**

When the player approves, play run 0 exactly as the README describes:
- a plan per turn in `runs/0/turns/nnnn.md`, with intent, orders, and expected vs actual;
- seasonal checkpoint comments in the issue;
- an ffmpeg recording of the display, cut per season;
- `runs/0/debrief.md` at the end: what happened, what went wrong (each point tied to a turn and a save), and proposed changes for `rome-v2`.
