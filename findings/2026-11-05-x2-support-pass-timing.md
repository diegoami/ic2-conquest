# Faithful AI: the remake runs army support and hire once up front in Instant and headless play; the original runs it per army (audit #195, X2)

**Tag:** [confirmed: disassembly of the seed build; anchored remake replays of a stored original game, 3 seeds × 2 modes].
Wine only for the original side (the stored game).
**Status:** draft for research, written as a remake issue candidate.
**Task:** research #195 (comprehensive AI audit), cross-cutting difference X2 in
`findings/2026-11-04-ai-audit195-inventory.md` (rows A09, B22, C08); next step 1 of the 2026-11-04 night handover.

Remake pin: **v0.9.4** = `168dbc04` (T277). Ruleset `classical-faithful`.

## The rule in the original

`FUN_0044f31c` (the army phase) calls `FUN_0044e41c` (support and hire) as each army's first call, at `0x44F366`
(`call 0x44e41c`, seed build disassembly). Army k's resupply, transfers and mercenary hire therefore see the state left by
armies 0..k−1 this seat: their moves, battles, conquests and the money they spent.

## The remake

`src/IC2.Engine/Ai/AiTurn.cs` at `168dbc04`:
- line 142: `retainedPass = commands is IAiBattleInterruption { RetainPartialAiPass: true }`;
- line 186: when `retainedPass` is false, `AiMercenaryHirePass.Run` resupplies and hires for **every army up front**,
  before any army moves;
- line 251: when it is true, `PrepareArmy` runs `AiMercenaryHirePass.RunArmy` per army, inside
  `ProposeInOriginalArmyOrder`, which is the original's timing.

`RetainPartialAiPass` is true only when the AI seat runs under `GameSession`'s `AiPhaseBattleGate` built with a battle
identity (`Presentation/GameSession.cs:2315`). It does not need a pending battle, but the gate has three conditions
(research intake PR #206):
- `PlaySeatTurn` (line 2163) builds the gate only when `UsesAiPhaseBattleGate()` holds (line 2398): Tactical human
  battles, watch mode off, and a living human nation;
- it passes the battle identity only when `ClassicalArmyNavigation.Applies` (line 2165).

**Instant battles, the CLI, every headless run and every observer (watch) game, Tactical or not, take the up-front pass.** The flag's only other reader is `AiCapitalDefence.cs:82`
(`continuePending`), which acts only while a human battle is pending.

## Minimal trigger

- **Start:** stored game `greece-rulebot1-40t` (`run-exp-longrun-v092`), turn 21, start save `t20-a01.SAV` (release
  `run-exp-longrun-v092`, `greece-rulebot1-40t-saves.tar.gz`). The human's only order is a recruit; no battle is opened in
  either mode.
- **Seat:** Seleucid. Two armies near Antioch (221,60): 27,113 and 20,400 men.
- **Replay:** `python3 runs/experiments/audit195/x2_mode_probe.py artifacts/run-exp-longrun-v092/greece-rulebot1-40t 21
  <out> --seeds 12366,12345,99`, which replays the turn on the remake from the original's own start in both modes.

| | 27,113-man army | 20,400-man army |
|---|---|---|
| **Original** (stored game, `t21` end) | stays at Antioch (221,60) | (221,64) |
| **Remake, Tactical** (per-army pass), seeds 12366, 12345, 99 | (221,60) | (221,64) — matches |
| **Remake, Instant** (up-front pass), seeds 12366, 12345, 99 | **(221,64)** | **(222,64)** |

All other nations are equal in both modes. The result does not depend on the seed. In this turn the mode switch changes
nothing but where the support pass runs (the flag's two readers, above, and no pending battle), so the up-front pass is
the cause: it changes which city the army resupplies at, and so where it stands.

The mechanism inside the hire pass (which purse or troop count differs when army 1 is supplied before army 0 moves) was
not traced.

## Expected and actual

- **Expected (original):** each army's support and hire runs when that army's turn comes, after the earlier armies moved.
- **Actual (remake, Instant/headless):** all armies are supplied before any moves.
- **Candidate fix:** run the support pass per army (the existing `PrepareArmy` path) in every Faithful mode, not only when
  a tactical battle can interrupt the seat. The remake's Tactical path already has the original's timing; only its gate is
  narrower than the rule.

## Scope

- **Not the cause of the other stays rows.** The 11 other "stays" rows of the v0.9.3/v0.9.4 rechecks give the same result
  in both modes on every seed (`x2-stays-v1`), so they are not X2. They stay unattributed (inventory, pass 1).
- **Every anchored replay so far ran in Instant mode.** Some of the earlier AI-phase residuals may include X2 effects that
  were not separated.

## Evidence

- `runs/experiments/data/run-exp-audit195/x2-greece-t21-v1/result.json` (per seed and mode, the armies that differ) and
  `x2-stays-v1/`; hashes in `SAVES.sha256`.
- Saves: release `run-exp-audit195`, `audit195-x2-saves.tar.gz` (SHA-256 `c36870b7…f17`); the original game: release
  `run-exp-longrun-v092`, `greece-rulebot1-40t-saves.tar.gz`.
- Tooling: `runs/experiments/audit195/x2_mode_probe.py`, `x2_stays_batch.sh`.
- Research verification of the one-change argument: research PR #204.
