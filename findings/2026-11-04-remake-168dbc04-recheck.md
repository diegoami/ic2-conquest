# Recheck on remake main 168dbc04 (T277, the v0.9.4 candidate): the cross-region stale word is fixed in play; no regressions in 19 stored games

**Tag:** [confirmed: anchored remake replays against stored original games]. Wine only.
**Status:** draft for research.
**Task:** owner 2026-11-04: "0.9.4 has been build". T277's own validation says: "No new original experiment or
corrected-pin anchored replay is claimed". This report supplies that replay.

**The pin.** At the time of writing, the remake has no `v0.9.4` tag. The pin is main `168dbc04`:
- `a44c42fc` (v0.9.3), then `6b2e3ccc` (docs), then `168dbc04`;
- `168dbc04` is T277 (#1761), "faithful transport failure and pending capital defence", closing #1758, #1741 and #1760.

**T277 changes two things:**
- **Failed search:** DB38's failed-search signal is kept when no ferry qualifies, or when an adjacent ferry embarks the
  army. That is D9A8 cases (a) and (b), as research specified for #1758.
- **Pending battle:** capital defence goes on while a human tactical battle is pending (#1741).

If the tag lands on another commit, the replays here should be repeated on it.

**Research #195 context.** The comprehensive all-AI audit (research issue #195) uses the stored runs as evidence, not as
its scope. Every row below is end-to-end evidence: the remake against the original, both played from the same state, in
Wine.

## 1. Anchored replays of every stored game

**Runs.** 19 games, 898 turns, all with `--pin 168dbc04 --turn-seed 12345 --out anchored-168dbc04-ts`:
- the eight earlier 40-turn games: Rome, Carthage, Gaul and Seleucid (`run-exp-longrun-v090`); Ptolemaic and Macedonia
  (`-v091`); Numidia and Greece (`-v092`);
- the eight 40-turn games of v0.9.3 (`-v093`);
- the three long games reaching 264 BC (`run-exp-longgames`).

The runner is `runs/experiments/longrun-v090/recheck_pin.sh`.

**Comparison.** `runs/experiments/longrun-v090/pin_diff.py` compares the position rows: the (turn, nation,
armies/fleets) entries where the units stand on different tiles after End turn. It checks itself by reproducing v0.9.3's
Rome result against v0.9.2 (14 → 13, Seleucid fleet t36).

**Totals.** No remake errors. **14 position rows gone and none new** (`ts-168dbc04-vs-a44c42fc-v1.txt`):

| game | rows a44c42fc → 168dbc04 | gone | cause |
|---|---|---|---|
| Numidia (`-v092`) | 19 → 16 | Ptolemaic armies t37 | **#1758 fixed:** the cross-region stale-word case (D9A8 (a): fleet 1 is loaded and 61 tiles away) |
| | | Rome armies t24, t25 | open since v0.9.2 (the open list's "Numidia t24 and t32"; t32 remains): gone with T277, so probably the same class; not hook-confirmed |
| Celtiberia (`-v093`) | 26 → 24 | Macedonia armies t39, t40 | **#1758 fixed:** D9A8 (a), Macedonia has no fleet |
| Bithynia (`-v093`) | 33 → 28 | Bithynia armies t2, t3; Seleucid armies t3 | **our adapter, not the remake** (§2) |
| | | Greece armies t30, t31 | Greece's army stays at (112,70) in the original. v0.9.3 walked it to (111,70)/(111,68); T277 keeps it. No human orders on these turns. Consistent with the failed-ferry suppression; not hook-confirmed |
| Media (`-v093`) | 24 → 22 | Greece armies t31, t32 | the same army and tile as Bithynia t30–31 (112,70 → 111,70 on v0.9.3) |
| the other 14 games | unchanged | — | — |

**The three long games are unchanged:** Rome 28, Rome-h1 58 and Carthage 194 rows. Neither T277 change appears in those
266–264 BC turns.

**Stays** (`stays-168dbc04-ts-v1.txt`): 14 → 13 rows; the only one gone is Numidia t37. The 12 other rows are those of
v0.9.3, already reported:
- 10 are "own capital": armies next to their own capital that the original keeps and the remake moves (Antioch, Alexandria,
  Ecbatana, Carthago, Rome);
- the other three are two port fleets and one own-city army.

None of these turns has a pending human battle, so they are not #1741's case. They stay open for the #195 audit, under
capital defence and garrison.

## 2. The adapter fix (ours)

`difftest/remake_adapter/Program.cs` now shifts `{army:N}` and `{fleet:N}` down by the number of tombstone records before
N that the importer skipped. It was rebuilt for this pin only; the a44c42fc build that the running queue uses was not
touched. See `2026-11-04-late-replays-and-observer-mode.md` §3.

Bithynia's t02/t03 orders now reach the right army, and the remake error at t03 is gone. Those turns' rows are therefore
not a remake change.

## 3. Registry recheck

`python3 -m difftest.recheck 168dbc04` (`run-exp-recheck-168dbc04`): all 139 registered tests (orders, stats, campaigns) have the **same verdict as on a44c42fc** (`report-v1.md`; tally against v0.8.4 identical, 113 unchanged / 11 FIXED / 11 REGRESSED / 4 CHANGED). No registered test moves either way.

## Open

1. **Hook-confirm the Greece (112,70) stays** (Bithynia t30–31, Media t31–32) and Numidia t24–25 as the failed-search
   suppression: the walk hook on the original start, and the remake's `OriginalArmyIntermediateSearchFailed` event.
2. **The 10 own-capital stays**, for #195 (capital defence without a pending battle).
3. **Repeat on the `v0.9.4` tag** if it is not `168dbc04`.

## Evidence

- `runs/experiments/data/run-exp-longrun-v093/`: `ts-168dbc04-vs-a44c42fc-v1.txt`, `stays-168dbc04-ts-v1.txt`,
  `recheck-168dbc04-runner-v1.log`.
- `run-exp-longrun-v09{0,1,2,3}/*/anchored-168dbc04-ts` and `run-exp-longgames/*/anchored-168dbc04-ts`.
- `run-exp-recheck-168dbc04/` (saves: release `run-exp-recheck-168dbc04`).
- Saves: release `run-exp-longrun-v093`, `recheck-168dbc04-anchored-saves.tar.gz`.
- Tooling: `runs/experiments/longrun-v090/recheck_pin.sh`, `pin_diff.py`; `difftest/remake_adapter/Program.cs`.
