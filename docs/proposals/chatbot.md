# Proposal: `ic2-chat`, a BYOK chatbot that plays the original game through the headless wrapper

**Status:** proposal for review (2026-10-02). Nothing here is built. Author: Claude Sonnet 5.5, for the player.
Reviewers: please answer the questions in §12 and flag anything in §3-§10 that you would change.

## 1. What the player asked for

A **chatbot** that drives the original *Imperial Conquest 2* through this repository's headless wrapper, with these
constraints (the player's words, 2026-10-02):

- an **independent program**: not a Claude Code agent, not a skill, not tied to any one assistant;
- it uses an **external LLM with BYOK** (bring your own key): the user supplies the endpoint, model and key;
- the proposal is **reviewed before** anything is built.

It builds on the direction already recorded in `docs/intent-and-approaches.md` ("Keep ic2-conquest, add modes";
trainer: typed commands and an agent, configurable URL and key).

## 2. Goals and non-goals

**Goals**

1. A person (or a model) plays the original game turn by turn through plain-language chat or typed commands.
2. Every game action goes through one **narrow, validated command set**; the model never gets a shell, files, or the
   network beyond its own LLM endpoint.
3. **BYOK done safely**: the key is never written to the repo, a log, a transcript or a prompt.
4. **Replayable**: every order and every turn's save is recorded, so a game the model played can be re-run from the
   seed and checked (this is what turns "the model played well" into evidence, `CLAUDE.md` rule 5).
5. **Testable without the game and without a real LLM**: a fake game backend and recorded LLM responses.
6. Works with **any OpenAI-compatible endpoint** (OpenRouter, OpenCode Zen/Go, OpenAI, a local server) and, as a
   second adapter, Anthropic's Messages API.

**Non-goals**

- Not a replacement for the exploration work (`findings/`, `coverage.md`); the chatbot **never writes findings**.
- No training, fine-tuning or reinforcement learning.
- No new game rules: the original game is the only rule source (the reimplementation is a possible later backend).
- No GUI/web front end in the first version (a terminal chat).
- Not speed-optimised: a turn on the original takes 30-60 seconds (Wine, UI-driven), which is fine for chat.

## 3. What exists today (the inputs)

| Piece | Where | State |
|---|---|---|
| Order driver (`Game`) | `harness/driver.py` | about 25 orders: move, attack (siege and field battle), recruit, mobilize, join/split/transfer armies, change units (rename, split, join, disband), supply, hire mercenaries, fortify, relations, taxation, build fleet, end turn. Each is checked on a save diff (`tests/test_orders.py`, 17 tests). |
| Save parser | `state/sav.py` | SAV to a dict: nations, cities, armies, fleets, news, relations; `summary()` already renders text. |
| Paths | `planner/path.py` | Dijkstra over DAT terrain costs; per-turn legs. |
| Determinism | `patches/seed_patch.py` | the build reads `SEED.TXT` at program start; a turn is repeatable if the process restarts with the seed (`findings/2026-09-29-loading-a-save-does-not-reseed.md`). |
| Per-turn autosave | the `rollingsave` build | every human turn writes `AUTOnnnn.SAV` and an `AUTOSAVE.LOG` line. |
| Run format | `CLAUDE.md` "Runs" | `runs/<id>/turns/nnnn.md`, `metrics.csv`, `armies.csv`, release `run-<id>` for binaries. |

**Gaps that limit the chatbot:** fleet orders (embark, unload, move, attack), accepting a post-battle peace
(`TBattlePols`), a few dialogs still on recorded coordinates; and the driver's known fragilities (a click into an
inactive window, a File > Save that clears the selected army, an "End turn ?" box when an army needs supplies).

## 4. Constraints inherited from this repository (`CLAUDE.md`)

1. No EXE, DAT, screenshot or video in git. Saves and screenshots go to a release `run-<id>`.
2. Never write to another repository. Rule discoveries go to `findings/`; the chatbot does not.
3. The player's words in a strategy file are never edited; the bot writes only in its own sections.
4. **No run starts before the player approves it** in the run's GitHub issue. An autonomous chatbot game is a run.
5. Every claim of progress cites a save.
6. No secrets in git, ever.

## 5. Architecture

### 5.1 Overview

Two programs and one contract. The chatbot does not import the harness; it talks to a **game service** over a small
protocol. That keeps it independent, lets it run on a different machine or runtime than Wine, and lets every test run
against a fake game.

