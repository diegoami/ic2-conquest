#!/usr/bin/env python3
"""Offline test of the exclusive-creation helpers of g1_recover_g5.py (review round 4, R2): a save or log destination that already exists is
never replaced (a versioned name is allocated) and the earlier bytes survive; a race between an exists() check and the write cannot overwrite.
Temp dirs only. Run: python3 -m tests.test_g1_recover_g5"""
import importlib.util
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("g1_recover_g5", ROOT / "runs/experiments/data/run-exp-g1-original-checks/g1_recover_g5.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp); G = t / "G"; ART = t / "art"; D = t / "data"; G.mkdir(); D.mkdir()
        (G / "AUTO0720.SAV").write_bytes(b"save-1")
        # an earlier recovered save and an earlier log with the same names already exist
        ART.mkdir(); (ART / "G5_20261012-065502_recovered_AUTO0720.SAV").write_bytes(b"earlier-save")
        (D / "recovered-g5-S.jsonl").write_text("earlier-log\n"); (D / "SAVES.sha256").write_text("old-hash  x\n")
        rec, dst, log = m.recover(G, ART, D, "S")
        assert (ART / "G5_20261012-065502_recovered_AUTO0720.SAV").read_bytes() == b"earlier-save", "earlier save replaced"
        assert dst.name.endswith(".v2.SAV") and dst.read_bytes() == b"save-1", dst
        assert (D / "recovered-g5-S.jsonl").read_text() == "earlier-log\n", "earlier log replaced"
        assert log.name == "recovered-g5-S.v2.jsonl" and log.read_text().count("\n") == 2, log
        assert (D / "SAVES.sha256").read_text().startswith("old-hash  x\n") and dst.name in (D / "SAVES.sha256").read_text()
        # a third run: v3, the first two survive
        (G / "AUTO0720.SAV").write_bytes(b"save-2")
        rec, dst3, log3 = m.recover(G, ART, D, "S")
        assert dst3.name.endswith(".v3.SAV") and dst.read_bytes() == b"save-1" and log.exists() and log3.name == "recovered-g5-S.v3.jsonl"
        # race: a file appearing between a (stale) exists() check and the open is not replaced
        p = t / "race.bin"
        f, used = m.reserve(p); f.write(b"A"); f.close()
        f2, used2 = m.reserve(p); f2.write(b"B"); f2.close()
        assert p.read_bytes() == b"A" and used2.read_bytes() == b"B" and used2 != p
    print("test_g1_recover_g5: all checks passed")


if __name__ == "__main__":
    main()
