"""Where the Ghidra decompile of the game lives, and which exact files findings cite.

Findings cite LINE NUMBERS of `all_app_functions.txt`, so the file is pinned by SHA-256 (`PINS`); a script that cites
line numbers calls `check()` and stops when the file is a different one. The folder is outside git on purpose
(decompiled game code, never committed): `$IC2_DECOMPILE`, else `$IC2_WORK/decompile` (`IC2_WORK` defaults to
`~/ic2-work`, as in `harness/driver.py`). Old overrides still work: `IC2_RETOOLS` (a folder), `IC2_DUMP` (the dump file),
`IC2_SYMBOLS` (the symbols file). Standard library only, so any script can import it after putting the repo root on `sys.path`.
Pins recorded 2026-10-10 (copied from the lost Windows-side ReTools folder, hashes identical)."""
import hashlib
import os
import sys
from pathlib import Path

WORK = Path(os.environ.get("IC2_WORK", Path.home() / "ic2-work"))
DIR = Path(os.environ.get("IC2_DECOMPILE") or os.environ.get("IC2_RETOOLS") or WORK / "decompile")

PINS = {
    "all_app_functions.txt": "2018c205a4e4ea4a4079f2d166623fb571062832d76e19b72e11d1f0edac87d8",
    "delphi_symbols.tsv": "c4dbf9bb6a1b4f2907bb9f9ef904d60150997a4f86d08e0dd3195ba87365f58f",
    "news_log_decomp.txt": "274d60b2af6ed30dbc11ce59a189d86ce70b15b6f94112efbe2cfba6309622dd",
}

# Files that were in the old ReTools folder but are not in the copy (never invent them).
MISSING = {
    "scratch/datload.txt": "listing of FUN_004481a0 (the DAT loader); cited by runs/experiments/info_window; lost in the computer move",
}


def path(name):
    """Path of a file in the decompile folder (`name` may be 'sub/file'). Fails with a clear message if it is missing."""
    p = DIR / name
    if not p.exists():
        why = MISSING.get(name)
        sys.exit("decompile file missing: %s%s\n(folder %s; set IC2_DECOMPILE to move it)"
                 % (p, " (known lost: " + why + ")" if why else "", DIR))
    return p


DUMP = os.environ.get("IC2_DUMP") or str(DIR / "all_app_functions.txt")
SYMBOLS = os.environ.get("IC2_SYMBOLS") or str(DIR / "delphi_symbols.tsv")
NEWS_LOG = str(DIR / "news_log_decomp.txt")

_checked = {}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def check(*files):
    """Stop (SystemExit) if a pinned file is not the pinned one. No arguments: the dump. Arguments: paths or pinned names."""
    for f in files or (DUMP,):
        p = str(f if os.sep in str(f) else DIR / f)
        name = os.path.basename(p)
        if p in _checked:
            continue
        if not os.path.exists(p):
            sys.exit("decompile file missing: %s\n(folder %s; set IC2_DECOMPILE to move it)" % (p, DIR))
        want = PINS.get(name)
        if want is None:
            sys.exit("%s is not a pinned decompile file (pinned: %s)" % (name, ", ".join(PINS)))
        got = sha256(p)
        if got != want:
            sys.exit("%s is not the pinned decompile file: SHA-256 %s, expected %s.\n"
                     "Findings cite its line numbers, which would not match. See docs/environment.md (Decompile)." % (p, got, want))
        _checked[p] = True
