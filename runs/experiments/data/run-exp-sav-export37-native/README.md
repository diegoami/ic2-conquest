# Original Windows tax-candidate evidence

Current consolidated result: [finding](../../../../findings/2026-10-18-sav-export-original-windows-tax-candidates.md). Three observed candidate sequences completed; internal callback instruction trace UNVERIFIED, twelve native JSON conversions/general exporter readiness not established.

Read [native-packet-validation-v2.json](native-packet-validation-v2.json) for all immutable input hashes, private stage SAV hashes and private PNG hashes. No SAV/PNG/private commander captions are committed. Private directory: `C:\Users\diego\Documents\ic2-tax-native\20261018T085043Z`. PNG/SAV bytes stay there; no release upload.

- `runtime-prelaunch-v1.json`, `launch-v1.json`: actual runtime/owner coordination; early status is chronological.
- `control1-comparison-v1.json`: owner's manual original tax10→0, complete source/control/candidate span comparisons; area-map window movement explicitly differs from candidate.
- `control2-comparison-v1.json`, `control3-comparison-v1.json`: autonomous actual original trackbar/OK tax9→40 and20→30; after saves exactly equal candidates.
- `case1-completion-v1.json`, `case2-completion-v1.json`, `case3-completion-v1.json`: per-case final native observations. Earlier partial statuses remain immutable, superseded by later cases and consolidated finding.
- Per-action JSON: actual process/HWND/control metadata, redacted dynamic caption, read-only scalar snapshots, private output receipts. Case3 event-pending is an intentionally retained supply-warning checkpoint, followed by one actual confirmation and completion. Python continuation failure is retained and recovered; no second order/turn.

Scripts in [sav_export37_native](../../sav_export37_native): `windows_bridge.py` owns guarded native UI/RPM/capture operations; `case1_actions.py` supplies exclusive Save As; `remaining_cases.py` orchestrates controls/candidates2/3 and pauses on unexpected events; `case3_resume.py` records the recovered continuation; `compare_control1.py` performs whole-file/span comparison; `verify_native_packet.py` checks existing private evidence read only.

To verify without starting a game, from repository root run:

```sh
python3 runs/experiments/sav_export37_native/verify_native_packet.py --output runs/experiments/data/run-exp-sav-export37-native/native-packet-validation-NEW.json
```

Output must not exist; private paths/Windows tools must be accessible. Do not rerun native orchestration on existing names: it intentionally refuses collisions. A reviewer without private inputs can review committed code/scalars/hash consistency, but cannot independently reproduce private-byte or visual observations. No test result should be represented as that missing access.
