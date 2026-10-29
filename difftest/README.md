# difftest: the same moves in the original and the remake (#229)

Tracker: #228. The harness plays **one action script** in the original *Imperial Conquest 2* and in the remake
(pinned at **v0.8.4**, `d9cc71bc82e22ad1d3d7c373c3d80d61ed0bcbeb`) from **the same start save**, saves the state
after every action in both, and reports the **first checkpoint where the two differ**.

| File | Role |
|---|---|
| `actions.py` | The action format `diff-actions/1` (JSON lines, header first). Ops: `set_tax`, `move`, `recruit`, `end_turn`. A new op goes here first, then into both adapters. |
| `original.py` | Plays actions through `harness/driver.py` with a startup seed; `save_as` after every action (`<tag>-aNNN.SAV` in the game folder, copied to the run as `aNNN.SAV`). Existing autosaves are moved aside, never deleted. |
| `remake.py`, `remake_adapter/` | Translates actions to remake commands (`set-tax`, `move`, `recruit-standing`, `end`) and runs a C# adapter on the remake's public API: it imports the original start SAV, submits the commands, and after every action writes the native save (`aNNN.native`) and the state **exported to the original format** (`aNNN.SAV`). Placeholders `{army:N}`, `{fleet:N}`, `{city:N}` name records by their original-format index at that moment. |
| `compare.py` | Reads both sides' SAVs with the same parser (`state/sav.py`) and lists every differing field; `MAPPING` says which fields are compared and which are ignored, and why. |
| `report.py` | First-divergence report between two runs (JSON + Markdown), with a per-action "changed A / changed B" column: one side changing and the other not is a **refusal difference**. |
| `selfcheck.py` | Negative controls: single corrupted fields must be reported, an unchanged copy must not. |
| `scripts/` | Action scripts. |

## Setup

```bash
git clone --branch v0.8.4 https://github.com/diegoami/imperial_conquest_2.git ~/projects/ic2-remake-v084   # read-only; push URL DISABLED
export DOTNET_ROOT=~/.dotnet PATH=~/.dotnet:$PATH
B=artifacts/diff084-build
dotnet build ~/projects/ic2-remake-v084/src/IC2.Cli/IC2.Cli.csproj -c Release --artifacts-path $B/build
dotnet build difftest/remake_adapter -c Release -p:RemakeBuild=$PWD/$B/build/bin/IC2.Cli/release --artifacts-path $B/adapter
```

`IC2_REMAKE` and `IC2_DIFF_BUILD` override the two paths. The build is kept outside the measurement folder so its
JSON files are never archived as measurements. The original side needs `setup/setup.sh` and the seeded build.

## Use

```bash
A=artifacts/run-exp-<name>
PYTHONUNBUFFERED=1 python3 -m difftest.run original difftest/scripts/toy3-rome.jsonl ~/ic2-work/fixtures/BASE.SAV $A/toy3-original --seed 12345 --tag D84T1
python3 -m difftest.run remake   difftest/scripts/toy3-rome.jsonl ~/ic2-work/fixtures/BASE.SAV $A/toy3-remake
python3 -m difftest.report $A/toy3-original $A/toy3-remake $A/report-toy3
python3 scripts/archive_measurements.py run-exp-<name> --commit
```

A run folder must not exist yet; a re-run writes a new folder (rule 6). Original in-game save names must be unique per
run (`--tag`).

## What a difference means

- The remake's side is its state **exported** to the original format. A difference can come from the exporter, not the
  rules: the import → export round trip of the start save is checked first (checkpoint `a000` must match).
- The two games draw random numbers from different streams by design, and AI nations act during `end_turn` in both.
  A difference after `end_turn` may be an AI decision or a random draw, not a rule difference in our orders. Each
  report names the first differing checkpoint; whatever follows it is a consequence until shown otherwise.
- Known asymmetries: the original asks about pending offers and post-battle peace when a save opens or a turn ends;
  the driver dismisses information boxes and answers a Confirm **No**. A battle against the human during the AI turns is fought by the original's Computer
  general, and resolved instantly in the remake (`HumanBattles = Instant`).

## Test history

Every comparison is recorded in [`HISTORY.md`](HISTORY.md), generated from the append-only [`history.jsonl`](history.jsonl):

```bash
python3 -m difftest.history record <report.json> --data run-exp-<name> --issue <n> --verdict "<one line: what it shows>"
```

A wrong or superseded verdict is never edited: record a new entry with `--corrects <id>`.

## Test registry

[`REGISTRY.md`](REGISTRY.md) lists every test that has run, one row per test with its latest verdict and the
finding that reports its difference. It is generated from the tracked measurements:
`python3 -m difftest.registry`. **Check it before running a test** (owner, 2026-10-29). Re-run a test only to
check a fix or a new remake version, and say so in the history. Every difference found goes into `findings/`; add
the test-to-finding link in `difftest/registry.py` (`FINDINGS`).