```text
 you / terminal
      |
 +----v--------------------------------------------+        HTTPS (your key)
 |  ic2-chat  (the chatbot, independent program)    +-----------------------------> LLM endpoint
 |  - chat loop and modes                           |   OpenAI-compatible, or Anthropic
 |  - LLM client (BYOK)                             |
 |  - command layer: validate, tool schema          |
 |  - state renderer, turn memory                   |
 |  - recorder (transcript, orders, save names)     |
 +----+---------------------------------------------+
      | JSON-RPC 2.0 over stdio (or a local socket)      the "game contract"
 +----v---------------------------------------------+
 |  ic2-gamed  (game service)                       |
 |  backend: OriginalBackend  = harness.Game + state.sav   (Wine, Xvfb)
 |           FakeBackend      = scripted/recorded states   (tests)
 |           (later) ReimplBackend = IC2.Cli
 +--------------------------------------------------+
```

**Why a service and not a library import:** (a) the chatbot needs no Wine, mingw or X11 and can be developed and
tested anywhere; (b) the contract is the only thing the harness must keep stable, and it is small; (c) a crash or hang
in the UI driver cannot take down the chat; (d) the same contract serves a second backend later; (e) it keeps the
"independent program" requirement honest. The cost is one more process and a protocol to version (§5.2); a direct
`import harness` adapter stays possible for a first spike (§10, M1).

### 5.2 The game contract (`ic2-gamed`)

JSON-RPC 2.0, one request per line on stdin/stdout, newline-delimited. All methods are synchronous from the caller's
view (the service queues UI work; it never runs two orders at once). Versioned by a `protocol` field in `hello`.

| Method | Meaning | Returns |
|---|---|---|
| `hello` | handshake: protocol version, backend name, build hash, seed | capabilities |
| `new_game` / `load(save, seed)` | start from a save or a new Rome game with a seed (restarts the game process: the seed is read at program start) | turn, date |
| `state` | the current game state, structured | nations, cities, armies, fleets, relations, news since last call, `turn`, `date` |
| `legal` | what can be ordered now (armies with moves, cities that can recruit, adjacent targets, nations that can be traded with) | lists, so the chatbot can validate before it asks the game |
| `order` | one order: `{name, args}`; returns `{ok, effect, popups, save_diff}` where `effect` is read back from memory or the save, never assumed | result |
| `end_turn` | ends the human turn, plays the AI seats, returns the autosave name and the AI's news | new turn |
| `save(name)` | explicit save | file name |
| `shutdown` | stop the game and the service | - |

Orders are a closed set, one JSON schema each (`move`, `attack`, `recruit`, `mobilize`, `join`, `split_army`,
`transfer_units`, `change_units`, `supply`, `hire_mercs`, `fortify`, `relation`, `taxation`, `build_fleet`, ...). The
schema is generated from the driver's signatures, so the chatbot's tool list and the service cannot drift. **Errors
are data**: `{ok: false, code, message}` (for example `army_has_no_moves`, `not_adjacent`, `confirm_declined`), never
a crash. The service enforces "never click End turn twice" and retries a swallowed click at most twice, as the driver
does today.

### 5.3 The chatbot (`ic2-chat`)

Components, each a module with one job:

1. **Config and BYOK** (§6).
2. **LLM client**: one interface, `complete(messages, tools) -> assistant message`, with two adapters:
   *OpenAI-compatible chat completions* (`/v1/chat/completions` with `tools`/`tool_calls`; covers OpenRouter,
   OpenCode, OpenAI, local servers) and *Anthropic Messages* (`tool_use`). A model without tool calling falls back to
   a **strict JSON command block** parsed and schema-validated by the chatbot. Timeouts, bounded retries with backoff,
   a per-turn token and money budget (§6.4).
