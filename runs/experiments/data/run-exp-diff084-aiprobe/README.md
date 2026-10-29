# run-exp-diff084-aiprobe: how often a remake AI march stops short with moves left

Probe: `RemakeAdapter aiprobe <remake> <start.SAV> 10 <out.jsonl> seed=N` (`difftest/remake_adapter/AiProbe.cs`), remake
v0.8.4 (`d9cc71bc`), `classical-faithful`. Starts: the 16 New Game starts (S00–S09 from `artifacts/run-exp-civ-sweep`,
S10–S15 from `run-exp-diff084-campaign/starts`), seeds 1, 2, 3; 10 End turns each; the human seat gives no orders.
Remake only (no original game is played).

Per AI march (one jsonl line): nation, army, the AI log's kind and reason, the aimed point and distance before, the
march's `ArmyMoved` event (from, to, moves spent), the allowance recomputed with the remake's refill rule
(`SupplyMoraleRule.BaseMoves` and the supply penalty) from the army at the end of the round (an estimate where troops
or supplies changed), moves left (allowance − spent) and the distance after the walk. `summary-v1.txt` is the table
in `findings/2026-10-30-ai-march-continuation-missing-in-remake.md`.
