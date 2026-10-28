"""#230 batch 2: controls for the war-declaration difference found in batch 1 (rel-war-carthage), written
2026-10-29 BEFORE these cases ran.

Hypothesis (from research decompiled-war-cascade-and-peace-paths.md: TPolitics_OK commits every changed cell of
the human's row through the relation setter, in nation order; the setter drags the target's allies into war):
declaring war from the International Relations dialog makes the target's ally go to war (cascade), but when the
ally's index is HIGHER than the target's, the loop reaches the ally's cell afterwards, finds the dialog's copy at
peace (0) and the committed value at war, and commits 0: the ally ends at -18 (the war cooldown). When the ally's
index is LOWER, its cell was already passed and it stays at war (3).

Predictions for the original (the remake, which declares through its command, should give 3 in every case):
- rel-war-numidia (5; ally Carthage 1, lower): Carthage-Rome 3.
- rel-war-dacia (10; ally Thracia 15, higher): Thracia-Rome -18.
- rel-war-thracia (15; ally Dacia 10, lower): Dacia-Rome 3.
- rel-war-bithynia (11; ally Galatia 12, higher): Galatia-Rome -18.
"""
from difftest.cases.orders230_b1 import BASE, case

CASES = [
    case("rel-war-numidia", "declare war on Numidia (ally Carthage, lower index)", {"op": "relation", "nation": 5, "kind": "war"}),
    case("rel-war-dacia", "declare war on Dacia (ally Thracia, higher index)", {"op": "relation", "nation": 10, "kind": "war"}),
    case("rel-war-thracia", "declare war on Thracia (ally Dacia, lower index)", {"op": "relation", "nation": 15, "kind": "war"}),
    case("rel-war-bithynia", "declare war on Bithynia (ally Galatia, higher index)", {"op": "relation", "nation": 11, "kind": "war"}),
]
