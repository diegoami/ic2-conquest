# Cloud continuation and private inputs

The owner requested cloud migration and a session-led workflow on 2026-10-21.
Read `CLAUDE.md` and `docs/agent-workflow.md`: worktrees, separate reviews and
model-family restrictions are optional or removed. Use the supplied checkout.
Battles and bots remain paused; migration does not authorize a new game run.

## Resume the SAV investigation

The whole-original-SAV investigation is [issue107](https://github.com/diegoami/ic2-conquest/issues/107).
Read [PR108](https://github.com/diegoami/ic2-conquest/pull/108), branch
`research/original-sav-semantic-atlas`, head
`97ba1d891f3487a6128dd6c68722f9104a425592` at migration preparation, its
`RUN-NOTES-sav-semantic-atlas.md` and
`findings/2026-10-21-original-sav-semantic-atlas.md`. Check live GitHub state:
the draft had no external review. Its old waiting-for-review-slot note predates
the new optional-review policy. The goal is one ledger identifying every field,
dependency and retained byte, distinguishing semantic understanding from byte
coverage, round-trip identity and native acceptance.

Conquest PR105 and PR106 merged. Source findings last delivered to research at
`7fe20bedba0b9cdbb012b1b348c96507f6a65768`; branch
`research/remaining-queue-status` at `d4fed37` retains relay receipts.
The owner permits messages to ic2-research. A local session bridge may not exist
in the cloud; never claim delivery unless it succeeds.

Research [PR48](https://github.com/diegoami/imperial-conquest-2-research/pull/48)
merged at `16f019397e65ba521bbcee7acea2a7d2c9bd7c93` after complete GLM approval.
Read that repo's `docs/progress/research37-intake.md`, `docs/pending-requests.md`
and `docs/reports/2026-10-18-sav-export-original-windows-tax-candidates.md`.
Its unchanged validator independently passed against the retained copy: 3 cases,
21 SAV + 38 PNG, 337 JSON records, zero game processes. Missing original writer
manifests, UNKNOWN31, callback validation and native JSON conversion (0/12)
remain unresolved; research #37 remains open at this checkpoint.

## Private bundle and authentication

Use the existing Windows IC2 rclone remote `gdrive:`. Its config is
`C:\Users\diego\AppData\Roaming\rclone\rclone.conf`, or WSL
`/mnt/c/Users/diego/AppData/Roaming/rclone/rclone.conf`. The WSL default config
has different remotes. Never print or commit configs/tokens. Configure Drive
credentials separately in the cloud's secret facility; OAuth tokens must match
their client. A file-free rclone remote can use these environment variables:

- `RCLONE_CONFIG_GDRIVE_TYPE=drive`
- `RCLONE_CONFIG_GDRIVE_TOKEN`: the full OAuth token JSON, set as a secret
- `RCLONE_CONFIG_GDRIVE_CLIENT_ID` and `RCLONE_CONFIG_GDRIVE_CLIENT_SECRET`:
  set these when the token was issued to a custom OAuth client

Set `IC2_DRIVE_REMOTE=gdrive:IC2/conquest/cloud-migration-20261021` for the
restore commands below. Do not paste token values into chat or shell history. The bundle contains no credentials or Wine prefix.

Destination: `gdrive:IC2/conquest/cloud-migration-20261021`.
Archive: `ic2-research-inputs-20261021.tar.gz`, 2,290,243 bytes.
SHA256: `2bea418bca6de330b2776c61581cf767d6b2829d4ac15dc03a728acdb693008e`.
The owner explicitly approved this payload and destination. Confirm the upload
receipt before relying on remote availability.

The archive holds 128 files (12,310,415 input bytes), a manifest and SHA256SUMS:
original EXE/DAT, top-level ReTools source extracts/symbols if present, 3 source
saves, the 63-file owner-retained native evidence copy, 16 crafted battle saves,
12 native JSON preflight saves and unique source-analysis receipts. Originals
were preserved. Keep the bundle private, outside Git and public releases.

Download outside the repository, verify and unpack:

```bash
export IC2_DRIVE_REMOTE=gdrive:IC2/conquest/cloud-migration-20261021
export IC2_INPUTS_DIR="$HOME/ic2-inputs"
mkdir -p "$IC2_INPUTS_DIR"
rclone copy "$IC2_DRIVE_REMOTE" "$IC2_INPUTS_DIR" --immutable
cd "$IC2_INPUTS_DIR"
sha256sum -c ic2-research-inputs-20261021.tar.gz.sha256
tar -xzf ic2-research-inputs-20261021.tar.gz
cd ic2-research-inputs-20261021
sha256sum -c SHA256SUMS
export IC2_DECOMPILE="$PWD/decompile"
```

Preserve filename case: retained C1B/C1T saves use lowercase `.sav`; Linux will
reject uppercase references. Preserve duplicate JSON names as provenance.
The original `Documents/ic2-tax-native/20261018T085043Z` folder remains access
denied; the bundle uses the readable owner-copied evidence. Original candidate
basenames and writer manifests remain missing. Temporary SHA-bound validation
aliases are not original writer-delivery provenance.

## Cloud setup limits

GitHub carries the source and pushed task branches. Clone normally and check
current PR/issue state. Run the offline checks in `docs/agent-workflow.md`;
source/SAV work does not require Wine. The specific cloud environment and its
secret injection mechanism still need to be selected by the owner.

If choosing the legacy OpenCode reviewer CLI, use a compatible 1.x executable
and fresh private data directory. This machine's default Linux CLI was 2.0.28
and incompatible; successful runs explicitly used 1.18.32 via `OPENCODE_EXE`.
The cloud harness can review without it. Never bundle `auth.json`.
