# Task: in-play corroboration of the strategic AI turn (research pending request, 2026-10-07)

The research repo's `docs/reports/2026-10-07-strategic-ai-turn.md` (as corrected at commit `7d7b613` — read THAT
version; the JoinFleets reversal and asymmetry #6 correction are in it) is decompile-only. This task corroborates
its rules in play, on a fixed seed, through the EXPLORE runner. The research request accepts any subset; the
checks in priority order:

1. **The week-11 tax policy** (`FUN_0044ffbc` §2.3): an AI nation's `+0x44A` tax moving at the season's last week
   by the cut/raise/zero rules — cut to `max(5, tax−6)` if unity < 650 or treasury > wealth/2000; raise to
   `min(40, tax+9)` if treasury < 0 or (own ≤ threat and treasury < 1000); zero if treasury > 0 and unity < 500.
   Cheap to watch: `state/sav.py` parses every nation's tax, unity, treasury and wealth, so a SAV per End turn
   gives the moves and their triggers directly.
2. **A free AI mercenary hire** (`FUN_0044e41c` §3.2): an at-war AI army with money > 50 acquiring a pool offer
   within Chebyshev 4 of its tile, with no payment anywhere in the diff (army purse and treasury unchanged).
3. **A homeland intercept dispatch** (`FUN_0044efc8` §3.1): an own AI army diverting toward a threatening foreign
   army (within 20 of the capital at war, 10 otherwise) instead of its usual target.
4. **A fleet hunt-vs-port decision** (`FUN_0044f4f8`/`FUN_0044e9a8` §4): a fleet chasing an enemy fleet (score
   ≥ 100) vs sailing to a resupply port, and the foreign-port purchase at amount/5.

## Scope
This task protects: **the fidelity of the four rules as the clone will implement them** — every observed move is
tied to its trigger values read from the same save, the fixed seed is stated and restartable, and what a check
does NOT observe is said so (a staged situation is labelled as staged). The decompile's claims are never restated
as observed: a row is `[derived]` (report citation) or `[confirmed]` (this experiment's saves), never mixed.

Forbidden results: a run without a save behind every turn; a claim of a rule move without the before/after saves
and the trigger values; an unlabelled staged situation; a measured output overwritten or deleted; a binary in
git; a write to another repository (the draft goes to this repo's `findings/`, the research session promotes it);
processes killed by pattern; a click at a guessed position.

## Read first
- The corrected report §2.2-2.3, §3.1-3.2, §4 and its "What this does not establish"
  (`/home/diego/projects/imperial-conquest-2-research`, commit `7d7b613`).
- `CLAUDE.md` rules 1-7 (rule 6's cadence: commit and push after each batch).
- `state/sav.py` (nation tax/unity/treasury/wealth, armies, mercenaries), `harness/driver.py` (`Game.load`,
  End turn), `runs/experiments/cosmetic_gaps/` (the hardened runner's verified-helpers pattern).

## Done when
1. A tracked data dir (`runs/experiments/data/run-exp-ai-turn/`) holds one SAV per watched turn, its sha256 in
   `SAVES.sha256`, binaries archived per batch to the release `run-exp-ai-turn` and cited by bare filename.
2. `findings/2026-10-07-ai-turn-corroboration.md` answers each attempted check with its tag and citations, and
   names the checks not attempted or not observed, with why.
3. The player (or the research intake) receives the draft; the research pending-requests entry is the research
   session's to remove.
