# Research37 bounded closure evidence

Finding: [unknown access and record lineage boundaries](../../../../findings/2026-10-18-sav-export-unknown-access-and-record-lineage-boundaries.md). Base/last reported-delivered MAIN baseline: 8904c162f1012e9ab1adfa7df32b897141f42f31. This packet leaves research37/conquest99 open.

Authoritative measurements:

- `source-alias-leads-v2.json`: exact sixteen-nation lexical scope; 156 functions/680 references, no additional functions versus prior inventory, no unknown starts or selected relative constants. No universal alias proof.
- `x86-path-controls-v2.json`: six passing original-x86 controls, four bounded unknown-byte read/write negatives with 496 nonzero patterned canaries, slot deletion lineage, equal-visible-text/different-tail rename, plus deliberate indirect read/write hook positive control. Original helpers/unpatched instructions, synthetic memory only. No game/save output.
- `source-controls-and-history-v1.txt`: eight full functions, exact pinned source line text. Extraction initially expected nine; full dump omits loader004487C4 and assertion failed after retaining eight. Those eight are valid exact extracts; loader evidence is prior `run-exp-sav-export37/original-save_load_impl.txt`. DAT loader is prior `original-news_log_decomp.txt`. No loader in this extract claimed.
- `validation-v1.json`: integrity checks, not a game/export test.

Retained non-authoritative/earlier outputs: `source-alias-leads-v1.json` rejected oversized range includes224adjacent bytes and17spurious addedfunctions, not nation evidence; empty `source-added-functions-v1.txt` correctly reflects v2 having no additions; `x86-path-controls-v1.json` earlier five passing controls without instrumentation positive control. No measurements were overwritten/deleted.

Scripts in `runs/experiments/sav_export37_closure/` require a new unique `--output` path and use exclusive creation. Never rerun onto an existing output, delete/overwrite saves, or apply these probes to private inputs. Source `/home/diego/ic2-work/decompile/all_app_functions.txt`, EXE `/home/diego/projects/ic2-work/resupply31/wine-aboard/prefix/drive_c/IC2/Imperial Conquest 2 fast rollingsave seed.exe`, public fixture `saves/run0-start-AUTO0720-seed12345.SAV`; pins in measurements and prior `input-provenance-initial.json`. Unicorn2.1.4. No binary output/upload needed; no owner-private inputs accessed. Native Windows gate unperformed, availability unverified.
