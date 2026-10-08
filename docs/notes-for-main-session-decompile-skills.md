# Note for the main session — decompile and exploration work the ic2-conquest session can take

> A note the main session can read in one pass. It tells the main session to **write a paste-ready prompt and hand it to the user**, who relays it to the `ic2-conquest` session, instead of doing the work itself. The user is the carrier because PowerShell (main) ↔ WSL (ic2-conquest) session messaging isn't reliable yet.

## How shipping works right now

When you want `ic2-conquest` to do something, **write a paste-ready prompt in the template below and hand it to the user**. The user relays it to the `ic2-conquest` session, the session does the work and commits a draft, the `ic2-research` session picks it up for intake review and promotion. Don't try `SendMessage` — the harness between PowerShell and WSL is not yet reliable. The user relay is the path until we fix the cross-OS link.

## Where you (the main session) read the result

You don't follow the draft on `ic2-conquest`'s `main` and you don't get a "reply" back through the user. The thing you actually look at is the **processed/canonical version in `imperial-conquest-2-research`** — the same repo the main session reads from today. Concretely:

- **Findings** the session writes on `main` are drafts. `ic2-research` does an intake review (same shape as the ai-mover intake this session produced last night) and, on promote, the canonical version moves to `imperial-conquest-2-research/docs/reports/<date>-<topic>.md`. Until that point the version is at `imperial-conquest-2-research/findings/<date>-<topic>.md` (provisional).
- **Exploration runs** land at `run-exp-<name>` on the conquest repo for the binaries, and at `runs/experiments/data/run-exp-<name>/…` for the tracked text outputs. Findings drafts produced by a run follow the same intake/promote pipeline.
- **`ic2-conquest`'s `main` is not a source of truth**. It's the draft side. When you want the authoritative result, query `imperial-conquest-2-research` — the file you're after is the one with the same topic and the most recent date.

Don't ask the main session to read intermediate commits on `ic2-conquest`'s `main`, and don't expect the user to bring anything back other than "your prompt was relayed". The user knows when the canonical version has landed in the research repo.

## What `ic2-conquest` can do

**Decompile:**

- **capstone** x86 disassembly on any byte range of `Imperial Conquest 2.exe` / `Imperial Conquest 2.dat` — `mnemonic / op_str` lines.
- **Ghidra headless** via `analyzeHeadless` + Jython post-script; full decompiler API. Needs Ghidra installed at the path `setup/setup.sh` documents.
- **`struct` / PE / fixed-offset parsing** — the same shape `state/sav.py` uses on `.sav` files, applied to the EXE.
- **Re-run the project extractors** — `runs/experiments/feature_inventory/extract_*.py` produces `function_list.tsv`, `dump_string_literals.v2.tsv`, `form_xrefs.tsv`, `forms.json`, `form_controls.tsv`, `help_topics.v2.tsv`. Deterministic, runs off the EXE + dump.

**Exploration runs of the game** (live driver under Wine/Xvfb):

- Drives the actual `.exe` through `harness/driver.py` (`Game.load`, `Game.move`, `Game.attack`, the battles `stage.py`, the recruit / merc dialogs, etc.) to capture saves and screenshots against a known seed.
- Runs on a dedicated prefix (`~/ic2-work-<exp>`) with its own Xvfb display. The player designates which prefix/display; opening a new one needs an owner `ok`.
- Produces `(prefix + release-<id>)` for the captures: `runs/experiments/data/run-exp-<name>/` for the tracked text outputs, `artifacts/run-exp-<name>/` for the binaries that ship in releases.

## When to ask vs. do it yourself

- **Hand the user a prompt for `ic2-conquest`** when: the EXE has bytes not yet in any tracked artifact; a function body of a named function needs re-reading; a saved field needs re-parsing under a new schema; the harness needs a new live-driver test; an open note in a finding needs a re-look at a specific byte range; or you need a fresh exploration run against a known seed.
- **Do it yourself** when: the question is answered by reading an existing artifact (including `imperial-conquest-2-research`); the question is "cite an existing finding"; the work is front-end coordination (queue next item, intake triage, write up a review).

## Prompt body (paste-ready for the user to relay)

```
To: ic2-conquest
[function / byte range / form / save]: <addr | bytes | form-name | save-name>
[goal]: <what to look for; the cell name; the field; the discriminator>
[evidence form]: <literal text + addresses | opcode mnemonics | tsv/csv | control list | JSON |
                 (alternatively) capture plan: which dialog/seed/steps + saves expected>
[land at]: <tracked path on the agreed branch; commit + push per rule 6; or main for findings drafts;
            (alternatively) release tag run-exp-<name> for an exploration run>
[deadline / size]: <small focused ask vs run-the-whole-experiment>
```

