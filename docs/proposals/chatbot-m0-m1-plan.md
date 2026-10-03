# Plan: `ic2-chat` M0 and M1, with outlines of M2 to M6

**Status:** plan for review (2026-10-03). Author: Claude Opus 5.5 (planner). Builds on the merged proposal
`docs/proposals/chatbot.md` (called "the proposal" below). Nothing here is built. Implementer: Sonnet; reviewers: DeepSeek V4.1
Flash, then GPT-6 Sol at medium effort (§7).

## 1. Decisions recorded, and what is still the player's call

**Decided by the player (2026-10-03), items 1 to 3. This plan does not reopen them; item 4 is advice, not a decision:**

1. **Scope:** the chatbot starts now. The scope is **M1 to M6** (`manual` and `assist` modes). `auto` and replay (M7, M8) come only
   after M6.
2. **Transport:** JSON-RPC 2.0 over stdio between two processes (`ic2-chat` starts `ic2-gamed` as a child process).
3. **Roles for each milestone:** Opus plans, Sonnet implements, and `openai/gpt-6-sol` at **medium** effort (never higher) reviews
   each PR. The DeepSeek V4.1 Flash first pass stays.
4. **Location (not decided: it is P1 below, the project's advice).** The advice is to put the code in `chatbot/` and `gamed/` in this
   repository. Each gets its own `pyproject.toml`. `chatbot/` imports nothing from `harness/`, `state/` or `planner/`, and nothing
   from `gamed/` either. `gamed/` is the only code that imports them. The contract in `gamed/schemas/` is where the code would be cut
   if it moves to its own repository later. The design stays movable: the chatbot depends only on a command line that starts the
   service and on the protocol text.

**Still the player's call** (each one blocks only the milestone named):

| # | Question | Blocks |
|---|---|---|
| P1 | Confirm the location (decision 4) | M1 start |
| P2 | Approval gate for `auto`: is an attestation flag enough, or should the program read the issue (§12 Q5 of the proposal) | M8 |
| P3 | Transcripts: on or off by default (Q6) | M6 |
| P4 | Guardrails in §9 of the proposal: the list of irreversible actions, the caps per turn, the allowlist in `auto` (Q8) | M3 (confirm policy), M6 |
| P5 | Is an **attended** `assist` session on the original a "run" under rule 4 (needs an approved issue), or a trial? | the live M6 smoke |
| P6 | Should the reviewer agent be allowed to run the offline tests (today its shell allows only `python3 -m py_compile`, `docs/external-review.md` "The reviewer's shell")? | nothing; affects how much reviewers can check |
| P7 | Run convention on the original: **restart the game and load each turn** (each turn can be replayed on its own), or one process per session (§8 risk R4) | M6 recorder format, M7 |

## 2. Answers to the ten questions of the proposal's §12

**Q1 Transport.** *Decided:* JSON-RPC over stdio. No direct-import spike. The fake backend (§5) makes the process boundary free in
tests, and the boundary is what keeps `chatbot/` free of Wine-era imports.

**Q2 Language.** *Recommend Python 3.12 for both.* The harness, the save parser and the planners are Python. Ubuntu 24.04 ships
3.12.3, the version this machine runs. "Independent program" is a property of the process and the contract, not of the language.
A second language would add a toolchain to `setup/setup.sh` and gain nothing until a GUI exists.

**Q3 Tool calling or strict JSON.** *Recommend tool calling first, with the JSON fallback in M4 behind the same validator.* Both
paths end in one schema check (the contract's order schemas), so the fallback is a parser of about 50 lines, not a second command
layer. It keeps local and cheap models usable. If M4 runs late, the fallback is the part to cut.

**Q4 Memory.** *Recommend structured notes that the program keeps, plus one short free-text field that the model writes.* The
program keeps objectives, standing orders, the threats seen, and the last turn's orders with their verified effects. The model's
own note is capped at about 300 tokens. Facts the program keeps can be checked against `state`; a summary the model rewrites
drifts and can carry an injected sentence from game text into every later turn (§8 R2). Over 24 turns, the facts survive and the
prose does not.

**Q5 Approval gate for `auto`.** *The player decides (P2).* Background: `auto` is M8, outside the current scope. A read-only
`gh issue view` check is about 30 lines. An attestation flag is enough only if the person who starts the run is the player.

**Q6 Transcripts by default.** *The player decides (P3).* Either way, M4's test (no artifact contains the key) covers transcripts.
The recorder writes the system prompt's hash, not its text, as the proposal says.

**Q7 Where it lives.** *Advised: `chatbot/` and `gamed/` in this repository (decision 4), awaiting confirmation (P1).*
Reason: the service imports `harness/`, `state/` and `planner/` from this checkout, and the driver changes every week (28 order
tests, the fleet work). A second repository would need a pin for every driver fix. The import-boundary test (§6, T1) keeps the cut
cheap.

**Q8 Guardrails (§9).** *The player decides (P4).* Two facts from the code that the decision needs:
- `Game.dismiss_popups` answers **every** `Confirm` box **Yes** (`harness/driver.py:417-420`).
- The prompts at peace ("Are you sure you want to attack this city/fleet?") declare war when answered Yes, on the target **and its
  ally** (`findings/2026-10-03-fleet-peace-prompt.md`; `findings/2026-10-02-unit-map-mouse-orders-and-tax-range.md` (b)).

So whatever the player chooses has to be enforced in `gamed` before the click. The driver cannot be relied on to say No. M1 keeps
this out of reach: `move` refuses a target tile that holds a marker (§4).

**Q9 Order of the milestones.** *Recommend keeping M6 before M7.* In `assist` a person approves every order, so nothing runs
unattended. M6's `orders.jsonl` (with the seed, the start save and its SHA-256) is the input that M7 replays, so M7 can replay
anything M6 records, after the fact. `auto` stays after replay (decision 1).

**Q10 A simpler design.** *Recommend these four simplifications, no new architecture:*
- **Hand-written order schemas,** not schemas "generated from the driver's signatures" (proposal §5.2). The driver's arguments are
  UI rows (`recruit(city_row, …)`, `mobilize(city_row, unit_rows)`, `disband_unit(city_row, unit_row)`), which would leak dialog
  rows into the contract.
- **`end_turn` is an order,** not a separate method, so that `order` and `load` are the only calls that change game state.
- **`state` comes from a save file:** an autosave after `load` or `end_turn`, or a Save As snapshot after an order, parsed with
  `state/sav.py`. `legal` is not in M1.
- **M1 uses the standard library only;** `jsonschema` is needed only by the tests.

## 3. Layout, packages, Python, how tests run

```text
gamed/                         ic2-gamed (the only code that imports harness/, state/, planner/)
  pyproject.toml               name "ic2-gamed", requires-python ">=3.12", no runtime deps; [project.scripts] ic2-gamed
  README.md                    how to start it; points at schemas/v0
  schemas/v0/                  the contract: *.schema.json (JSON Schema 2020-12) + examples/*.json
  ic2_gamed/  __init__.py  __main__.py  repo.py  rpc.py  server.py  errors.py  validate.py  state_view.py  walk.py
              backends/  __init__.py  base.py  fake.py  original.py
  tests/      __main__.py  test_rpc.py  test_schemas.py  test_state_view.py  test_validate.py  test_walk.py
              test_fake.py  test_original_offline.py  conformance.py  results.md
chatbot/                       ic2-chat (imports nothing from harness/, state/, planner/, ic2_gamed)
  pyproject.toml               name "ic2-chat", requires-python ">=3.12", no runtime deps in M1; [project.scripts] ic2-chat
  README.md
  ic2_chat/   __init__.py  cli.py  gamed_client.py
  tests/      __main__.py  test_client.py  test_boundary.py
```

- **Packages:** distributions `ic2-gamed` and `ic2-chat`; modules `ic2_gamed` and `ic2_chat`.
- **Python:** 3.12, the system Python of Ubuntu 24.04. Nothing needs `pip install`. Ubuntu's system Python refuses `pip install`
  outside a virtual environment (PEP 668), so everything runs from the checkout, as `tests/` does today. The pyproject files serve
  a later venv install and declare `[project.optional-dependencies] test = ["jsonschema>=4.10"]`. This machine has
  `python3-jsonschema` 4.10.3. M1 task T1 adds the package to `setup/setup.sh`.
- **Launching the service.** From the repository root, `gamed/` is a namespace package, so the service starts as `python3 -m gamed.ic2_gamed --backend fake|original` (a venv install would add the `ic2-gamed` script). `GamedClient`'s command defaults to that, with `cwd` the repository root, and the conformance suite uses the same command. T1 includes a test that runs `python3 -m gamed.ic2_gamed --backend fake` from the root of a clean `git clone` of the branch and gets `hello` back.
- **Finding the repository:** `ic2_gamed/repo.py` puts the repository root (`Path(__file__).resolve().parents[2]`) on `sys.path`,
  the pattern `tests/test_orders.py:15` uses. `backends/original.py` imports `harness.driver` **lazily**, so the fake path never
  touches it.
- **Running the tests (as today: `python3 -m tests.test_orders`, `python3 -m tests.test_sea_path`).** From the repository root:
  `python3 -m gamed.tests` and `python3 -m chatbot.tests` (namespace packages; each `__main__.py` runs every offline `test_*`
  function, prints `PASS`/`FAIL` lines like `tests/test_orders.py:506-514`, and, **unlike that runner, exits 1 on any failure**).
  Each file also runs alone (`python3 -m gamed.tests.test_fake`), and the plain-assert `test_*` functions work under pytest when it
  is installed (it is not on this machine).
- **No game, no LLM:** the offline suites use `FakeBackend`, a stub `Game` object injected into `OriginalBackend`, and the saves
  committed in `saves/`. The original runs only through `python3 -m gamed.tests.conformance --backend original`, which refuses to
  start unless `IC2_GAMED_LIVE=1`.

## 4. Protocol v0 (`ic2-gamed`)

**Framing.** JSON-RPC 2.0. One UTF-8 JSON object per line on stdin, and one per line on stdout, each followed by a flush.
- **No batches** in v0: an array is answered with error -32600.
- A request without an `id` (a notification) is logged to stderr and ignored. The server sends no notifications in v0.
- Lines over 4 MiB get error -32600.
- **stdout carries protocol lines only.** Logs go to stderr. `Game.__init__` defaults to `log=print` (`harness/driver.py:98`),
  which would write to stdout, so the original backend passes `log=lambda s: print(s, file=sys.stderr)`.
- Requests are handled one at a time, in order. EOF on stdin is the same as `shutdown`.

**Versioning.** The `protocol` string is `"MAJOR.MINOR"`, `"0.1"` for M1.
- A minor version only adds optional fields, methods or order names, and clients ignore unknown fields. A major version breaks.
- **While the major version is 0, the client and server must match exactly.** `hello` returns -32001 otherwise.
- The schemas live in `gamed/schemas/v<major>/`. Any schema change bumps the version in the same PR, and a test compares the
  constant in `ic2_gamed/server.py` with `schemas/v0/hello.schema.json`.

**Methods in M1:**

| Method | Params | Result |
|---|---|---|
| `hello` | `{client, protocol}` | `{protocol, server, server_version, backend: "fake"\|"original", exe_sha256\|null, orders: ["move","end_turn"], methods: [...]}` |
| `load` | `{save, seed}` | `{turn, date, current_nation, popups, seed_line, source}` |
| `state` | `{}` | the state object below |
| `order` | `{name, args}` | `{name, effect, popups, retries, turn}` |
| `shutdown` | `{}` | `{}`; the original backend then stops the game (`Game.kill`) and the server exits 0 |

- **`load`:** `save` is a **file name**, resolved only inside an allowlist of directories: `saves/`, `$IC2_WORK/fixtures`, and
  the session folder. A path separator or `..` is error -32602. The model can never name a path. `seed` is an integer, or null for
  the clock. The original backend calls `Game.load(path, seed)`, which restarts the process because the seed is read only at
  program start (`harness/driver.py:462-471`).
- **`order move`:** `args` is `{army, x, y}`. `effect` is `{army, from, to, expected_to, moves_before, moves_after, cell_before,
  cell_after}`.
  - `expected_to` comes from the shared walk model (`walk.py`, §5). A difference between `to` and `expected_to` is reported as
    data, not as an error. It measures the Bresenham assumption on the original.
  - A walk that stops early is a success.
- **`order end_turn`:** `args` is `{}`. `effect` is `{autosave, turn_before, turn_after, date, battles}`.
  - The autosave is **copied into the session folder** at once. Two human seats overwrite each other's `AUTOnnnn.SAV`
    (`findings/2026-10-02-two-human-seats.md`).
  - Any "End turn ?" box answered by the driver shows up in `popups` as `CONFIRM …` (`harness/driver.py:1157-1163`).
  - **The server calls `Game.end_turn` at most once per `order`** and never again after an exception or a timeout (the session becomes degraded, code -32025 below). `Game.end_turn` has its own re-click after 8 seconds with no sign of the turn starting (no new `AUTOSAVE.LOG` line, `harness/driver.py:1138-1148`): that is the driver's rule, which `gamed` does not change (M1 forbids driver changes); it is the one place the driver clicks twice, a missing sign is not proof the first click did nothing, and the plan treats it as an open risk (V6, §8), not as solved. After the call the server checks that the turn or the seat changed; if it did not, the result is `state_changed: "unknown"` and the session is degraded.

**The prechecks for `move`** run in `validate.py` for both backends, before anything is clicked:
- the army exists and has troops;
- its owner is the current nation;
- `moves > 0` (an army with 0 moves cannot be selected, `docs/rules-digest.md` §5 "Moves");
- the target is on the map (320 × 140) and differs from the army's tile;
- **the target tile holds no marker:** its map code is below 12. Cities are 20-99, armies 200-247 and fleets 300-347
  (`docs/sav-layout-notes.md` "Overlay markers"). Clicking a marker is an attack, a resupply or a peace prompt, and the driver would
  answer that prompt Yes.

**`state`, derived from `state/sav.py`.** `state_view.project(parsed, source)` takes the dict from `state.sav.parse` and returns:
- `protocol`, `turn`, `date`, `calendar {season, week, year_bc}`, `current_nation`, `turn_order`, `pending_offer`;
- `nations[]` without `city_list`;
- `cities[]` (all 334);
- `armies[]`: live armies only (the `live_armies` rule, `state/sav.py:162`), each keeping its record `id`;
- `fleets[]`, `mercenaries[]`, `news[]`;
- `source {kind: "loaded"|"autosave"|"snapshot"|"fake", file, sha256}`.

It drops `map` (44,800 values), `size` and `tail_off`. Without the map, the save at turn 0720 serializes to about 95 KB. It is
serialized with `json.dumps(…, separators=(",", ":"), ensure_ascii=False)` in insertion order, so the same save always gives the same
bytes. In the original backend, `state` is the last autosave or loaded save if no order has run since; otherwise it is
`Game.save_as("GAMED_STATE.SAV")` parsed (`harness/driver.py:515-523`), cached until the next order. Both backends go through
`project`, which is what makes the conformance suite meaningful.

**Errors.** Everything that is not a success is a JSON-RPC `error`, with `data = {kind, state_changed: "no"|"yes"|"unknown",
retryable, game_text: [...], detail}`. `game_text` is OCR text read by `Game.read_popup`, often garbled ("ate too lage",
`tests/results.md:36`), so it is shown as text and never parsed.

| Code | kind | When | state_changed |
|---|---|---|---|
| -32700 / -32600 / -32601 / -32602 | standard | parse error, invalid request or batch, unknown method, bad params | no |
| -32001 | `protocol_mismatch` | a different protocol in `hello` | no |
| -32002 | `no_game` | `state` or `order` before `load` | no |
| -32010 | `invalid_order` | a precheck failed; `detail.reason` is one of `no_such_army`, `not_owner`, `no_moves`, `off_map`, `same_tile`, `target_occupied`, `unknown_order` | no |
| -32011 | `order_refused` | the game showed a refusal box and the readback shows no change | no |
| -32012 | `confirm_required` | reserved for M3 (attack at peace); not raised in M1 | no |
| -32020 | `click_swallowed` | `DriverError` "army … not selected" (`driver.py:548`) after the driver's 3 tries, or a move whose readback shows no change and no box after 2 retries by gamed | no |
| -32021 | `unexpected_dialog` | `Game.popups()` is not empty after an order; its text is OCR'd and the box is **left open** | unknown |
| -32022 | `driver_timeout` | "timeout waiting for …" (`driver.py:134`), "end turn timed out" (`:1167`) | unknown |
| -32023 | `autosave_failed` | "autosave: …" (`driver.py:1172`) | yes |
| -32024 | `game_lost` | the game process is gone (reading `/proc/<pid>/mem` fails) | unknown |
| -32025 | `session_degraded` | any order after -32021, -32022 or -32024, until the next `load` | no |
| -32099 | `internal` | any other exception, with the traceback on stderr only | unknown |

`errors.classify(exc)` maps a `DriverError` (`harness/driver.py:89`) to a code by message prefix, through one table. Its test uses
the exact strings from the driver, so a reworded message fails a test instead of falling through silently.

**Worked example** (`>` client to server, `<` server to client; the numbers are those of `tests/results.md:20-22` and the save
`saves/run0-start-AUTO0720-seed12345.SAV` = `BASE.SAV`):

```text
> {"jsonrpc":"2.0","id":1,"method":"hello","params":{"client":"ic2-chat","protocol":"0.1"}}
< {"jsonrpc":"2.0","id":1,"result":{"protocol":"0.1","server":"ic2-gamed","server_version":"0.1.0","backend":"original","exe_sha256":"354d8265…532f","orders":["move","end_turn"],"methods":["hello","load","state","order","shutdown"]}}
> {"jsonrpc":"2.0","id":2,"method":"load","params":{"save":"run0-start-AUTO0720-seed12345.SAV","seed":12345}}
< {"jsonrpc":"2.0","id":2,"result":{"turn":720,"date":"Spring week 1, 270 BC","current_nation":0,"popups":[],"seed_line":"S 0000012345","source":{"kind":"loaded","file":"run0-start-AUTO0720-seed12345.SAV","sha256":"050bc354…"}}}
> {"jsonrpc":"2.0","id":3,"method":"order","params":{"name":"move","args":{"army":0,"x":93,"y":35}}}
< {"jsonrpc":"2.0","id":3,"error":{"code":-32010,"message":"invalid order: target_occupied","data":{"kind":"invalid_order","state_changed":"no","retryable":false,"game_text":[],"detail":{"reason":"target_occupied","code":20}}}}
> {"jsonrpc":"2.0","id":4,"method":"order","params":{"name":"move","args":{"army":0,"x":101,"y":36}}}
< {"jsonrpc":"2.0","id":4,"result":{"name":"move","effect":{"army":0,"from":[100,37],"to":[101,36],"expected_to":[101,36],"moves_before":8,"moves_after":4,"cell_before":2,"cell_after":8},"popups":[],"retries":0,"turn":720}}
> {"jsonrpc":"2.0","id":5,"method":"order","params":{"name":"end_turn","args":{}}}
< {"jsonrpc":"2.0","id":5,"result":{"name":"end_turn","effect":{"autosave":"AUTO0721.SAV","turn_before":720,"turn_after":721,"date":"Spring week 3, 270 BC","battles":[]},"popups":["@ Celtiberia wants to trade with Rome."],"retries":0,"turn":721}}
> {"jsonrpc":"2.0","id":6,"method":"shutdown","params":{}}
< {"jsonrpc":"2.0","id":6,"result":{}}
```

(93,35) is Pisae, a Roman city (map code 20), so the move is refused before any click. (101,36) is a river tile that costs 4
(`tests/results.md:40`).

## 5. FakeBackend and the conformance suite

**What it replays:** real saves. `load` parses a committed `.SAV` with `state.sav.load`, so the fake starts from the original's
true map, armies, cities and calendar. It never invents a start state. From then on, it holds the parsed dict in memory and
changes it.

**What it stubs.** A tiny deterministic rules stub, **labelled "not rules" in the code and in `hello` (`backend: "fake"`)**:
- **`move`** uses `walk.py`, which the original backend's `expected_to` uses too:
  - an integer Bresenham line from the army to the target;
  - each step pays `state.sav.move_cost(code)` for the tile it enters;
  - it stops at sea, a river shape beyond 11 or any marker (code < 2 or ≥ 12);
  - it stops at the first step it cannot afford **and keeps the remaining moves** (the human walk, `docs/rules-digest.md` §5
    "Walking").
  
  The fake then updates the army's `x`, `y`, `moves` and `cell`. It also updates the map: the old tile gets back the stored
  covered cell, and the new tile gets the marker `owner + 200/216/232` by troop count (`docs/sav-layout-notes.md`).
  **`walk.py` must not call `planner.path.turn_legs`:** that function raises `TypeError` on a blocked tile, because
  `passable_cost` returns `None` and `spent + c` is evaluated (`planner/path.py:68-70`; reproduced on Pisae (93,35)). `walk.py`
  uses `planner.path.passable_cost` with an explicit `None` check. Fixing `turn_legs` is a separate small PR, not part of M1.
- **`end_turn`:**
  - The calendar moves on by the digest's rule (`docs/rules-digest.md` §1): week + 2; after week 11, week 1 and the next season;
    after Winter, the BC year decreases by 1. `turn` comes from `state.sav.turn_number`.
  - Each live army's moves go back to the value it had at `load`, a stub, not the tick's formula.
  - Two news lines are appended: `" "` and `"Week  N      Season      YYYBC"`.
  - The new state is written as `AUTOnnnn.json` in the session folder and `effect.autosave` names that file (`AUTOnnnn.json`); the original backend names the copied `AUTOnnnn.SAV`. `effect.autosave_kind` is `"json"` (fake) or `"sav"` (original) and the schema's pattern is `^AUTO[0-9]{4}\.(SAV|json)$`. The server copies or writes the file through the backend's `autosave_to(dst)`, so nothing assumes a `.SAV`.
  - There is no AI, economy, supply or battle.
- Any other order name gets -32010 `unknown_order`. In M3 the fake gains a stub per order, or `not_supported_by_fake`.

**Conformance suite** (`gamed/tests/conformance.py`). It starts the **real server process** (`python3 -m gamed.ic2_gamed --backend
<b>`), talks to it over pipes, and validates every response against `schemas/v0`. The same checks run **unchanged** on both
backends:

1. `hello` matches the schema, uses protocol `0.1` and lists `move` and `end_turn`; `hello` with protocol `9.0` gives -32001.
2. `state` before `load` gives -32002. `load` of `run0-start-AUTO0720-seed12345.SAV` with seed 12345 gives turn 720 and the date
   "Spring week 1, 270 BC". `state` is schema-valid, and army 0 is at (100,37) with 8 moves.
3. A move to (93,35) gives -32010 `target_occupied`; a move of army 999 gives `no_such_army`; a move of a Gaul army gives
   `not_owner`. After each, `state` is byte-identical to the state before.
4. A move of army 0 to (101,36) succeeds with `to` = `expected_to` = (101,36), moves 8 → 4 and cell 2 → 8 (the outcome of
   `test_move`). Every other army is unchanged.
5. `end_turn` gives turn 721, "Spring week 3, 270 BC" and the autosave `AUTO0721.<ext>` (`.json` with `autosave_kind` `json` on the fake, `.SAV` with `sav` on the original; the file named exists in the session folder); army 0 has moves > 0.
6. `shutdown` returns `{}` and the process exits 0 within 15 s. Malformed JSON gives -32700, and the server stays up.

On the fake, the suite runs in `python3 -m gamed.tests` and takes seconds. On the original it is manual: `IC2_GAMED_LIVE=1 python3
-m gamed.tests.conformance --backend original`, needing the environment of `setup/setup.sh`. It takes about 3 to 4 minutes (two
loads at about 25 s, and `end_turn` at about 40 s, `tests/results.md:20-22`). The result is recorded in `gamed/tests/results.md`
with the saves cited, which go to `artifacts/run-exp-gamed-m1/` and the release `run-exp-gamed-m1` (rule 1).

## 6. M1 work breakdown (implementer: Sonnet)

One PR, the tasks committed in this order. Every test below runs offline unless it says otherwise.

| # | Task | Files, names | The test that proves it |
|---|---|---|---|
| T1 | Skeletons, runners, import boundary | both `pyproject.toml`, the `__init__.py` files, `gamed/tests/__main__.py`, `chatbot/tests/__main__.py`; `python3-jsonschema` added to `setup/setup.sh` | `chatbot/tests/test_boundary.py`: an AST scan of `chatbot/**/*.py` finds no import of `harness`, `state`, `planner` or `ic2_gamed`. A runner exits 1 when a test fails (checked with a deliberately failing dummy test) |
| T2 | Schemas v0 | `gamed/schemas/v0/{envelope,hello,load,state,order_move,order_end_turn,error_data}.schema.json`, `examples/*.json` (the §4 exchange) | `test_schemas.py`: every schema passes `Draft202012Validator.check_schema`, every example validates, `PROTOCOL` in `server.py` equals the schema's `const` |
| T3 | JSON-RPC core | `rpc.py`: `read_message(stream)`, `write_message(stream, obj)`, `serve(stdin, stdout, dispatch)`; `__main__.py`: `main(argv)` with `--backend fake\|original`, `--session-dir`, `--save-dir` (repeatable) | `test_rpc.py` on in-memory streams: -32700, -32600 (batch, oversized line), -32601, a notification is ignored, EOF ends `serve`, nothing but JSON lines reaches stdout |
| T4 | State projection | `state_view.py`: `project(parsed, source) -> dict`, `dumps(obj) -> str` | `test_state_view.py`: projecting each of the 14 saves in `saves/` is schema-valid and gives the same bytes twice; for `run0-start…`, army 0 is (100,37) with 8 moves and 23,700 troops, the turn is 720, and there is no `map` key |
| T5 | Prechecks | `validate.py`: `check_move(state_dict, current_nation, args, tile_code) -> None` (raises `OrderInvalid(reason, detail)`; `tile_code` is the map code of the target, which the projected `state` no longer carries: the fake reads it from its parsed save, the original backend from `Game.cell(x, y)`); `walk.py`: `bresenham(a, b)`, `walk(parsed, army, target) -> (to, spent, stop_reason)` | `test_validate.py`: one case for each reason in §4. `test_walk.py`: (100,37) → (101,36) costs 4; a line into Pisae stops before it; an unaffordable mountain keeps the remaining moves; no `TypeError` on blocked tiles |
| T6 | FakeBackend | `backends/base.py`: `class Backend(Protocol)` with `hello_info()`, `load(path, seed)`, `state()`, `move(army, x, y)`, `end_turn()`, `close()`; `backends/fake.py`: `class FakeBackend` | `test_fake.py`: the `test_move` outcome; the map marker and covered cell are swapped correctly; calendar wraps (week 11 Spring → week 1 Summer; week 11 Winter → week 1 Spring, year − 1) |
| T7 | Errors | `errors.py`: the code constants, `RpcError`, `classify(exc) -> RpcError` | `test_errors` (inside `test_original_offline.py`): each driver message quoted in §4 maps to its code; an unknown message gives -32099; the traceback goes to stderr, never into `data` |
| T8 | Server methods | `server.py`: `class Session` (the backend, a `degraded` flag, the allowlist, the session dir), `dispatch(method, params)`; resolving `load` names; `end_turn` copies the autosave | covered by T9 on the fake. `test_rpc.py` adds: a `load` name with `/` or `..` gives -32602; after a forced degrade, `order` gives -32025 until `load` |
| T9 | OriginalBackend | `backends/original.py`: `class OriginalBackend(game_factory=None)`. Lazy `from harness.driver import Game, DriverError`; `Game(log=<stderr>)`; `move` = precheck from game memory (`army_pos`, `army_rec`, `cell`, `i16(CUR_NATION)`), then **not `Game.move`** (it calls `dismiss_popups`, which answers any Confirm box Yes: a click that opened "Are you sure you want to attack ?" would declare war) but `Game.select_army` and `Game.click_tile`, followed by a look at `Game.popups()` **before** anything is dismissed: a Confirm box is answered **No** (`Game.answer(title, yes=False)`), its text goes into the typed error `unexpected_dialog` (-32021) and the session is degraded; only OK-only information boxes are read and dismissed. Readback, at most 2 retries when nothing changed and no box appeared. The marker precheck is a second defence, not the guarantee; `state` uses Save As or the autosave, as in §4 | `test_original_offline.py` with an injected stub `Game` (scripted positions, popups and exceptions): a swallowed click is retried and then gives -32020; a Confirm box after the click is answered No (the stub records which button), gives -32021 and degrades the session, and the stub's `dismiss_popups` is never called while a Confirm is open; `end_turn` is called exactly once even when it raises |
| T10 | Conformance | `gamed/tests/conformance.py`: `run(backend) -> list[result]`, `main()` | runs on the fake inside `python3 -m gamed.tests`; refuses `--backend original` without `IC2_GAMED_LIVE=1` |
| T11 | Chatbot client | `ic2_chat/gamed_client.py`: `class GamedClient(command, cwd, env, timeouts)` with `call(method, params)`, `close()`; it starts the child with an **allowlisted environment** (`PATH`, `HOME`, `LANG`, `IC2_WORK`, `IC2_EXE`, `DISPLAY_IC2` only). `cli.py`: `ic2-chat probe --save NAME --seed N` (hello, load, state summary; no LLM) | `test_client.py` against `python3 -m gamed.ic2_gamed --backend fake`: hello, load, a move, end_turn, shutdown. With `IC2_CHAT_API_KEY=dummy-key-123` and `IC2_RELEASE_TOKEN=x` set in the parent, the child's environment (echoed by a test-only `--debug-env-names` flag that prints **names only**) contains neither |
| T12 | Live run, done by a person or a session that has the game | `gamed/tests/results.md` | `IC2_GAMED_LIVE=1 python3 -m gamed.tests.conformance --backend original` passes. Also the checks from §8 "Verify early" (V1, V5 and the record of V6), with the saves cited |

**Do not:**
- read, print or store any key or token. No `.env` files; nothing under `~/.local/share/opencode*`; `IC2_RELEASE_TOKEN` only as in
  `CLAUDE.md` rule 1;
- import `harness`, `state`, `planner` or `ic2_gamed` from `chatbot/`;
- change the behaviour of `harness/driver.py`, `state/sav.py` or `planner/`. Wrap them in `gamed/`. If a driver change seems
  needed, stop and say so in the PR;
- launch Wine, Xvfb or the game in any offline test. Only `conformance.py --backend original` with `IC2_GAMED_LIVE=1` may;
- write to stdout from `gamed/` except protocol lines;
- commit `.SAV`, `.EXE`, screenshots or anything from `$IC2_WORK` (rule 1);
- call `Game.move` or `Game.dismiss_popups()` from `gamed/` for any click that could open a `Confirm` box (they answer it Yes); the
  original backend clicks with `select_army` and `click_tile` and reads `popups()` first;
- issue `end_turn` twice, or retry it after an exception (the driver's own internal re-click is the one exception, documented in §4 and §8);
- add runtime dependencies, or `legal`, the renderer or the LLM client (M2 to M4).

### Outlines for M2 to M6

| M | Content | Acceptance | Depends on | Needs the game? |
|---|---|---|---|---|
| M2 State, `legal`, renderer | gamed: a `legal` method (my armies with moves > 0, cities that can recruit by `can_recruit_at`, adjacent foreign markers with the relation, the relation radios) and a `tiles` method (a terrain excerpt around a point). chatbot: `state_view/` renders compact text and a diff view from the `state` JSON alone | Golden renders of all 14 committed saves are byte-stable. Every number in a render is checked against `state.sav` for the same save (a gamed-side test that writes a JSON fixture the chatbot test reads). `legal` lists trade targets as clickable, not as accepted (Numidia accepted; others refused or did nothing, `saves/README.md`) | M1 | No |
| M3 Full order set | Orders with hand-written schemas and **semantic arguments**: `recruit {city, type, troops}` (gamed maps the city id to the dialog row and the troop count to spinner presses: 2 × 1000s gave 3,200, `tests/results.md:21`), `attack`, `mobilize`, `disband_unit`, `supply`, `hire_mercs`, `fortify`, `relation`, `taxation`, `build_fleet`, split/join/transfer, change units, fleet orders. **Attack at peace gives -32012 `confirm_required` unless `args.declare_war` is true**, decided in a precheck from relation memory (`NATIONS + 0x26`), per P4 | Offline: prechecks and error mapping with a stub `Game`; fake stubs where cheap. Live (opt-in, about 20 min): the 28 cases of `tests/test_orders.py` re-expressed through the service. Invalid orders never touch the game | M1, M2 (`legal`) | Live part only |
| M4 BYOK and LLM client | `config.py`, `Secret` (`repr` is `***`), an OpenAI-compatible adapter and an Anthropic Messages adapter, timeouts, bounded retries, budgets, the JSON fallback (Q3) | A stdlib `http.server` mock speaking both APIs: a 429, a timeout, a malformed tool call, budget stops, a redirect to another host is not followed, `http://` is refused unless the host is localhost. **Every artifact of a scripted session is grepped for the key: zero hits** | none (can run alongside M2 and M3) | No |
| M5 `manual` mode | REPL: typed commands to `order`, `state`, `end`, `help`, `quit` | Offline: a scripted session on the fake. Live, opt-in: move 0 → (101,36), recruit HI 3,200 at Rome, end. The resulting `AUTO0721.SAV` must be **byte-identical** to `saves/phase0-scripted-turn-AUTO0721.SAV` (sha256 `6bfd9da2…`) | M2, M3 | Live part only |
| M6 `assist` and recorder | prompt assembly (system, strategy brief, program notes and the model's capped note, state view, last results); batch proposal; approve, edit or reject; `runs/<id>/turns/nnnn.md`, `orders.jsonl` (with the seed, the start save and its sha256, P7); metrics produced **by gamed** (a `metrics` method that wraps `state/metrics.py`), because `chatbot/` may not import `state/` | Offline: cassettes drive three turns on the fake and give identical recordings twice. Live: one smoke on the original, done by a person (P5) | M4, M5 | Live smoke only |

## 7. Review plan for each PR

**The chain does not give two reviews in one call.** `scripts/external_review.py` moves to the next model in `--model a,b` only
after an *infrastructure* failure, never after a real review (docstring at lines 2-17; `docs/external-review.md` "Roles"). The
default list is DeepSeek then **Luna** (`DEFAULT_MODELS`, line 35). So each chatbot PR gets **two separate calls**, and the model
list is always passed as an argument:

```bash
python3 scripts/external_review.py --pr N --model opencode-go/deepseek-v4.1-flash#high          # first pass, no label
python3 scripts/external_review.py --pr N --model openai/gpt-6-sol#medium --apply-label         # the review of record
```

`#medium` survives the script: `opencode_watched.effort` rewrites only a missing variant and `max` (lines 79-83), and passes
`--variant medium` (lines 205-206). Nothing stops an operator from typing `#high`, so the PR template (below) states the command.
On exit 3 the fallback is `/review-pr N` on Opus. On exit 4, read the review and decide; do not pay for another review.

**M0 tasks, before the first M1 PR:**
1. **Check that the model id exists for the reviewer.** Run `opencode models openai`, with the reviewer's own `XDG_DATA_HOME`,
   `XDG_CACHE_HOME` and `XDG_STATE_HOME` (`docs/external-review.md` "WSL notes"), and look for `openai/gpt-6-sol`. It prints the
   catalogue, not credentials. `--dry-run` is not enough: it starts no model, and the `unknown-model` check runs only inside a real
   run (`opencode_watched.py:175-192`).
2. **Check that `medium` is a variant the provider accepts for Sol.** The script's comments know only low/high/max for Go. The
   first real Sol review is the test: review this plan's PR with it. A failure shows up as `nonzero-exit` or `unknown-model` in
   `rendered/pr<N>-*/result.json`.
3. Record "chatbot PRs: DeepSeek first pass, then Sol medium" in the roles table of `docs/external-review.md`, in its own small PR.
   The table names Luna today, and changing it is the player's decision 3, written down.
4. The player confirms P1.

**What every reviewer checks first** (put in the PR body, which the brief pastes in):
- The PR body contains the **pasted output** of `python3 -m gamed.tests` and `python3 -m chatbot.tests`. The reviewer cannot run
  them (P6), only `python3 -m py_compile`.
- `git diff --name-only` touches nothing under `harness/`, `state/` or `planner/` (or the PR says why).
- No `import harness|state|planner|ic2_gamed` under `chatbot/`.
- No key-shaped strings, no `.env`, no binaries.
- Every schema change bumps `protocol`.
- No test launches Wine without `IC2_GAMED_LIVE`.
- Any claim about the original cites a save (rule 5).

## 8. Risks, and what to verify early

**Risks:**
- **R1. The driver is fragile.**
  - The first End turn click did not register in 3 of 21 starts (`findings/2026-10-02-start-as-each-nation.md`). The driver
    re-clicks after 8 s (`driver.py:1145-1149`).
  - The field-battle auto-play is flaky (`coverage.md` §1, 🟡).
  - `supply`, `hire_mercs` and `fortify` click recorded coordinates (`driver.py:976-978, 994-997, 1005-1015`).
  - `Game.start` kills **every** Wine process in the prefix (`wineserver -k`, `driver.py:113-120`), so a gamed session and an
    experiment cannot share `$IC2_WORK`. gamed takes a lock file `$IC2_WORK/gamed.lock` and refuses a second session.
  - Mitigation: typed errors, the degraded state, no automatic `end_turn` retry.
- **R2. Prompt injection.** Game text (city names, news, OCR'd boxes) reaches the model. Defences:
  - the command layer accepts only schema-valid orders;
  - `load` takes names from an allowlist;
  - the program keeps the notes (Q4), so injected text does not persist in the model's memory;
  - the chatbot has no tool except `order`.
- **R3. Key handling.**
  - The key exists only in the chatbot process (`Secret`).
  - gamed starts with an allowlisted environment (T11), so neither the LLM key nor `IC2_RELEASE_TOKEN` reaches it or Wine.
  - M4's test greps every artifact of a session for the key.
- **R4. Replay and resume.** The seed is read only at program start (`findings/2026-09-29-loading-a-save-does-not-reseed.md`).
  Resuming after a crash ("load the last autosave with the run's seed", proposal §8) starts a new random stream, so the bytes match
  only if the recorded run also restarted at that turn. Hence P7: restarting each turn makes every turn replayable on its own, at
  about 25 s per turn.
- **R5. Time per turn.** A load takes about 25 s, an order about 5-15 s, `end_turn` about 40 s (`tests/results.md`), plus a Save As
  snapshot for each `state` after an order. Expect 1.5-3 minutes per turn plus LLM time. Client timeouts: 120 s per order, 360 s for
  `end_turn` (the driver's own limit is 300 s, `driver.py:1129`).
- **R6. Stdout pollution.** A stray `print` in the driver path would corrupt the protocol (the default `log=print`). T3's test and
  the original backend's stderr logger guard it.

**Verify early** (V1 and V5 in T12; the others in the first days of M1):
- V1. Does a mid-turn Save As (the `state` snapshot) change the next autosave's bytes? Play the scripted turn twice, with and without
  `save_as` between the orders, and compare the two `AUTO0721.SAV`. If they differ, the snapshot must come from a separate path,
  or snapshots must be off in replayable runs.
- V2. `openai/gpt-6-sol` with `#medium` runs in the reviewer (§7, M0 tasks 1-2).
- V3. All 14 committed saves parse and project (T4).
- V4. stdout stays clean on the original: run the live conformance with stdout piped through a JSON-line checker.
- V5. Bresenham: three live moves (straight, diagonal, a shallow slope over mixed terrain) compare `expected_to` with `to`. A
  mismatch is a finding for `findings/`, not a bug to hide.
- V6. The driver's `end_turn` re-click: `Game.end_turn` clicks End turn a second time after 8 s without a new `AUTOSAVE.LOG` line (`harness/driver.py:1138-1148`). Decide, before M6 runs it unattended, whether that rule is acceptable for `gamed` (the AI seats can take longer than 8 s in a late turn, and a click queued while they run may end the next turn) or whether `gamed` needs a stricter check; any driver change is a separate PR. M1 only records what happens in the live conformance run (the stderr line `end_turn: first click swallowed, clicking again` and the turn number after).

## 9. Corrections to the proposal

1. **§3 and §12 are out of date on tests and fleets.** `tests/test_orders.py` has **28** tests (`TESTS`, lines 499-504), not 17.
   The fleet orders exist: `move_fleet`, `embark`, `disembark`, `attack_fleet`, supply, repair, split, join, transfer, scuttle
   (`harness/driver.py:571-962`). The peace prompts for a city and for a fleet are measured (findings of 2026-10-02 (b) and
   2026-10-03). Only `TBattlePols` (post-battle peace) is still unbuilt (`coverage.md` §1, ⬜).
2. **§5.2 "the schema is generated from the driver's signatures":** the signatures take dialog rows, not game ids (Q10).
   Hand-written schemas with semantic ids instead.
3. **§5.2 "retries a swallowed click at most twice, as the driver does today":** the driver retries the *selection*
   (`select_army`, 3 tries, `driver.py:542-548`). It does **not** check the destination click of `move` (`driver.py:588-595`).
   gamed adds that check.
4. **§5.2 error `confirm_declined`:** the driver never declines. `dismiss_popups` answers every `Confirm` Yes (`driver.py:417-420`),
   and `end_turn` answers "End turn ?" with End turn (`:1157-1163`). Declining must be a gamed precheck (-32012).
5. **§5.2 `end_turn` as its own method:** this plan makes it an order (Q10).
6. **§8 metrics "via the existing `state/metrics.py`" by the chatbot:** that breaks the import boundary of decision 4. gamed
   produces them (M6).
7. **§8 resume after a crash** does not give byte-identical saves unless every turn restarts the game (R4, P7).
8. **§5.4 `recruit rome hi 3000`:** the driver presses 1000s/100s spinners from a non-zero start (2 presses gave 3,200), so a troop
   count needs a mapping in gamed (M3). Whether every count can be reached is not verified.
9. **`planner/path.py` `turn_legs`** raises `TypeError` on a blocked tile (`:68-70`). The proposal's "Paths: per-turn legs" holds
   only for paths from `dijkstra`, which never include blocked tiles.
10. **§13 names GPT-6 Luna** as the second reviewer. Decision 3 replaces it with Sol at medium for this work (§7).
