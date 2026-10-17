#!/usr/bin/env python3
"""Validate the three retained controls without executing the game; new outputs only."""
import argparse
import hashlib
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data/run-exp-resupply33"

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    canonical = json.loads((DATA / "summary-canonical-20261017.json").read_text())
    raw = json.loads((DATA / "ledger-initial-20261017.json").read_text())["records"]
    manifest = dict(line.split("  ", 1)[::-1] for line in (DATA / "SAVES.sha256").read_text().splitlines())
    assert len(manifest) == 9
    checked = []
    for expected, ledger in zip(canonical["records"], raw, strict=True):
        kind = expected["stem"].split("-")[0]
        phase = json.loads((DATA / f"phases-{kind}-byte-audit-20261017.json").read_text())
        assert phase["error"] is None
        runtime_path = DATA / expected["runtime"]
        assert hashlib.sha256(runtime_path.read_bytes()).hexdigest() == phase["runtime_sha256"]
        runtime = json.loads(runtime_path.read_text())
        assert runtime["seed"] == phase["supplied_seed"] == expected["runtime_seed"] == 4169717509
        logs = [json.loads(line) for f in DATA.glob("replay-*.jsonl") for line in f.read_text().splitlines()]
        for event, field in [("loaded", "fresh_loaded"), ("post", "fresh_post")]:
            entry, = [d for d in logs if d.get("event") == event and d.get("file") == expected[field]]
            assert entry["whole_save_identical"] is True
            assert manifest[entry["file"]] == entry["sha256"]
            if event == "post":
                assert manifest[entry["auto"]] == entry["auto_sha256"]
        comparison = phase["post_comparison"]
        for key in ["queues_match", "treasury_match", "mobilization_match", "all_city_bytes_match", "all_live_army_bytes_match", "all_live_fleet_bytes_match"]:
            assert comparison[key] is True, (kind, key)
        assert comparison["all_nation_bytes_match"] is False
        assert comparison["nation_byte_differences"] == [{"nation": 11, "offset": "0x482", "x86": 196, "wine": 192}]
        assert 708 - 708 % 16 == 704
        observed_phases = [{"phase": p["phase"], "before": p["before"]["treasuries"][0], "after": p["after"]["treasuries"][0]} for p in phase["phases"]]
        assert [p["phase"] for p in observed_phases] == ["diplomacy", "recruitment", "army", "fleet"]
        assert observed_phases == expected["phases"]
        writes = [{k: w[k] for k in ["ip", "nation", "before", "after", "debit", "frames"]} for w in phase["writes"]]
        assert writes == expected["treasury_writes"]
        assert ledger["stem"] == expected["stem"] and ledger["ledger"] == expected["ledger"]
        assert [w["debit"] for w in writes] == [r["cost"] for r in ledger["ledger"]]
        assert all(w["ip"] == "0x45070e" and w["nation"] == 0 and w["frames"] == ["recruitment", "budget_recruit"] for w in writes)
        assert ledger["total"] == sum(w["debit"] for w in writes) == ledger["observed_debit"]
        assert ledger["residual"] == expected["treasury_residual"] == 0
        entries = [e for e in phase["events"] if e.get("event") == "entry" and e.get("function") == "budget_recruit"]
        assert len(entries) == 1 and entries[0]["eax"] == expected["budget_target"]
        assert phase["initial"]["mobilization"] == 24
        assert phase["final"]["mobilization"] == (47 if kind == "fleet" else 43)
        checked.append({"case": kind, "debit": ledger["total"], "residual": 0, "phase": "recruitment", "whole_Wine_loaded_post_identity": True, "x86_nation_UI_exception_retained": comparison["nation_byte_differences"]})
    assert len(checked) == canonical["cases"] == 3
    with args.output.open("x") as out:
        json.dump({"provenance": "Offline assertions over retained raw logs, phase controls and canonical summary; no new game execution.", "cases": checked, "manifest_saves": len(manifest)}, out, indent=2)
        out.write("\n")
    print(json.dumps({"cases_validated": len(checked), "manifest_saves": len(manifest)}))

if __name__ == "__main__":
    main()