3. **State renderer** (§7): turns the structured state into a compact, stable text view for the model.
4. **Command layer**: the tool list (from the contract's schemas), argument validation against `legal`, a per-turn
   action cap, and the translation of results back into model-readable text. The model's only way to act is a tool
   call; its free text is shown to the user and never executed.
5. **Turn memory**: the conversation is *not* an ever-growing transcript. Each turn the model gets the system prompt,
   the strategy brief, a short **rolling summary** the model itself maintained (a few hundred tokens), the new state
   view, and the last turn's results. Older turns are in the recorder, not in the prompt.
6. **Recorder** (§8).
7. **Modes** (§5.4) and the **terminal UI** (a plain REPL; `rich` or `prompt_toolkit` optional).

### 5.4 Modes

| Mode | Who decides | Use |
|---|---|---|
| `manual` | you type commands (`recruit rome hi 3000`, `move 0 101 36`, `end`); no LLM | the trainer; also the way to try the game and the contract |
| `assist` | the model proposes a batch of commands for the turn; **you approve, edit or reject** before anything runs | the default for a new model or strategy |
| `auto` | the model plays up to N turns, with stop conditions (below) | a run; **requires `--run-id` and `--approved-issue`** (§9) |

Stop conditions in `auto`: turn budget reached; money budget reached; the model asks for help; an order fails twice in
a row in the same way; a game event the strategy marks as a stop (a capital under siege, an offer of peace); the
player's kill switch (Ctrl-C finishes the current order, writes the recording, and stops).

Chat on top of the modes: you can ask "why did you move army 0 north?" or "what is Gaul doing?" at any point; the
model answers from the state view and its own notes, and a question never issues an order.

## 6. BYOK and secrets

1. **Where the key lives.** The environment (`IC2_CHAT_API_KEY` or a name you configure per provider) or the OS
   keychain through `keyring`. A config file holds only the *name* of the variable, never the key.
   `~/.config/ic2-chat/config.toml` is outside the repository; a repo-local `chat.local.toml` is git-ignored.
2. **What the config holds:** `provider` (`openai-compatible` | `anthropic`), `base_url`, `model`, `api_key_env`,
   `temperature` and other parameters, budgets, timeouts. Nothing else.
3. **Never leaked.** The key is read once, held in memory, sent only in the `Authorization` header to `base_url`. It
   is redacted from every log line and exception (a `Secret` wrapper whose `repr` is `***`), never put in a prompt,
   transcript, recording or crash report, and the process refuses to start if the key variable is set in the *game
   service's* environment (the service never needs it). A test greps every artifact of a scripted session for the key.
4. **Budgets.** `max_turns`, `max_tokens_per_turn`, `max_cost_usd` (from a price table you provide, or a token cap if
   none), a hard timeout per LLM call. Exceeding any stops the run cleanly with the state saved.
5. **Endpoint trust.** `base_url` must be `https` unless it is `localhost`; the chatbot does not follow redirects to a
   different host with the key attached.
6. **Pre-commit guard.** A repo test fails if a file contains a string shaped like a key (`sk-`, `Bearer `, 40+ hex)
   under `chatbot/`, `runs/` or `docs/`.

## 7. The state view (what the model sees)

Compact, deterministic text; the same save always renders the same bytes (golden-tested). Sections, in order:

1. `date`, turn number, season, weeks to the next season, whose turn.
2. **Mine**: treasury, tax, income estimate, mobilization, unity, cities (name, x,y, population, fortification,
   loyalty, whether it can recruit, the queue), armies (id, x,y, terrain, troops by type, units, moves, supplies %,
   morale, money), fleets (when launched).
3. **Near me**: foreign armies and cities within a radius of each of my armies and cities (owner, relation to me,
   distance, troops if visible), plus relations with every nation (peace/trade/alliance/war and cooldowns).
4. **News** since my last turn, and anything pending (an offer, a war declared on me).
5. **Legal now**: from `legal`, as short lists, so the model does not invent actions.
6. **Last turn**: my orders, each with its verified effect or its error.

The renderer works from the structured `state` (not the raw save), and a **diff view** (what changed since last turn)
keeps long games inside the token budget. `state.sav.summary()` is the seed of the renderer.

**Prompt injection.** Everything in the state view is game data, including city names and news text. The system prompt
says so, the model has no tool but the command set, and an invalid or unexpected command is rejected by the command
layer, not trusted. The chatbot never evaluates, fetches or opens anything the model or the game text names.

## 8. Recording and replay

Each turn writes, under `runs/<run-id>/`, the **same files the project already uses**:

- `turns/nnnn.md`: intent (the model's stated plan, trimmed), the orders, expected versus actual effect, surprises;
- `orders.jsonl`: one line per order `{turn, seq, name, args, ok, effect}`: **the canonical, replayable record**;
- `transcript.jsonl`: model messages and tool calls per turn, **with the key and the system prompt hash, not the
  prompt text** (the prompt text is reproducible from the version); optional and off by default for privacy and size;
- `metrics.csv`, `armies.csv` via the existing `state/metrics.py`;
- the saves `AUTOnnnn.SAV` of every turn: in `artifacts/run-<id>/` (git-ignored) and in the
  release `run-<id>` (the bot creates it at the first batch and uploads after each, `CLAUDE.md` rules 1 and 6).

**Replay:** `ic2-chat replay runs/<id>` restarts the game with the recorded seed and start save, re-issues
`orders.jsonl` through the same service, and compares each turn's save with the recorded one **byte for byte**. A
mismatch is reported with the first differing offset. This is what makes a model's game *evidence*: an LLM's choices
are not repeatable, its orders are. (Byte-repeatability of scripted turns and of a field battle was already shown:
`tests/results.md`, `runs/experiments/gallic-army/`.)

**Resume after a crash:** the service restarts the game, loads the last autosave with the run's seed, and the
chatbot continues; a half-issued order is re-checked against the state before it is re-sent.

## 9. Guardrails

- **Capability boundary.** The model can only call commands from the contract. No shell, no file access, no HTTP.
  The chatbot has no code path that executes model text.
- **Per-turn limits.** Max orders per turn, max retries per order, no order twice in a row with the same arguments if
  it failed.
- **Irreversible actions** (declare war by attacking a nation at peace, disband an army, scuttle, accept a peace
  treaty) need an explicit confirmation in `assist` mode and a strategy-level allowlist in `auto`.
- **Run approval (rule 4).** `auto` refuses to start without `--run-id N --approved-issue M`; the program writes both
  into the run's first line. It cannot verify the approval (it is a comment on a GitHub issue), so this is an
  *attestation* by the person who starts it; the proposal asks reviewers whether a read-only `gh` check is worth it.
- **Strategy files.** The strategy brief given to the model is read from `strategies/<name>.md`; the chatbot never
  edits it. Its notes go into `runs/<id>/` only ("Trials" sections are written by a person or by the bot's own
  section rule).
- **Never** two End-turn clicks; **never** a state-changing call outside `order` / `end_turn` / `load`.

## 10. Implementation plan

Milestones, each with an acceptance test that does not need an LLM or the game unless stated. Sizes are rough
(S about 0.5 day, M 1-2 days, L 3+ days). Dependencies in brackets.

**M0. Review and decisions (S).** This document reviewed; answers to §12 recorded; protocol and repo layout fixed.

**M1. The game contract and a fake backend (M).** Create `chatbot/` (own `pyproject.toml`, own entry point) and
`gamed/`. Define the JSON-RPC methods and schemas; implement `FakeBackend` (replays recorded states and
accepts orders against a tiny rules stub); implement `ic2-gamed` for the original as a thin wrapper over
`harness.Game` and `state.sav` (`hello`, `load`, `state`, `order` for `move` and `end_turn`).
*Acceptance:* a conformance suite runs unchanged against `FakeBackend` and, manually, against the original; the move and
end-turn orders match `tests/test_orders.py` outcomes.

**M2. State and `legal` (M) [M1].** Structured `state`; `legal`; the text renderer with golden files built from the
saves already in `saves/`; the diff view.
*Acceptance:* renders are byte-stable; every number in a render is checked against `state.sav` for the same save.

**M3. The full order set and validation (M) [M1].** Expose every driver order through `order` with a JSON schema, a
verified `effect` and typed errors; the chatbot-side validator uses `legal`.
*Acceptance:* the 17 order tests pass through the service; invalid orders are rejected before the game is touched.

**M4. BYOK and the LLM client (M).** Config, `Secret`, the two adapters, retries, timeouts, budgets, the JSON fallback.
*Acceptance (offline):* a local mock server speaking both APIs; tests for budget stops, a 429, a timeout, a malformed
tool call, and **a test that no artifact of a scripted session contains the key**.

**M5. `manual` mode (S) [M2, M3].** The REPL: typed commands, `state`, `end`, `save`, `help`.
*Acceptance:* a scripted session reproduces the Gallic-army experiment's first turns through the service.

**M6. `assist` mode and the recorder (M) [M4, M5].** The prompt (system, strategy, summary, state view, last results),
batch proposal, approve/edit/reject, `turns/nnnn.md`, `orders.jsonl`, metrics.
*Acceptance (offline):* recorded LLM responses ("cassettes") drive three turns on the fake backend and produce
identical recordings; one live smoke on the original, by a person.

**M7. Replay (M) [M6].** `ic2-chat replay` with the byte comparison and a first-difference report.
*Acceptance:* a recorded three-turn scripted sequence on the original replays byte-identical twice.

**M8. `auto` mode (M) [M7].** Stop conditions, budgets, resume after a crash, the approval attestation.
*Acceptance:* the stop conditions fire on the fake backend; a killed process resumes from the last save.

**M9. High-level commands (L) [M3, fleet orders].** Macros over orders with the path planner: `defeat(target)`,
`retreat_for_winter(army)`, `raid(target)`; fleets and embark come with the missing fleet orders.
*Acceptance:* each macro is a tested sequence of verified orders; a macro that cannot finish says why.

**M10. Evaluation (M) [M8].** A runner that plays the same seed with different models or strategies and tabulates
cities held, population, losses, treasury, turns survived, tokens and cost, so models can be compared and a strategy
claim has numbers behind it.

**M11. Optional.** `ReimplBackend` over `IC2.Cli`; a Windows-native client talking to the WSL service; a web front end.

A first usable slice is **M1 to M6** (manual and assist). `auto` and replay are M7 and M8 on purpose: a model should
not play unattended before the recording that makes its play checkable exists.

### Repository layout

```text
chatbot/         ic2-chat: config, llm/, state_view/, commands/, modes/, recorder/, cli.py   (own pyproject)
gamed/           ic2-gamed: the service, backends/ (original, fake), schemas/                (own pyproject)
docs/proposals/  this file
runs/<id>/       turns/, orders.jsonl, metrics.csv ...                                       (text only)
```

`chatbot/` imports nothing from `harness/`, `state/`, `planner/`; `gamed/` is the only code that does. If the
chatbot later needs its own repository (a web UI, heavy dependencies, a different release cadence), the contract in
`gamed/schemas/` is the boundary to cut along.

## 11. Testing strategy

- **Contract tests** against `FakeBackend` (always) and the original (manual, slow).
- **Golden renders** of the state view from the saves in `saves/`.
- **Cassettes**: recorded LLM request/response pairs replayed offline, so tests are deterministic and free.
- **Secret tests**: grep every artifact of a scripted session for the key; a key-shaped-string scan of the repo.
- **Replay tests**: recorded order sequences reproduce saves byte for byte on the original (manual or in the nightly
  environment that has Wine).
- The existing 17 order tests stay as the driver's own checks.

## 12. Risks and open questions for the reviewers

**Risks.**
1. *Driver fragility* limits unattended runs: swallowed clicks, a save that clears the selection, unexpected boxes.
   Each unexpected dialog is a failure of the service, not of the model; M3 and M8 must handle them as typed errors.
2. *Model quality and cost*: a cheap model may play badly or loop. Budgets and stop conditions bound the damage; M10
   measures it.
3. *Prompt injection* through game text is low-probability but the command boundary must hold (§7, §9).
4. *Time per turn* (30-60 s on the original) makes a 24-turn run 12 to 25 minutes of game time plus LLM time.
5. *Scope creep*: macros (M9) and fleets depend on driver work that is not done.

**Questions.**
1. **Transport:** JSON-RPC over stdio between two processes (proposed), or a plain Python import with a `Backend`
   protocol for the first version, splitting later? Which is the cheaper correct start?
2. **Language/runtime:** Python for both (proposed, the harness is Python); is there a reason to write the chatbot in
   another language, given "independent program"?
3. **Tool calling vs. strict JSON:** require tool calling and drop models without it, or keep the JSON fallback
   (more code, wider model support)?
4. **Memory design:** rolling self-written summary (proposed) versus structured notes the program maintains
   (objectives, standing orders, threats). Which survives a 24-turn game better?
5. **Approval gate (rule 4):** is an attestation flag enough, or should `auto` read the GitHub issue (read-only) and
   check for the player's approval comment?
6. **Transcripts:** record model text by default (useful for review, bigger, may contain strategy reasoning), or only
   orders (proposed) with transcripts opt-in?
7. **Where it lives:** `chatbot/` and `gamed/` in this repository (proposed) or a separate repository from day one?
8. **Anything in §9 you would allow the model to do that is forbidden, or forbid that is allowed?**
9. Are the milestones ordered so that nothing unattended runs before the recording exists? Should M7 (replay) come
   before M6?
10. Is there a simpler design that meets the same goals?

## 13. How this proposal gets reviewed

1. A PR with this file only. 2. `python3 scripts/external_review.py --pr <n>` (DeepSeek V4.1 Flash, then OpenAI GPT-5.6
Luna, the default chain since 2026-10-05; the quota check first, `CLAUDE.md` L50) for the first pass. 3. A Claude Opus pass with `/review-pr <n>` as the second opinion. 4. The player decides,
answers §12, and approves milestones; nothing is built before then.
