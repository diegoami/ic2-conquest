# ic2-conquest: the player's intent, the assessment, and the approaches

Written 2026-10-01, in the session that bootstrapped the harness under WSL2
(see `docs/wsl-setup.md`). This file records, in the player's own words, what
the project is being asked to become, my answer to each ask, and the concrete
approaches on the table. Nothing here is committed policy yet; it is the
material for the decisions.

## 1. The player's intent

### 1.1 The four questions, verbatim

> Open the IC2-conquest project and have a look at it:
> - can we run the discovery under windows
> - can we turn this into a project to run the original game headless
> - can we turn this into a discovery project that would discover the game and write the game specification
> - can we turn this into a trainer that at each turn gives me the game state and some utility command to perform strategy high level decision, like defeat an enemy, retreat for the winter, recruit an army and send it to raid on a fleet in a far away place
>
> just check, do not change. ask questions if necessary. may require other project, if you have not access I will retrieve them.

### 1.2 The decisions the player made

- **"under Windows"** → *"Run existing harness in WSL2"*: keep the Linux
  Wine/Xvfb driver and build the environment in WSL, rather than port the
  driver to native Win32.
- **Trainer target** → *"Both, behind one interface"*: the trainer may drive
  the original (through the order driver) **and** the reimplementation
  (`IC2.Engine`/`IC2.Cli`), behind one abstraction.
- **Trainer interaction** → *"Both, but the agent must be configurable, both
  URL and KEYs, would use a cheap opencode model"*: the player can type
  high-level commands, **and** an agent can plan each turn; the agent is an
  OpenAI-compatible endpoint with a configurable base URL and API key, defaulting
  to a cheap opencode model.
- **Repository shape** → *"Keep ic2-conquest, add modes"*: do not split into
  separate projects; add the runner / discovery / trainer as modes of this repo.
- **Toolbar drift fix** → *"Derive toolbar x at runtime"*: do not just move the
  hardcoded numbers; discover the button positions at run time.

## 2. What the project is today

`ic2-conquest` is a bot that plays the **original** 1996 game headless under
Wine/Xvfb, to find strategies that dominate the map and prove them with
per-turn saves, logs and plans; secondarily, to exercise every mechanic.

- **Determinism** comes from a seed patch (`patches/seed_patch.py`); the game
  seeds `RandSeed` from `SEED.TXT` beside the exe at program start.
- **State** is parsed from autosaves (`state/sav.py`), with per-turn metrics
  (`state/metrics.py`).
- **Orders** go through the game's own UI (`harness/driver.py`), each checked
  by a save diff (`tests/test_orders.py`).
- **Coverage** is the checklist `coverage.md`; discoveries are drafted in
  `findings/` in the research repo's report format.
- **Run 0** (Rome pilot, `rome-v1`, 24 turns) is proposed in
  `runs/0/proposal.md` and issue #1, not yet started.

Three other repositories are inputs: `imperial-conquest-2-research` (the ~70
reports), `imperial_conquest_2` (the reimplementation), and
`imp_conquest_fixtures` (the original files and `patch_exe.py`). All three were
reachable from this machine; nothing had to be retrieved.

## 3. My answer to each ask

### 3.1 Run the discovery under Windows

Split in two. **Static discovery** — Ghidra decompilation, save parsing,
report writing — already runs natively on Windows: Ghidra 12.1.3 + JDK 21 and
the IC2 project are under `%LOCALAPPDATA%\ReTools`, and `patch_exe.py` is
Python. **Dynamic discovery** — driving the running game — is the Linux
harness; the player chose WSL2, so it stays as it is and is now built (see
§3.5 and `docs/wsl-setup.md`).

### 3.2 A project to run the original headless

It already is one: `setup/setup.sh` + `harness/` + `patches/` run the original
headless and issue orders. It needed an environment, which now exists in WSL.

### 3.3 A discovery project that discovers the game and writes the spec

Mostly present: a save parser, a UI driver that can provoke mechanics,
`coverage.md` as the checklist, `findings/` in the report format, and a
one-way gate to the research repo. The specification already exists as the
research reports plus the build repo's `docs/game-design.md` and
`docs/design-audit.md`. What is missing for an *automatic* loop is the
scheduler that picks an untested mechanic, runs the experiment, diffs saves and
drafts a finding — today that is agent/human-driven. A caveat: many mechanics
(combat, AI) never reach a save, so discovery leans on memory reads, battle
snapshots, and the Ghidra static side too.

### 3.4 A trainer giving state + high-level commands each turn

This is the README's per-turn planner, half-built. Present: state
(`state/sav.py`), movement (`planner/path.py`), orders (`driver.py`). Missing:
the planner loop itself (`planner/` holds only `path.py`) and several order
types (`coverage.md`: fleets/embark/disembark, join/split/transfer, taxation,
disband are ⬜). The player's examples map to: *defeat an enemy* =
move+attack+play_battle (army attack still 🟡); *retreat for winter* = path +
winter supply (not built); *recruit an army* = recruit/mobilize (✅); *raid a
far fleet* = fleets/embark (⬜). With two backends and a configurable agent,
as the player decided, this is the largest of the three modes.

### 3.5 What was done in this session

The WSL environment was built and proven: the seeded build matches
`tests/results.md`, the game runs headless, loads saves, and 3 of 5 order tests
pass. Two blockers were found and fixed (a stale apt repo; a Wine prefix with
no user profile), and one remains (toolbar coordinate drift). All of it is in
`docs/wsl-setup.md`.

## 4. Possible approaches

### 4.1 Headless runner (mode)

Goal: one entry point that runs the original headless and exposes the `Game`
object, independent of the strategy/trainer code.

