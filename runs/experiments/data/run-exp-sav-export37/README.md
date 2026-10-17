# Research37 immutable evidence index

Canonical task: research37/latestcomment6239985304, pinned in `issue37-initial.json`; conquest99. Finding: [SAV export live regions and rejection policy](../../../../findings/2026-10-17-sav-export-live-regions-and-safe-rejection-policy.md).

Authoritative packet:

- `nation-matrix-v2.csv`: 33 contiguous regions / all1172bytes, 31bytes UNKNOWN/reject changed-state inheritance. `nation-matrix-initial.csv` is a retained initial draft with unresolved/incorrect citation placeholders; do not cite it as final evidence. Generator corrections do not change the raw source or measurements.
- `source-inventory-addresses-v2.json`:247fullfunctions/2040references; includes literal absolute-address reads that the initial named-only inventory omitted. `source-focused-v1.txt`:27functions/1111numbered lines, exact original line text. Both inventories are targeted reference searches, not exhaustive alias analysis or proof that an unreferenced region is unused.
- `original-news_log_decomp.txt`: original supplemental NewGame448AA4 and DATloader4481A0; `original-save_load_impl.txt`:load4487C4/save4484D0; `original-save_load.txt`:matching UI entry points. `input-provenance-initial.json` hashes source/EXE/DAT and reused reports. No binary source copied into this packet.
- `public-scalar-audit-initial.json`:14already-public tracked saves,224nation records. Native owner JSON/private templates were not accessed. Exact public filenames/hashes included; all owned prefixes and alphabetical ordering match; all unused citylist entries-1; 31unknown bytes sampledzero, not static proof.
- `dat-profile-initial.json`:16DATprofiles,224historicalbaseline matches. Applicability to a native campaign remains a separate required proof.
- `x86-controls-v2.json`:10unmodified-original-x86 controls; constructor residue, compaction/index repair, tombstones, city-list transfer, text copy, coordinate finder ordering and map bands. Synthetic0xA5memory is a control, never a prototype. `x86-controls-initial.json` preserves the earlier8controls. No SAVs or live game outputs generated.

Reproduction from the task recovery layout `/home/diego/projects/ic2-work/sav-export37/conquest`: each script under `runs/experiments/sav_export37/` requires a new `--output runs/experiments/data/run-exp-sav-export37/<unique-name>`. It opens output exclusively. Never delete/overwrite a measurement or save. EXE/DAT resolve from sibling `resupply31/wine-aboard/prefix/drive_c/IC2`; source from `/home/diego/ic2-work/decompile/all_app_functions.txt`; public inputs from tracked `saves/`. `controls.py` needs Unicorn; hashes/version are pinned. Do not run these commands on owner-private inputs or write output saves.

No new binary artifacts require upload. The no-owner-save/no-original-byte-upload boundary of research37 is respected. Native Windows three-output validation is unperformed and remains conditional on candidates/private inputs/owner runtime coordination. Wine is not a substitute. Matrix coverage, public parsing and emulation do not establish compatibility or RNG equivalence.
