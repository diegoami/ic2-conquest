# Main handoff: strategic fidelity pilot #171

Conquest finding `findings/2026-10-24-strategic-fidelity-pilot171.md` is intaken.
Research PR69 merged at `cdb355fde49b7047d6164de26b2922054fb120ee`.
Use the [canonical report](https://github.com/diegoami/imperial-conquest-2-research/blob/cdb355fde49b7047d6164de26b2922054fb120ee/docs/reports/2026-10-24-strategic-fidelity-pilot171.md).
Research independently reproduced retained controls without a new game run or
production change. Fleet174's initial packet was promoted by Research PR70,
and its accepted-movement packet by PR71/72. Navigation187 is promoted by PR72
at `c863a97cb1fc66206e23521c7bdd024548ba41dd`, with its caller limit retained;
T212 stays blocked. The newer conquest PR190 continuation remains unpromoted.

Pinned remake55d96876: eleven distinct generated inputs,112original army-tree
states,290524input checks. Own scorers give58/112matching branch kinds; actual
original scores fed to production DecideFromScores restore112/112. Every
different original winning city(51) and army(55) is excluded by native direct-
walk eligibility. This extends #1388's selector/routing boundary; it does not
justify making every target reachable or omitting intermediate routing.

New resupply controls independently prove the original destination selector
uses a troops/1000 threshold,
requires own stock above that quotient, and favors a capital via lower adjusted
distance. Native raw selector uses /100, stock below the quotient and a capital
penalty. Research PR69 corrected canonical strategic-ai-turn §3.3 and the spec;
automatic supply-transfer capacity remains /100. Six same-input controls include
swapped capitals and stock29/30/297/298, with positive matching controls.

Scope selector/routing and resupply corrections through
normal Main issues/PRs, keeping intentional reachable-resupply policy separate.
Bring meaningful controls into the suite; rerun existing movement/AI/solution
checks. Do not infer that all112rows prove full greedy-command-loop equivalence,
or that different whole-turn economic/diplomatic outcomes prove those rules bad.
Fleet/homeland/economy/diplomacy exact decision/RNG comparison remains future
research. No other repository was edited, and native Windows acceptance remains
incomplete. No direct Main session message was sent.