- **A. Keep `harness/driver.py` as the API.** Least work; the tests already
  use it. Risk: the runner, state, and trainer stay entangled.
- **B. A thin `runner/` package** that wraps setup, process control and the
  `Game` object behind a stable interface, leaving `driver.py` as its
  implementation. Recommended if the trainer is to have two backends.
- **C. A separate repository.** Rejected by the player ("keep ic2-conquest,
  add modes").

### 4.2 Discovery (mode)

Goal: discover the game and write the specification, increasingly automatically.

- **A. Human/agent-driven (today).** `coverage.md` is the queue; a session
  runs an experiment and drafts a `findings/` entry. No new code.
- **B. Experiment runner.** An `experiments/` schema (start save, seed, order
  list, observations) plus a runner that loads, issues the orders, ends the
  turn, and writes the save pair and a state diff. The finding is still drafted
  by an agent, but the evidence is produced mechanically. Good next step after
  the toolbar fix; it reuses the driver and the differ from `tests/`.
- **C. Generated specification.** Derive a machine-readable spec from the
  parsed state plus `docs/rules-digest.md` (e.g. a JSON of rules with
  provenance), so the trainer and the reimplementation can consume it. The
  research reports remain the human spec.
- **D. Static-assisted discovery.** Drive Ghidra decompilation for mechanics
  that never reach a save (combat, AI), and confirm each against a headless
  run. This is how the research repo already works; a discovery mode could
  schedule it.

Recommended: **A now, B next, C once the trainer needs it**; D stays in the
research repo.

### 4.3 Trainer (mode)

Goal: each turn, show the game state and accept high-level commands; an agent
can also plan, configurable by URL and key.

- **One interface, two backends.** Define a `GameBackend` protocol:
  `state() -> GameState`, `legal_actions()`, `apply(action)`, `end_turn()`.
  - `OriginalBackend`: wraps `harness/driver.py` + `state/sav.py`. Slow
    (30–60 s/turn), UI-fragile, but the real game.
  - `ReimplBackend`: wraps `IC2.Engine`/`IC2.Cli`. Fast, deterministic, but not
    the original.
  - Options for the second backend: in-process .NET interop (needs .NET from
    WSL), or a subprocess speaking JSON over stdin/stdout to `IC2.Cli`. The
    subprocess route keeps the two runtimes apart; recommended.
- **Command vocabulary.** High-level verbs over the low-level orders:
  `defeat(target)`, `retreat_for_winter(army)`, `recruit(city, type, troops)`,
  `raid(target)`, `reinforce(army)`, `fortify(city)`, `trade(nation)`. Each is
  a macro: plan a path (`planner/path.py`), issue the driver calls, verify on
  the save. Many need order types that are still ⬜ (fleets, embark, join).
- **Agent.** A planner loop that reads `GameState` + `docs/rules-digest.md` +
  the active strategy, and emits commands. Configurable through a git-ignored
  `planner/agent.local.json` (or env): `base_url`, `api_key`, `model`. Default
  to a cheap opencode model. The same interface serves the typed-command and
  agent modes; the player can override the agent's proposal.
- **Interaction.** Both, per the player: the trainer prints state + options,
  accepts typed commands, and can delegate a turn to the agent.

### 4.4 UI position calibration — **done** (PR #3)

Under this Wine the toolbar buttons and the dialog controls sit at different
positions than `coverage.md` records, so a `recruit` click landed on **Balance
sheet** and a dialog's `OK` was missed. Both are now derived at run time:

- **Toolbar:** `Game.calibrate_toolbar` reads each button's tooltip window (a
  named X window), caches the centres in `$IC2_WORK/toolbar.json`, and falls
  back to `TOOLBAR`.
- **Dialog controls:** `harness/win_controls.c` enumerates a window's child
  HWNDs (Wine draws them itself; they are not X windows) and `Game.controls`
  reads their class/text/screen-rect. `recruit` and `mobilize` click by
  caption/class. `setup.sh` builds the helper with mingw.

All five order tests pass (`move`, `recruit`, `end_turn`,
`scripted_turn_repeats`, `attack`). The other dialog methods (`supply`,
`fortify`, `hire_mercs`, `relation`) still use the recorded coordinates; the
same pattern converts them. Details in `docs/wsl-setup.md` §4.

Rejected alternatives, for the record: reading the VCL `TToolBar`/control rects
from process memory (exact, but needs the VCL layout reverse-engineered), and
using the menus instead of the toolbar (the driver prefers the toolbar because
menus drop clicks under Wine without a window manager).

### 4.5 Suggested order

1. ~~Toolbar + dialog-control calibration (§4.4)~~ — **done**, all five order tests green.
2. Finish the order driver (the ⬜ orders) and the run-0 experiment the
   `HANDOVER.md` lists.
3. `GameBackend` interface + `OriginalBackend`, and the command vocabulary
   (§4.3) → the trainer on the original.
4. `ReimplBackend` over `IC2.Cli` (subprocess/JSON).
5. Agent config (URL/key/model) and the planner loop.
6. Discovery experiment runner (§4.2 B), then the generated spec (§4.2 C).

## 5. Open questions

- Which cheap opencode model is the default, and where do its URL/key live
  (env vs a git-ignored file)?
- For the reimplementation backend: .NET from WSL (in-process) or a `IC2.Cli`
  subprocess over JSON?
- Does "write the game specification" mean the human-readable research reports,
  a machine-readable spec, or both?
- Should the discovery mode schedule experiments itself, or stay
  agent/human-driven for now?
- The run-0 pilot (issue #1) still needs an explicit "go"; how does it relate to
  the trainer work — first prove the harness with run 0, or build the trainer
  first?