One focused ask per relay — the user hand-carries each one; don't bundle a multi-step plan into a single prompt unless the plan is one round-trip with a single deliverable.

## Example asks — decompile

Each is a paste-ready prompt body.

**Walk a function's basic blocks and caller set:**

```
To: ic2-conquest
[function / byte range]: <addr> (<named function>)
[goal]: capstone-walk the function; list the basic blocks and any calls to other named functions.
[evidence form]: opcode mnemonic list with addresses + a list of named-function call sites.
[land at]: a new findings draft under findings/<date>-<topic>.md on the agreed branch; commit + push per rule 6.
```

**Re-run an extractor with a tighter selector:**

```
To: ic2-conquest
[function / byte range]: the string-literal table at runs/experiments/data/run-exp-feature-inventory/dump_string_literals.v2.tsv
[goal]: re-run extract_dump_strings.py with a selector that keeps only literals whose address falls inside <addr-range>; emit a tracked tsv.
[evidence form]: tsv columns = addr, function_name, literal_text, dump_line.
[land at]: runs/experiments/data/run-exp-feature-inventory/dump_string_literals.<slice>.tsv on the agreed branch.
```

**Decode a DAT fixed-offset table:**

```
To: ic2-conquest
[function / byte range]: DAT offset <hex> (a 5x5 short matrix, 25 words, each row 5 shorts)
[goal]: walk the 25 words with capstone / struct; emit a JSON object indexed by row/column.
[evidence form]: JSON array of row objects; one field per column.
[land at]: a new findings draft under findings/<date>-<dat-table-decoded>.md on the agreed branch.
```

**Find which function reads a constant:**

```
To: ic2-conquest
[function / byte range]: in-memory address DAT_<hex>; in-DAT address <hex>
[goal]: tell me which function(s) read each side (in-memory copy / DAT-copy); disassemble the readers and report.
[evidence form]: per-side: function name + addr + a short disassembly snippet (5-10 lines) that touches the constant.
[land at]: a new findings draft under findings/<date>-<const-readers>.md on the agreed branch.
```

## Example asks — exploration runs

**Drive a dialog with capture:**

```
To: ic2-conquest
[form / save]: form <Name>; seed <int>; (optional) starting save <SAV-name>
[goal]: drive the dialog via Game.*; capture the saves before/after, the driver's per-step log, and the dialog's quoted literals as captured from the live window.
[evidence form]: tracked SAVs (rule 1: SHA-256 in SAVES.sha256; binaries in artifacts/run-exp-<name>/) + a tracked per-step log under runs/experiments/data/run-exp-<name>/.
[land at]: release tag run-exp-<name> for the binaries + an experiment branch for the text outputs + a findings draft on main.
```

**Stage a custom sequence:**

```
To: ic2-conquest
[save / prefix / steps]: starting from <save>; prefix <path>; run steps <N1, N2, N3>
[goal]: stage the sequence and capture the SAVs before/after each step, plus the driver's tile-by-tile log.
[evidence form]: tracked SAVs + a per-step JSON log; both kept under runs/experiments/data/run-exp-<name>/.
[land at]: release tag run-exp-<name> + an experiment branch for the text outputs.
```

**Drive a refusal-text sequence:**

```
To: ic2-conquest
[form / save]: form <name>; starting from <save> on prefix <path>
[goal]: trigger every refusal branch of the form's OK-side handler; capture the rejection literals and the SAV diff at each step.
[evidence form]: a list of (step → literal → SAV diff) tuples, in a tracked tsv under runs/experiments/data/run-exp-<name>/.
[land at]: release tag run-exp-<name> + a findings draft on main.
```

## Do not ask `ic2-conquest` for

- **Writes to other repos** — the conquest repo creates drafts the research repo promotes (rule 2 of CLAUDE.md).
- **EXE patches** without first SHA-256-saving the input file (rule 1).
- **Live harness on the player's display** — use a dedicated `ic2-work-<exp>` prefix; opening a new one needs an owner `ok`.
- **A re-derivation of facts already captured** — reading an existing artifact (research repo, `function_list.tsv`, etc.) is faster than re-running.
- **Multi-step plans in a single relay** — the user hand-carries each one. Bundle only when one round-trip produces one deliverable.

---

This doc is the durable in-repo version of the note. The user carries the same content to the main session as a paste-ready prompt. Both forms should agree on examples, do-not-asks and where-to-look framing. If they drift, the version pasted into the main session is the source of truth for that conversation; this file is the durable artifact for future runs.
