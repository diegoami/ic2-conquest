---
name: relay-to-research
description: Relay a new finding of this repo to the ic2-research session (and prepare the note for the IC main session) as soon as it is on main. Use every time a findings/ file is added or changed on origin/main, a gate or inventory row is promoted, or the user says "relay", "tell research", "send to ic2-research". Args: the finding path(s); empty = every findings/ file new since the last relay.
---

Relay $ARGUMENTS to the ic2-research session. The player's standing rule (2026-10-05, restated 2026-10-08):
**when findings are available, relay them to ic2-research at once, without asking.** This repo never writes
to the research repo (CLAUDE.md rule 2); the research session's intake promotes the draft.

## 1. Pick what to relay

- With arguments: those paths.
- Without: `git fetch -q origin && git diff --name-only --diff-filter=AM <last-relayed-commit> origin/main -- findings/`.
  The last relayed commit is in the memory file `research-intake-relay.md` ("Last relay"); if missing, ask.
- Relay only what is **pushed to origin/main** (or a pushed experiment branch, named as such). Push first if needed.
- Skip `PROMPT-*`, `*.json`, `*.skeleton.md` helper files unless asked.

## 2. Gather, per finding (read the file; never guess)

- path, branch, commit SHA that added/changed it (`git log -1 --format=%h -- <path>`), PR number if any;
- the answer in 1–3 lines, and the tag (`[confirmed]`, `[confirmed, partial]`, `[derived]`);
- which inventory/ledger rows it moves (e.g. "L11 198-armies: `[derived]` → `[confirmed, partial]`");
- evidence: `runs/experiments/data/run-exp-<name>/`, release `run-exp-<name>` URL, the cited save filenames
  (rule 5: every claim cites a save);
- corrections to earlier notes or to research's reports, and known slips / open questions.

## 3. Send

1. `ListAgents`; find the research session (name contains `ic2-research` or "IC2 CONQUEST RESEARCH").
2. `SendMessage` to it with the message below (one message for several findings).
3. If it is not listed or the send fails: do not retry another way. Print the same message as a
   paste-ready block for the player, and say it was not delivered.

Message shape:

```
New finding(s) on diegoami/ic2-conquest main, ready for intake:

1. findings/<file>.md  (commit <sha>[, PR #n])
   Answer: <1-3 lines>. Tag: <tag>.
   Moves: <rows>. Corrects: <earlier notes, or "none">.
   Evidence: runs/experiments/data/<dir>/ ; release <url> ; saves <names>.
   Open: <slips / not established>.
```

## 4. IC main session

IC main (PowerShell) reads only promoted reports, and cross-OS messaging is unreliable
(memory `user-relay-until-cross-os-messaging-works`). Do not SendMessage it; end your reply with one line for
the player: "IC main: <finding> relayed to ic2-research; it reaches IC main once promoted."

## 5. Record

Update memory `research-intake-relay.md` "Last relay: <origin/main sha>, <date>, <files>" and the findings
baseline in `report-new-findings-on-main.md`. Tell the player in one line what was relayed and to whom.
