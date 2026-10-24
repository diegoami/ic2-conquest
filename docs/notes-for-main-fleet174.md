# Main handoff: stored fleet destinations #1405

Research PR70 is merged at `ebe8acb530f9b0250855aded20e1988f94d4c873`.
Use the [canonical fleet report](https://github.com/diegoami/imperial-conquest-2-research/blob/ebe8acb530f9b0250855aded20e1988f94d4c873/docs/reports/2026-10-24-strategic-fleet-controls174.md).
Conquest source finding: `findings/2026-10-24-strategic-fleet-controls174.md`;
evidence: `runs/experiments/data/run-exp-strategic-fleet/`.

Fourteen synthetic original-instruction/native controls isolate missing native
stored-route state. Absent/A/B SAV containers differ only at fleet0route+4/+6;
original destinations differ while native state hashes/proposals agree. Current
export mapping explicitly canonicalizes absent native route state. Treat this
as faithful feature support, not an undisclosed violation of existing policy.
Research reproduced retained controls offline without a new game/production edit.

Scope #1405's native state/save/load/export and actual accepted behavior through
the normal Main task/PR workflow. Keep deliberately designed sailing policy and
proposal membership separate from accepted full-loop decisions. Original prepass
and port selection run before routing; route absence tests signed X. The
combined stored-route/zero-moves case is UNTESTED and belongs in the follow-up,
along with route lifetime, movement/cargo/port/contact and appropriate CI checks.
Do not infer global RNG or Windows acceptance from this report. Main is reached
through the owner and existing issue links; no direct Main session message.
