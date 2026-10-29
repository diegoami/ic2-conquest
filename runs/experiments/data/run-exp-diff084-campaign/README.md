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
