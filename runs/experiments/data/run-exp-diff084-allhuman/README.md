# run-exp-diff084-allhuman: an AI-free game, the rule bot on all 16 seats (#232)

Start `start-allhuman-AUTO0720.SAV`: New Game with all 16 nations human, seed 12345 (`python3 -m difftest.fixtures
all-human`). No AI acts in either game; the rule bot (rulebot-1) gives every seat its orders in the original's turn order
(Illyria, Numidia, Ptolemaic, Galatia, Seleucid, …), which the remake follows exactly. 32 seat-turns = two weeks.
Runner `python3 -m difftest.campaign`; remake v0.8.4 (`d9cc71bc`).

Seat-turns 1–4 are identical in the whole world (0 differences). Every later own-record difference has one of three causes:

| Cause | Seat-turns |
|---|---|
| the missing second walk (`findings/2026-10-29-walk-stops-at-own-city-on-line230.md`): a walk ends short with moves left in the remake only | 5 Seleucid, 12 Rome, 14 Carthage, 15 Gaul, 29 Bithynia, 32 Celtiberia |
| random draws: siege losses and fortification, a fleet's storm damage, the weekly rough-sea weather (the remake painted 520 cells at the first week's end, the original none) | 19 Ptolemaic, 21 Seleucid, 28 Rome, 30 Carthage |
| consequences of the above (orders differ because an army stands elsewhere) | 21, 30, 31 |

No other rule difference appeared. `allhuman-rulebot1-32/turns.jsonl` has every seat-turn: orders and replies on both sides,
and the differences.
