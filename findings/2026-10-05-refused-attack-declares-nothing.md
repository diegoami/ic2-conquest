# A refused attack declares nothing: the original checks that the attack is legal first, then asks "Are you sure…?", then declares war, then attacks

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Question 6 of `docs/tasks/v050-rule-reads.md` (clone task T135, `imperial_conquest_2` #705). **Wine-only.** Natural state, nothing edited; fixture copies only.

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; code in `runs/experiments/data/run-exp-v050-rules/code_extract_q6_attack_order.txt`). `[confirmed]` = seen in play with save pairs.

**Answer.**
- **The order is: legality, prompt, war declaration, attack** `[derived]` `[confirmed]`. In `TUnitMap_SelectUnit` @ 004466CC the click on a city, army or fleet marker first computes `legal = an army is selected and its moves ≥ 1 and the army is at Chebyshev distance exactly 1 from the clicked tile` (:46514-46521, `FUN_004492A0` = distance == 1). **Only when `legal` holds** does the code go on, for a city (:46539-46547):
  1. if the owner is not the attacker and the relation is **not already 3**: the box "Are you sure you want to attack this city ?" (Yes / No / Cancel, :46541); relation 3 skips the box;
  2. on Yes (or relation 3): `FUN_00449B40(me, owner, 3)` **declares the war** (:46544-46545);
  3. then the attack itself: `FUN_0044B27C` (siege, :46547). For an army target it is `FUN_0044AEE4` (:46564-46572), for a fleet `FUN_0044B5D0` (:46623-46629), with the same box and the same declaration first.
  4. Whatever the answer, the army selection is dropped (`DAT_004A0328 := −1`, :46551, :46575, :46614).
- **So a refused attack has no prompt and no relation change** `[confirmed]`: with the army 4 tiles away, or adjacent with 0 moves, a click on a peaceful nation's city did nothing visible, left the relation at 0 (peace) both ways, wrote no news, and dropped the selection. **"Declare war before or after the legality check": after.** The war is declared only after the click has passed the check and the player has answered Yes; no check follows the declaration (the siege and the field-battle functions do not refuse).
- **The legality is only three things for a city or an army**: an army selected, moves ≥ 1, adjacent. **For a fleet there are more refusals, all before the prompt**: the selected fleet must be one of the player's with moves ≥ 1 and adjacent (:46611-46617, silent), and "You cannot attack a fleet docked at its own city !" (:46637) when the target sits at an own city; and a fleet click from an army selected checks the fleet's capacity ("The army is too large for this fleet ?", :46593-46599) as an embark, not an attack.
- **The prompt is for any relation but war**: the test is `relation == 3` (:46540, :46565, :46622), so peace (0), peace with a cooldown (negative values), trade (1) and alliance (2) all get the box.
- **What Yes declares** (`FUN_00449B40` @ 00449B40, :48501-48544) `[derived]`: relation `[me][them] := 3` and `[them][me] := 3` (:48502-48504); the news "X declares war on Y." (`FUN_00449A44` @ 00449A44 :48455; upper-cased when either side is human, :48460-48465); then **every nation `k` allied to the target** (relation `[them][k] == 2`) and not yet at war with the attacker gets relation 3 with the attacker both ways and its own news line (:48526-48543). The cascade is one step: the allies' own allies are not looked at. The attacker's own allies are not dragged in by this function.
- **Where a human can declare war**: only the three sites above (one per marker type: :46545 city, :46570 army, :46627 fleet) and the International Relations dialog (`TPolitics_OK` @ 00453230, :55385); the other callers of `FUN_00449B40` are the AI, the quarterly thaw, peace and rebirth code `[derived]`.
- **A move never attacks.** A click on a terrain tile is a move (`TUnitMap_UnitMapClick` @ 00446420, :46384-46385: tile code under 20 or over 347 → `CheckForMove`); only a click on a marker goes to `SelectUnit` (:46427). The walk (`FUN_0044D734`) steps along a line to that terrain tile and stops at the first step it cannot afford; it does not declare war.

## Method

