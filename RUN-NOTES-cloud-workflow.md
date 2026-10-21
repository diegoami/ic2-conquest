# Cloud migration and session-led workflow

Owner scope: prepare private research inputs for cloud continuation; remove
compulsory review, worktree and model-family gates. Use the existing Windows
IC2 `gdrive:` remote. Explicit approval received for the exact 2.3 MB private
bundle and `gdrive:IC2/conquest/cloud-migration-20261021` destination.

Plan: align entry points and active workflow docs; lift reviewer CLI family and
provider gates; validate offline; publish the policy/handoff; upload and verify
private inputs separately. Work in supplied checkout, preserve unrelated files.

Implementation: shared policy and Codex mapping updated; optional review routes
retain their internal read-only worktrees. Same/unknown families and DeepSeek
are no longer refused. CLI still accepts one explicit model per invocation;
explicit caller exclusions remain available. Historical review receipts remain.

Validation: reviewer self-test 83/83; fake-provider reviewer suite 36/36;
environment suite 16 passed; archive pycache checks passed; whitespace clean.
Initial test adaptation exposed missing model IDs in the fake provider listing;
fixture listing updated and the full reviewer suite passed. No game or reviewer
provider launched. Bundle 128/128 per-file SHA256 checks passed, originals kept.

Continuing work and restore instructions: docs/cloud-continuation.md. GitHub
PR/issue state is authoritative. Atlas PR108 remains a draft at this checkpoint;
review is now optional, not a mandatory gate. Research PR48 merged and no review
slot is occupied. Last source findings delivered: 7fe20bed; atlas not yet on main.

END: Cloud target/secret injection not yet selected. Original writer folder and
manifests remain missing; retained-copy provenance is documented. Private bundle
upload is being verified; record the final receipt in docs/cloud-continuation.md.
No unrelated backups, proprietary inputs or tokens are staged with this change.
