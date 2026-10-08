# Note for the main session — decompile skills the ic2-conquest session can take

The **ic2-conquest session** (this VM; discoverable via `ListAgents` as `ic2-conquest`) is staffed this run with decompile skills the main session does not have to do itself. Send the work here; the session will hand back cited evidence and a tracked file.

## Capabilities

| Skill | When to use it |
|---|---|
| **capstone x86 disassembly** | Walk any byte range of `Imperial Conquest 2.exe` (or `.dat`); output `mnemonic / op_str` lines. |
| **Ghidra headless** (`analyzeHeadless`) | Drive the full decompiler API in a Jython post-script. Needs Ghidra installed (see `setup/setup.sh`). |
| **`struct` / PE / fixed-offset parsing** | The same shape `state/sav.py` uses on SAVs, applied to the EXE for fixed addresses the decompile reports name. |
| **Re-run the project extractors** | `runs/experiments/feature_inventory/extract_*.py` → `function_list.tsv`, `dump_string_literals.v2.tsv`, `form_xrefs.tsv`, `forms.json`, `form_controls.tsv`, `help_topics.v2.tsv`. Deterministic. |
| **Live harness** | Wine/Xvfb on a dedicated prefix (`~/ic2-work-<exp>`); the AI-mover contact work used `:601` and prefix `ic2-work-contact`. |

Past work using these skills is visible in `findings/2026-10-04-battle-exchange-hook.md` (capstone + unicorn on `tests/test_battle_hook_build.py`) and in `state/sav.py` / `state/battle.py` / `state/battle_block.py` (the constants are decompile-shaped Python).

## When to send a request vs. do it yourself

- **Send here** when: the EXE has bytes not yet in any tracked artifact; the function bodies of named functions need re-reading; a saved field needs re-parsing under a new schema; the harness needs a new live-driver test; an open note in a finding needs a re-look at a specific byte range.
- **Do yourself** when: the question is answered by `Read` of an existing artifact; the question is "cite an existing finding"; the work is front-end coordination (queue next item, intake triage, write up a review).

## Request template (SendMessage body)

```
To: ic2-conquest
[function / byte range / form / save]: <addr | bytes | form-name | save-name>
[goal]: <what to look for; the cell name; the field; the discriminator>
[evidence form]: <literal text + addresses | opcode mnemonics | tsv/csv | control list | JSON>
[land at]: <tracked path; commit+push per rule 6; or main for findings drafts>
[deadline / size]: <how long is OK; small focused ask vs run-the-whole-experiment>
```

## Example asks

- *"Capstone-walk `FUN_00456ca0` (TAboutIC_Cancell); show the construction call to TCellAuto and any guard, so H04's reproduction path is anchored byte-exact. Land at `findings/2026-10-08-…-decompile.md` on main."*
- *"Re-run `runs/experiments/feature_inventory/extract_dump_strings.py` with a selector for `dword ptr` references in FUN_0044d420 — emit a tracked tsv of the readback so I can cite the river-cost readback in the next finding."*
- *"Pull a 5×5 melee-matrix candidate from DAT offset `0x1F7A6` with capstone, decode the `[short][short][short][short][short]` records per type, and emit JSON so I can cross-check against the existing `combat-type-effectiveness-matrix.md`."*
- *"Disassemble the per-type combat value field at offset `+0x26` of the unit-type-stat table; decode the 5 words and tell me which function reads them (DAT `0x1F2F0`-derived constants vs in-memory `DAT_00478FD6`)."*

## Do not ask for

- **Writes to other repos** (rule 2: the conquest repo creates drafts the research repo promotes).
- **EXE patches** without first SHA-256-saving the input file (rule 1).
- **Live harness work on the player's display**; use a dedicated `ic2-work-<exp>` prefix (the existing `:601` is fine; opening a new one needs an owner `ok`).
- **A re-derivation of facts already captured in a committed artifact** — `Read` is faster than re-running.
- **Multi-step plans** in a single message — the session will ask for one focused ask at a time.

## Reply shape

Each request gets:

1. The cited addresses / literals / opcode snippets (verbatim, with byte offsets where they apply).
2. A tracked file path + commit hash on the agreed branch (rule 6 measurements-kept).
3. The decompile vehicle used (capstone / Ghidra headless / extractor / harness / Sav-parse).
4. Any **open notes** the work turned up — so the next ask lands cleanly.

Anything that needs a multi-step plan, a feature-branch side-effect, or a prefix change gets a clarification round first.