- **Code.** Read `TUnitMap_UnitMapClick`, `TUnitMap_CheckForMove`, `TUnitMap_MoveHumanArmy`, `TUnitMap_SelectUnit`, `FUN_00449B40`, `FUN_00449A44`, `FUN_0044B27C`, `FUN_0044AEE4`, `FUN_004492A0`, `FUN_00449018`.
- **Play.** Gaul human, from `S06_Gaul_AUTO0720.SAV` (release `run-exp-civ-sweep`, the New Game start as Gaul with `SEED.TXT` 12345; sha256 `1b004d3f…d23d`, in `SAVES.sha256`): army 9 (40,500 troops, 8 moves) at (93,28); **Genua (89,30) belongs to Greece, relation Gaul–Greece 0 (peace)**; Greece has no ally (relation 2) at that start, so no cascade is visible. `runs/experiments/v050_rules/q6_refused_attack.py` (normal build, own display): C) click Genua with the army 4 tiles away; move to (90,29) (cost 3, moves 8 → 5); B) adjacent with moves: click Genua, answer **No**; step between (90,30) and (90,29) until moves 0; A) adjacent with 0 moves: click Genua. The script was cut by the tool's time limit after step A. `runs/experiments/v050_rules/q6b_yes_branch.py` then reloaded `Q6_02_adjacent_moves5.SAV` and answered **Yes**. A save after each step; the box and the screens are in the release.

## Evidence

Army 9 and the relation, read from the saves with `state/sav.py` (`claims_audit.py` recomputes each line); news = the save's news log.

| Save | Step | Army 9: pos / moves / troops | Relation Gaul→Greece / Greece→Gaul | News lines |
|---|---|---|---|---|
| `Q6_00_start.SAV` | start | (93,28) / 8 / 40,500 | 0 / 0 | 32 |
| `Q6_01_after_far_click.SAV` | **C**: army selected, click Genua 4 tiles away | (93,28) / 8 / 40,500 | **0 / 0** | 32 |
| `Q6_02_adjacent_moves5.SAV` | moved to (90,29) | (90,29) / 5 / 40,500 | 0 / 0 | 32 |
| `Q6_03_after_prompt_no.SAV` | **B**: click Genua → box "Are you sure you want to attack this city ?" (`Q6_B_no_after_click.png`) → **No** | (90,29) / 5 / 40,500 | **0 / 0** | 32 |
| `Q6_04_adjacent_moves0.SAV` | stepped (90,30), (90,29), (90,30), (90,29), (90,30) | (90,30) / **0** / 40,500 | 0 / 0 | 32 |
| `Q6_05_after_zero_move_click.SAV` | **A**: army selected, 0 moves, adjacent, click Genua: **no box** (`Q6_A_zero_moves_after_click.png` shows none) | (90,30) / 0 / 40,500 | **0 / 0** | 32 |
| `Q6b_01_after_yes.SAV` (from `Q6_02`) | **E**: click Genua, box, **Yes** | (90,29) / **0** / 38,695 | **3 / 3** | 34: "GAUL DECLARES WAR ON GREECE.", "Genua   (Greece)  falls to Gaul." |

- **C and A are the refused attacks**: no box, no relation change, no news, selection dropped (`selected -1` in `state_log.jsonl` after each click). **B (No)** shows the box is the first thing the legal click does, and that No changes nothing. **E (Yes)** shows the declaration is immediate and precedes the siege in the news (the declaration line first, then the result); the siege succeeded (Genua's owner is Gaul in the save) and used the army's moves (5 → 0, `FUN_0044B27C` :49815) and some troops (−1,805).
- Both relation entries move together in E (3 / 3), as `FUN_00449B40` writes both (:48502-48504).

## What this does not establish

- **The ally cascade was not seen in play** (Greece had no ally at this start); it is `[derived]` from `FUN_00449B40`. The earlier fleet finding `2026-10-03-fleet-peace-prompt.md` saw the same cascade for a fleet attack (Carthage's ally Numidia).
- **Attacks on an ally (relation 2), a peace-with-cooldown nation (negative value), an army or a fleet** were not run on this order; the code uses the same `relation == 3` test and the same order for all three markers.
- **A refusal other than moves and adjacency** (a fleet's) was not run.
- **Whether the click needs a first activation click** in a fresh window is the driver's pitfall, not a rule; every step was verified from memory (selection id, moves, relation).
- **Wine-only**, one nation and one city.

## Reproduction

```text
gh release download run-exp-civ-sweep -p S06_Gaul_AUTO0720.SAV -D artifacts/run-exp-v050-rules/inputs
python3 runs/experiments/v050_rules/q6_refused_attack.py      # about 3 minutes (run it in the background: it passes the tool's 2-minute limit)
python3 runs/experiments/v050_rules/q6b_yes_branch.py
python3 runs/experiments/v050_rules/claims_audit.py
```
