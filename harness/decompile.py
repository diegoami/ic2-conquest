"""Where the Ghidra decompile of the game lives, and which exact files findings cite.

Findings cite LINE NUMBERS of `all_app_functions.txt`, so the file is pinned by SHA-256 (`PINS`); a script that cites
line numbers calls `check()` and stops when the file is a different one. The folder is outside git on purpose
(decompiled game code, never committed): `$IC2_DECOMPILE`, else `~/ic2-decompile` (its own folder since 2026-11-04: the
old place, `~/ic2-work/decompile`, shared a parent with worktrees and game-folder copies that get cleaned up, and was lost
that way), else the legacy `$IC2_WORK/decompile`. Copies: Windows `%LOCALAPPDATA%/ReTools` and Drive
`gdrive:IC2/decompilation/` (docs/environment.md, "Decompile"). Old overrides still work: `IC2_RETOOLS` (a folder), `IC2_DUMP` (the dump file),
`IC2_SYMBOLS` (the symbols file). Standard library only, so any script can import it after putting the repo root on `sys.path`.
Pins recorded 2026-10-10 (copied from the lost Windows-side ReTools folder, hashes identical)."""
import hashlib
import os
import sys
from pathlib import Path

WORK = Path(os.environ.get("IC2_WORK", Path.home() / "ic2-work"))
HOME_DIR = Path.home() / "ic2-decompile"


def _find_dir():
    # Experiment libs point IC2_WORK at a private game-folder copy, which has no decompile: fall back to the shared one.
    explicit = os.environ.get("IC2_DECOMPILE") or os.environ.get("IC2_RETOOLS")
    if explicit:
        return Path(explicit)
    if HOME_DIR.is_dir():
        return HOME_DIR
    return WORK / "decompile" if (WORK / "decompile").is_dir() else HOME_DIR


DIR = _find_dir()

# The source of truth is Google Drive (owner 2026-11-04: "we can never assume that it will be there because we work on
# other computers and on the cloud ... if it is not there, get it from google drive through rclone"). The local folder is
# only a cache; fetch() fills it when a file is missing.
DRIVE = os.environ.get("IC2_DECOMPILE_DRIVE", "gdrive:IC2/decompilation")
WSL_RCLONE_CONF = Path("/mnt/c/Users/diego/AppData/Roaming/rclone/rclone.conf")


def rclone_config():
    """$RCLONE_CONFIG, else the Windows-side config when running in this WSL, else None (rclone's own default)."""
    c = os.environ.get("RCLONE_CONFIG")
    if c:
        return c
    return str(WSL_RCLONE_CONF) if WSL_RCLONE_CONF.exists() else None


def fetch(log=lambda m: print(m, file=sys.stderr)):
    """Copy the decompile from Drive into DIR (top-level text files and scripts/, scratch/; not the Ghidra project).
    Returns True when rclone succeeded. Never prints the config's contents, only passes its path."""
    import shutil
    import subprocess
    if not shutil.which("rclone"):
        log("decompile: rclone is not installed; install it and configure the 'gdrive:' remote, or set IC2_DECOMPILE")
        return False
    DIR.mkdir(parents=True, exist_ok=True)
    cmd = ["rclone"] + (["--config", rclone_config()] if rclone_config() else []) + [
        "copy", DRIVE, str(DIR), "--include", "/*.txt", "--include", "/*.tsv", "--include", "/*.json",
        "--include", "/scripts/**", "--include", "/scratch/**"]
    log("decompile: %s missing locally, fetching from %s" % (DIR, DRIVE))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        log("decompile: rclone failed (%d): %s" % (r.returncode, r.stderr.strip()[-500:]))
        return False
    return True


def ensure(name="all_app_functions.txt"):
    """Make sure `name` is in DIR, fetching the folder from Drive once if it is not."""
    if not (DIR / name).exists():
        fetch()
    return (DIR / name).exists()

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
    if not p.exists() and name not in MISSING:
        ensure(name)
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
        if not os.path.exists(p) and os.path.dirname(p) == str(DIR):
            ensure(name)
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
