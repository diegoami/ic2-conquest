Research #138 (remake #1628): Carthage army 3, turn 1, from BASE.SAV (seed 12345), remake side.
Probe: difftest/remake_adapter/AiProbe.cs with decisions=<file> (the remake's own AiArmyTargetTree decision log).
- probe/decisions-1622407e-t1.jsonl : remake v0.8.5
- aiprobe-dab3a2ea-rome-t1.jsonl    : remake main at T246 only (scorer word storage)
- aiprobe-main-d8e7a646-rome-t1.jsonl, probe/decisions-d8e7a646-t1.jsonl : remake main (T247, 2026-10-30)
- probe/decisions-d8e7a646-ee60classify-t1.jsonl : main + ee60-classify.patch.txt (scratch copy, not pushed anywhere):
  the army scorer's region-halving test uses ClassicalArmyNavigation.Classify (the original FUN_0044eb9c/eb18) under
  faithful navigation, as the city scorer already does.
Each decisions file has every army decision of the round, one JSON line each (army-3 appears twice: Decide and the
post-march re-evaluation).
