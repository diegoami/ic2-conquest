# Broad conversion matrix — issue #153

2026-10-23: owner explicitly requested a broad follow-up to #151, with starts
from several nations and feature-by-feature conversion tests in both directions.
Approval recorded in https://github.com/diegoami/ic2-conquest/issues/153 .
Branch `experiment/sav-conversion-broad`, base `4ca3afa04c3eb8454c63ed6a4984f5564e8e0496`.
No additional findings on origin/main at start. Preserve all existing owner files.

Plan: all16 human-nation starts (two startup seeds across the sweep); progressed
states for four contrasting nations; targeted state/action cases for strategic
army/naval/economy/recruitment/diplomacy/city/combat-aftereffect features; hotseat,
pending offer, elimination, text and numerical limits; actual unsupported-state
refusals/migration tests where valid. Report distinct coverage levels: preserved
state, original action, remake action after return, refused, blocked, untested.
This is conversion testing, not resumption of the paused battle research queue.

Reuse pinned, read-only remake assemblies and build only task-owned adapters
into ignored artifact folders. Use isolated original Wine prefix/display. Check
findings for each mechanic and driver workarounds before creating experiments.
No source change in another repo; defects get evidence and an upstream issue.

Never delete/overwrite a save or measurement, including failed attempts. Every
save, script and attempt uses unique names. Text measurements go directly to
`runs/experiments/data/run-exp-sav-conversion-broad153/`; binary/native JSON
artifacts stay under `artifacts/run-exp-sav-conversion-broad153/` and Drive, with
SHA256 manifests. Commit/push each batch and at least every30min. Record complete
outcomes before adapting. No subagents/reviewers launched. Native Windows and
the owner's twelve-save manifest remain separate owner gates.

## First batch

Current remake main ae614899d63ac721ee46d1e3213191fe1f43a676 differs from read-only local a510c33 by PR1353 quality4 fix (2production files +2tests). Verified GitHub blob identities of2production files, built current CLI via compile-item substitutions without changing or cloning another repository. Build output/assembly pins retained in artifact folder and source-pin receipt. All16human starts (alternating seeds7/11) and4progressed states (Rome6/Carthage12/Ptolemaic18/Macedonia24) export, pass independent policy, import/reload/resume, and execute their selected prediction command. Original all16sweep currently running serially in private Wine/Xvfb: first4complete, movement verified, freshreopen byte-equal. Feature adapter initially lacked the tests-only ValueList.Replace extension; corrected task-owned helper, no save trial repeated. Port geometry checked against selected existing fixture; Antium at102,46, fleet101,46, adjacent sea100,46. Feature captions will be read via a task-owned LB_GETTEXT helper, not assumed row numbers.
