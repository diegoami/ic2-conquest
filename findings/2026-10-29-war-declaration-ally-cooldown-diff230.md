# Declaring war from International Relations leaves a higher-index ally at peace (−18); the remake puts it at war

**Tag:** [confirmed, partial]: five original-vs-remake cases under Wine with the same start save and the same
order, and an explanation `[derived]` from the research's reading of `TPolitics_OK`. Not run on native Windows.
**Task:** [conquest #230](https://github.com/diegoami/ic2-conquest/issues/230) (tracker #228), remake **v0.8.4**
(`d9cc71bc82e22ad1d3d7c373c3d80d61ed0bcbeb`), `classical-faithful`.

## Answer

When the human declares war on a nation that has an ally, the two games end in different states:

- **Remake:** the ally goes to war with the human (relation 3 both ways), whatever its index.
- **Original, from the International Relations dialog:** the ally goes to war only if its nation index is **lower**
  than the target's. If the ally's index is **higher**, it ends at **−18 both ways**. That is peace with the
  cooldown a war leaves behind.

| Case (start: Rome, 270 BC, `BASE.SAV`) | Target (index) | Ally (index) | Original: Rome–ally | Remake: Rome–ally |
|---|---|---|---|---|
| `rel-war-carthage` | Carthage (1) | Numidia (5), higher | **−18** | 3 |
| `rel-war-dacia` | Dacia (10) | Thracia (15), higher | **−18** | 3 |
| `rel-war-bithynia` | Bithynia (11) | Galatia (12), higher | **−18** | 3 |
| `rel-war-numidia` | Numidia (5) | Carthage (1), lower | 3 | 3 |
| `rel-war-thracia` | Thracia (15) | Dacia (10), lower | 3 | 3 |

In every case the relation with the target itself is 3 in both games, and nothing else differs right after the
order. After the following End turn, the acting nation's own records differ only in that relation.

## Explanation `[derived]`

The research reads `TPolitics_OK` (`0x00453230`) as committing **every changed cell of the human's row** through
the relation setter, in nation order (`decompiled-war-cascade-and-peace-paths.md`, §"TPolitics_OK"). The setter
(`FUN_00449B40`) drags the target's allies into war, one step only
(`2026-10-05-refused-attack-declares-nothing.md`). Ending a war through the setter writes the −18 cooldown
(`decompiled-diplomacy-peace-terms-and-instant-battles.md`).

So: the loop reaches the target, declares war, and the setter makes the ally 3. If the ally's cell comes later in
the loop, the dialog's copy of that cell still says peace (0). The committed value (3) differs from it, so the loop
writes 0. Peace over war becomes −18. If the ally's cell came earlier, it was already passed and stays 3.

The five cases were run after the first one was explained, with the predictions written beforehand
(`difftest/cases/orders230_b2.py`, commit before the run). All four controls came out as predicted.

**Not tested:**
- Declaring war by attacking (the unit-map path, `TUnitMap_SelectUnit`), which calls the setter once and never
  walks the row. The research expects the ally to stay at war there.
- An ally of the human. An AI's own declarations.
- Two declarations in one dialog session.

## Remake side

The remake's `declare-war` (the command the CLI and the harness use) applies the cascade and stops. Its
International Relations dialog was not read for this finding. If that dialog submits the same command, a remake
player always gets the ally at war.

## Evidence

Measured with the differential harness (`difftest/`, `python3 -m difftest.sweep`). Data:
`runs/experiments/data/run-exp-diff084-orders/` (batch 1) and `runs/experiments/data/run-exp-diff084-orders-b2/`
(batch 2), each with `results.jsonl` (the run's verdicts), `results-rejudged-*.jsonl` (the final verdicts) and per
case `original/receipt.jsonl` and `remake/receipt.jsonl`. Saves are named per case: run `run-exp-diff084-orders`,
`rel-war-carthage/original/a001.SAV` (turn 0720, after the order), `a002.SAV` (turn 0721, after End turn); the
remake's `rel-war-carthage/remake/a001.SAV` (exported by the remake). The same names apply for the batch-2 cases in
`run-exp-diff084-orders-b2`. Hashes are in each folder's `SAVES.sha256`; binaries are in the releases of the same
names. Original: `Imperial Conquest 2 fast rollingsave seed.exe` (SHA-256 `354d8265…`), startup seed 12345, Wine 10.0.
