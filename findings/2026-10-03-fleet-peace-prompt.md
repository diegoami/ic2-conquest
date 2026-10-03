# Attacking a fleet of a nation you are not at war with: a Yes/No/Cancel box, Yes declares war on it and on its ally, and the battle follows at once

**Status:** draft finding from `ic2-conquest`, awaiting promotion. **Wine-only: every result below is a candidate until the desktop original confirms it.** It closes the open item of `findings/2026-10-02-naval-battles.md` ("the peace prompt for a fleet: not tested, they were at war"). **Natural state, nothing edited.** Five trials (No, Cancel, Yes × 3 seeds) from one fixture.

**Answer.**
- **Clicking an adjacent fleet of a nation you are on trade terms with opens a box with Yes, No and Cancel**, read as "Are you sure you want to attack this fleet ?" (the driver's text read is garbled; the question is the one the research reports quote). The battle does not start until it is answered.
- **No and Cancel change nothing:** both fleets' ships, condition, moves and owners and both relation entries (trade, 1 and 1) were identical before and after.
- **Yes declares war and fights at once:** both relation entries went from 1 to **3 immediately**, the battle was instant (the attacker's fleet destroyed, the defender's reduced, as in `findings/2026-10-02-naval-battles.md`: Ptolemaic 70 × 63 against Carthage 90 × 74 lost in all three seeds), and the next autosave's news reads **"PTOLEMAIC DECLARES WAR ON CARTHAGE."**, **"PTOLEMAIC DECLARES WAR ON NUMIDIA."**, "Carthage sinks fleet of Ptolemaic." in that order.
- **The war reaches the target's ally:** Numidia was Carthage's ally (relation 2) and at peace with Ptolemaic (0); after the attack Ptolemaic's relation to Numidia was **3 (war)** as well, and Greece, on trade terms with both, was unchanged (1).

## Method

- **Fixture:** `python3 -m tests.make_fleet_battle_fixture --no-war` repeats the pair-1 staging (`findings/2026-10-02-fleets-sail-and-drift.md`) **without** Carthage's war order: the same sailing, the same positions at 0723 (Ptolemaic's seat): Ptolemaic fleet 1 at (111,73), 70 ships, condition 63; Carthage fleet 0 at (110,73), 90 ships, condition 74; both supplies 0; relation **1 (trade)** both ways (`T1P_FIXTURE_fleets_adjacent.SAV`, from `T1P_0723_s02_Ptolemaic.SAV`). Build and seed as in the other findings (`354d8265…532f`, Wine 9.0, Xvfb, one process per trial).
- **Trials** (`runs/experiments/fleet-battles/peace_prompt.py`): load the fixture with the seed; read both fleets and both relation entries (nation records, `+0x26 + 2·j`); `Game.attack_fleet(1, 0)`; the box is read and left open; **No** / **Cancel** pressed (the control by its text) and the state read again; or **Yes** answered, the state read, the autosave saved (seed 1), End turn and the next autosave's news read.

## Observations

Saves (`PP_yes_seed1.SAV`, `PP_yes_seed1_AUTO0723.SAV`), the box screenshots (`peace_prompt_box_seed1.png`, `peace_prompt_box_cancel_seed1.png`) and `peace_prompt.json` are in release `run-exp-peace-prompt`.

| branch | seed | the box | fleets after | relations after (Carthage→Ptolemaic / back) |
|---|---|---|---|---|
| No | 1 | Yes / No / Cancel | unchanged (70 × 63, 90 × 74) | 1 / 1 |
| Cancel | 1 | the same | unchanged | 1 / 1 |
| Yes | 1 | the same | attacker destroyed; Carthage 90 → 72 ships, condition 74 → 60 | **3 / 3** |
| Yes | 2 | the same | attacker destroyed; Carthage 78 ships, 64 | 3 / 3 |
| Yes | 3 | the same | attacker destroyed; Carthage 78 ships, 64 | 3 / 3 |

**The news** (next autosave, `PP_yes_seed1_AUTO0723.SAV`, the same three lines in seeds 2 and 3): "PTOLEMAIC DECLARES WAR ON CARTHAGE." / "PTOLEMAIC DECLARES WAR ON NUMIDIA." / "Carthage sinks fleet of Ptolemaic." The treaties: before, `Ptolemaic → {Carthage 1, Seleucid 3, Numidia 0, Greece 1, …}` and `Carthage → {Numidia 2, Seleucid 1, Greece 1, Celtiberia 3, …}`; after, `Ptolemaic → {Carthage 3, Seleucid 3, Numidia 3, Greece 1, …}`.

**The box is the same in each trial** (the click selects nothing else; after No or Cancel the selection was cleared and the fleets could still be ordered; not tested further). The End turn box after Yes listed the usual army and fleet warnings.

## Inferences

- A fleet attack at trade terms is a **war declaration with a confirmation**, like the army attack on a city (`findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md`): No and Cancel are free, Yes costs the war, including **the target's allies** (Numidia here), whose own wars and alliances are then in play. The relation drops straight to war without a step through peace or hostility.
- The prompt and its news explain the cascade: a bot that wants a naval battle with a nation on trade terms should expect the war on its allies as well.

## What this does not establish

- **Other relation values:** only trade (1) was tested. Peace (0), alliance (2) and the peace-with-cooldown values (−10, −18 of the start saves) were not; an attack on an **ally** may be refused outright. Whether the ally cascade is the rule for every ally, or depends on the alliance's strength or on the attacker's own relations, is one case.
- **The box's text** is read through a garbled text read; the title and the three buttons are what is certain.
- **The cascade's reach beyond one step** (Numidia's own allies) was not read; only Ptolemaic's row of the relations was.
- **One fixture, three seeds for Yes** (the three battles gave the same outcome by strength); the effect on the AI's behaviour in the following turns (revenge, alliances called) was not followed.
- **Wine-only.**

## Reproduction

```text
setup/setup.sh
python3 -m tests.make_fleet_battle_fixture --no-war          # about 20 minutes: the trade-terms fixture
python3 runs/experiments/fleet-battles/peace_prompt.py       # No, Cancel and Yes (seed 1)
python3 runs/experiments/fleet-battles/peace_prompt.py yes --seeds 3
```
