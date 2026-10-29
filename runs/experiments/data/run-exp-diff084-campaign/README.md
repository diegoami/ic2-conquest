# run-exp-diff084-campaign: rule-bot games in both games (#232)

Runner: `python3 -m difftest.campaign` (docstring). Bot: `difftest/bot.py` (rulebot-1). Remake v0.8.4 (`d9cc71bc`),
continued from its native save each turn (checked equal to one continuous session); original one process, seed
12345.

## rome-rulebot1-5t: Rome, BASE.SAV, 5 turns

| Turn | Orders | Rome's own records after End turn |
|---|---|---|
| 1 | same: tax 20, recruit 1,200 HI at Rome, army 0 toward Felsina, army 1 toward (99,32) | differ: army 1 at (115,49) vs (118,52), the walk difference (`findings/2026-10-29-walk-stops-at-own-city-on-line230.md`) |
| 2 | same: recruit, army 0 besieges Felsina, army 1 marches | differ: army 1's position; army 0's losses in the siege (random draws, consistent per #233 `siege10`) |
| 3 | same | army 1's position and siege losses; Ariminum's fortification and supplies |
| 4 | **differ**: army 1 buys supplies in the original and marches in the remake (positions and supplies differ) | consequences |
| 5 | differ | consequences |

The first divergence is the walk (turn 1). Everything after it in Rome's records follows from it or from random
draws. AI nations differ from the first End turn, as in every run (#176/#177 families). Per turn:
`rome-rulebot1-5t/turns.jsonl` (orders and replies on both sides, differences); saves under `original/` and
`remake/t<k>/`.

## Nine more nations (2026-10-29): rulebot-1, 5 turns, from `artifacts/run-exp-civ-sweep/S0n_<Nation>_AUTO0720.SAV`

Summary: `campaigns-report-v1.txt` and `.json` (`python3 -m difftest.campaign_report`). Orders there are compared by
**identity**: each army or fleet index is replaced by (owner, x, y) in the state the bot read. Two games name the same
army by different record indexes (Ptolemaic, turn 2: army 7 vs 6, one army of 56,400 at (189,94)), and `turns.jsonl`'s
`orders_same` compares the raw indexes. Once an army stands elsewhere, its orders differ by identity too.

| Campaign | First own difference | Cause |
|---|---|---|
| Carthage | turn 1 | army 3's walk ends apart: the missing second walk (reproduced, `run-exp-diff084-orders-b5`) |
| Gaul | turn 1 | army 9's walk ends apart, the same cause (reproduced). Rome's AI then destroys the army in the original only |
| Celtiberia | turn 1 | a relation changed by AI diplomacy (#177 family) |
| Illyria | turn 1 | Rome ends its trade with Illyria in the remake only (relation −8): AI diplomacy |
| Greece | turn 2 | one city's supplies and the treasury: AI or economy, not from Greece's orders (none that turn) |
| Ptolemaic | turn 2 | a fleet's condition: the storm draw. Its army's walk toward (171,68) is blocked by sea in both games |
| Seleucid | turn 2 | siege losses (random draws, consistent per #233 `siege10`) |
| Macedonia | turn 3 | AI armies (an army changes hands) |
| Numidia | none | identical own records and orders for all 5 turns |

Failed attempts, kept: the first folders of Carthage, Seleucid, Ptolemaic, Macedonia and Numidia (an in-game save name
shared by all runs, refused by the driver), Gaul (the display died mid-run), and Greece, Celtiberia and Illyria
(the display was gone; `harness/driver.py` `ensure_xvfb` now checks our own display). `carthage-rulebot1-5t-r3` is
a partial duplicate started by a rerun-script bug and stopped. The completed runs are the folders with `summary.json`.

## The last six nations (2026-10-29): New Game starts made here (`starts/S<row>_<nation>_AUTO0720.SAV`, seed 12345)

Summary of all 16: `campaigns-report-v2.txt` and `.json`.

| Campaign | First own difference | Cause |
|---|---|---|
| Dacia | none | identical own records and orders for all 5 turns |
| Armenia | none | identical for all 5 turns |
| Bithynia | turn 1 | the compared army lists differ by armies of other owners (an army that belongs to another nation in one game). Bithynia's own move spent all 8 moves in both, so this is not the walk. AI armies; not analysed further |
| Galatia | turn 1 | the same pattern; its own move spent 8 of 8 in both. AI armies; not analysed further |
| Media | turn 2 | the same pattern, in a turn without own orders. AI armies |
| Thracia | turn 2 | the same pattern, in a turn without own orders. AI armies |

Over all 16 starts: 3 identical for 5 turns (Numidia, Dacia, Armenia); 3 first differ through the
missing second walk (Rome, Carthage, Gaul); the rest through the AI (diplomacy, armies, economy) or random draws.
