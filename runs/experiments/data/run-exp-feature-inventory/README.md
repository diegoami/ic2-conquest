# run-exp-feature-inventory: data of the feature inventory

Task `docs/tasks/feature-inventory.md`; draft `findings/2026-10-05-player-facing-feature-inventory.md`. Scripts: `runs/experiments/feature_inventory/`.

| File | What |
|---|---|
| `forms.json`, `form_controls.tsv` | every `TPF0` form resource of the exe (29 forms, 908 controls), captions, hints, handlers, decoded `ShortCut` |
| `form_xrefs.tsv` | each form's VMT and the functions that reference it |
| `dump_string_literals.tsv`, `exe_strings.tsv`, `delphi_symbols.tsv` | string literals by function (whole-application Ghidra dump), exe `AnsiString` literals, symbol table copy |
| `help_contents_entries.tsv`, `help_topics.tsv`, `help_records_raw.tsv`, `help_decode_meta.txt`, `help_decode_check.txt` | the help file: the `.cnt` entries (parsed; the `.cnt` is a game file and not tracked), the decoded WinHelp topics, the raw decoded records, decoder metadata and check |
| `inventory_rows.psv` | the inventory (one row per feature), the source of the table in the finding |
| `coverage_map.cfg`, `news_templates.cfg` | the mapping rules from source entries to rows or exclusions |
| `coverage_entries*.tsv`, `coverage_report*.txt` | the recomputed coverage, versioned (`.v2`, `.v3` ...; the newest is current): one line per entry, and the totals (`python3 runs/experiments/feature_inventory/coverage_check.py --check`) |
| `coverage_selftest_output*.txt`, `same_screen.cfg`, `report_titles*.tsv`, `dump_string_literals.v2.tsv` | the checker's self-test output, the declared identical screenshots, the research-report titles for the rules sweep, and the dump literals including punctuation-only ones |
| `explore/b1.log`, `explore/b2.log` | text logs of EXPLORE batches 1 and 2 (Wine) |
| `SAVES.sha256`, `MANIFEST-batch1.txt`, `MANIFEST-batch2.txt` | SHA-256 of the screenshots and the archive; the files are in the release `run-exp-feature-inventory` |
