# SAV export #37, Q1 addendum: the 31 INERT nation bytes stay untouched through battle, siege, elimination and treaties

**Tag:** [confirmed in emulation]. It adds states to the INERT result of research's 2026-10-21 atlas; it does not change
it.
**Task:** research [#37](https://github.com/diegoami/imperial-conquest-2-research/issues/37) Q1, option (b), asked
2026-10-31.
- The atlas found no reader of nation +0x450..+0x46A, +0x46D and +0x491..+0x493: statically, and in one Wine round.
- It named the untraversed states as its gap. These are now executed.

## Method

`runs/experiments/savexport37/q1canary.py`:
- Unicorn on the pinned EXE with the #187 RAM snapshot (`runs/experiments/navigation187/core.py`).
- **All 16 nation records** get a canary in the 31 bytes (496 bytes in all), and every seat is set AI.
- A memory hook over the whole nation table reports every read or write overlapping those bytes, with the instruction
  address.
- **Positive control:** the same hook counts accesses to the live unity word +0x440 and the human flag +0x490.
- The routines and their RNG run unmodified. Stubbed (presentation only):
  - sound, map redraw;
  - the news line and its string helpers;
  - the turn title, the nation-menu disable, and `TPremierForm_RefreshForms`.

## Result (`q1canary-v1.json`)

| Path | Entry | What ran | Accesses to the 31 bytes | Control accesses | Canary bytes after |
|---|---|---|---|---|---|
| treaty, honourable | `FUN_00450c68(8, 1)` | war → −18, 1 news line | **0** | unity 2 | unchanged |
| treaty, sues | `FUN_00450c68(1, 8)` | war → −18; the loser's trades and alliances end (4 news lines) | **0** | unity 2 | unchanged |
| battle | `FUN_0044aee4(2, 10)` | instant AI–AI battle; the defender's army destroyed (owner −1) | **0** | unity 7, human 2 | unchanged |
| siege → elimination | `FUN_0044b27c(2, last city of Numidia)` | capture (city owner → 1), then elimination: the victim's unity → 0, disable-nation called | **0** | unity 7, human 1 | unchanged |
| a full AI round | `FUN_0044fa20` × 16 seats | diplomacy, economy, armies and fleets of every seat | **0** | unity 4,446, human 213 | unchanged |

**So, within this scope, INERT also holds for battle, siege, capture, elimination, both treaty branches and a whole AI
round.** The exporter policy (PRESERVE_OR_ZERO; byte identity with an original lineage carries the source bytes) is
unchanged. With this, Q1 closes as research proposed.

## What this does not establish

- **Other paths:** rebellion and revival (`FUN_0044c360`), the human's dialogs, a tactical battle, and the round tick and
  weekly or quarterly ticks outside the AI seat turn.
- **The full RAM:** the hook covers the nation table only. A reader that copies the record elsewhere first would show
  as a read of the copy, which would itself be visible here only if it touched the 31 bytes.
- **Native Windows.** The snapshot is one state, and the battle and treaty outcomes are those of the snapshot's RNG.
- Development runs `q1canary-dev1..dev4.json` are kept: dev1 crashed in the AI round, dev2 and dev3 in the siege path,
  each on a presentation call that was then stubbed.

## Evidence

- Code: `runs/experiments/savexport37/q1canary.py`.
- Data: `runs/experiments/data/run-exp-savexport37/q1canary-v1.json`, with `dev1..dev4` kept.
- Private, not published: the EXE and the #187 RAM snapshot.
