# A refused attack declares nothing: the original checks that the attack is legal first, then asks "Are you sure…?", then declares war, then attacks

**Status:** draft finding from `ic2-conquest`, awaiting promotion. Question 6 of `docs/tasks/v050-rule-reads.md` (clone task T135, `imperial_conquest_2` #705). **Wine-only.** Natural state, nothing edited; fixture copies only.

**Tags.** `[derived]` = read from the decompile (function, address, line of `all_app_functions.txt`; code in `runs/experiments/data/run-exp-v050-rules/code_extract_q6_attack_order.txt`). `[confirmed]` = seen in play with save pairs.

**Answer.**
- **The order is: legality, prompt, war declaration, attack** `[derived]`; the refused and the Yes branches of it were seen in play (below). In `TUnitMap_SelectUnit` @ 004466CC a click on a city (marker codes 20-99, :46532), army (200-247, :46555) or fleet (300-347, :46582) marker proceeds as follows.
  - **City and army targets.** `legal = (an army is selected, DAT_004A0328 ≥ 0) and (its moves ≥ 1) and (the army is at Chebyshev distance exactly 1 from the clicked tile, FUN_004492A0)` is computed first (:46514-46521). The code goes on **only when `legal` holds and the target's owner is another nation** (city :46539; army :46563-46564). Then (city :46540-46547, army :46565-46572): if the relation to the owner is already 3 (war) there is no box; otherwise the box "Are you sure you want to attack this city ?" / "…this army ?" (Yes / No / Cancel, :46541, :46566); on Yes (or war) the declaration `FUN_00449B40(me, owner, 3)` is called only if the relation is not 3 (:46544-46545, :46569-46570); then the attack itself: `FUN_0044B27C` (siege, :46547) or `FUN_0044AEE4` (field battle, :46572); the selection is then dropped (:46551, :46575).
  - **Fleet targets** (a foreign fleet; an own fleet is a selection or an embark, below). The legality here is the **selected fleet's**, not the army's: a fleet is selected (`DAT_004A032A ≥ 0`), its moves ≥ 1 and it is at distance 1 from the clicked tile (:46611-46617; otherwise silent, selections dropped). Then `FUN_004494E4(target fleet's owner, clicked tile)` (:46619): it scans the **whole 3 × 3 around the clicked fleet's tile** (`FUN_004494E4` @ 004494E4, :48086-48121) for a city of the **target's owner**; if one exists the click is refused with "You cannot attack a fleet docked at its own city !" (:46621, :46637-46639) **before any prompt**, so a fleet adjacent to its owner's port, not only one in it, is protected. Otherwise: no box when the relation is 3 (:46622), else the box "Are you sure you want to attack this fleet ?" (:46623); on Yes the declaration (:46626-46628), then `FUN_0044B5D0` (:46629), which resolves the battle at once and has no refusal of its own (:49885-49947).
  - **An own fleet clicked with an army selected and legal** is an embark, not an attack: if the fleet carries no army (`+0x49C282 == −1`) the army's troops `div 500` must not exceed the fleet's ships word, else "The army is too large for this fleet ?" (:46592-46599); otherwise `FUN_0044B79C` (:46601). Otherwise (the army not legal, or the fleet already carrying one) the fleet is only selected (:46591, :46608-46609).
- **So a refused attack has no prompt and no relation change** `[confirmed]` for the two cases played (the save pairs below): with the army 4 tiles away, or adjacent with 0 moves, a click on a peaceful nation's city left the relation at 0 (peace) both ways, the army's moves and troops, and the news log unchanged, and showed no box (screenshots). That the selection was dropped is a memory read (`SEL_ARMY`, `state_log.jsonl`) `[memory-only]`. **"Declare war before or after the legality check": after**: the declaration comes only after the legality, the owner test and the player's Yes, and no check follows it (`FUN_0044B27C`, `FUN_0044AEE4` and `FUN_0044B5D0` have no refusal branch; read for this finding) `[derived]`.
- **Legality in short:** for a city or an army target: an army selected, moves ≥ 1, distance exactly 1, the target owned by another nation; for a fleet target: a fleet selected with moves ≥ 1 at distance 1, and **no city of the target's owner anywhere in the 3 × 3 around the target fleet** (the refusal is before the prompt).
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

- **C and A are the refused attacks**: no relation change, no news, army unchanged (saves); no box (screenshots `Q6_C_far_after_click.png`, `Q6_A_zero_moves_after_click.png`); selection dropped (`selected -1` in `state_log.jsonl`: `[memory-only]`). **B (No)** shows (screenshot `Q6_B_no_after_click.png` and the save pair `Q6_02` → `Q6_03`) the box is the first thing the legal click does, and that No changes nothing. **E (Yes)** shows the declaration is immediate and precedes the siege in the news (the declaration line first, then the result); the siege succeeded (Genua's owner is Gaul in the save) and used the army's moves (5 → 0, `FUN_0044B27C` :49815) and some troops (−1,805).
- Both relation entries move together in E (3 / 3), as `FUN_00449B40` writes both (:48502-48504).

## What this does not establish

- **The ally cascade was not seen in play** (Greece had no ally at this start); it is `[derived]` from `FUN_00449B40`. The earlier fleet finding `2026-10-03-fleet-peace-prompt.md` saw the same cascade for a fleet attack (Carthage's ally Numidia).
- **Attacks on an ally (relation 2), a peace-with-cooldown nation (negative value), an army or a fleet** were not run on this order; the code uses the same `relation == 3` test and the same order for all three markers.
- **The fleet refusals** (selected fleet without moves, not adjacent, or a city of the target's owner in the 3 × 3) were not run; they are `[derived]`.
- **Whether the click needs a first activation click** in a fresh window is the driver's pitfall, not a rule; every step was verified from memory (selection id, moves, relation).
- **Wine-only**, one nation and one city.

## Reproduction

```text
gh release download run-exp-civ-sweep -p S06_Gaul_AUTO0720.SAV -D artifacts/run-exp-v050-rules/inputs
python3 runs/experiments/v050_rules/q6_refused_attack.py      # about 3 minutes (run it in the background: it passes the tool's 2-minute limit)
python3 runs/experiments/v050_rules/q6b_yes_branch.py
python3 runs/experiments/v050_rules/claims_audit.py
```
