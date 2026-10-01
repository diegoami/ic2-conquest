# Running ic2-conquest in WSL2 (Ubuntu 24.04)

How to bring the harness up on a Windows machine with WSL2, and the two
gotchas that make the plain `setup/setup.sh` run fail there. Written after a
working bootstrap on 2026-10-01: the seeded build matches `tests/results.md`
(`354d8265…532f`), the game runs headless, loads saves, and 3 of the 5 order
tests pass (the two failures are the toolbar-coordinate drift, below).

Everything here is machine-level. Nothing in this repository changes except
this file.

## 0. Prerequisites

- WSL2 with Ubuntu 24.04 (`wsl.exe -l -v` shows it `Running`, `Version 2`).
- A user with passwordless sudo, and network access to GitHub and the Ubuntu
  archives.
- ~1 GB free disk and about ten minutes.

## 1. Quick path (once the two fixes are in)

```bash
# as root, from the repository root
sudo IC2_SRC=$HOME/diegoami IC2_WORK=$HOME/ic2-work bash setup/setup.sh
# give the work tree back to your user (setup ran as root)
sudo chown -R $USER:$USER ~/ic2-work ~/diegoami
# create the Wine user profile (see §3)
DISPLAY=:99 WINEPREFIX=$HOME/ic2-work/prefix WINEARCH=win32 \
  /usr/lib/wine/wine wineboot -u
# a start save
mkdir -p ~/ic2-work/fixtures
cp saves/run0-start-AUTO0720-seed12345.SAV ~/ic2-work/fixtures/BASE.SAV
# prove it
python3 -m tests.test_orders
```

`IC2_SRC` must be overridden: `setup.sh` defaults it to `/home/user/diegoami`,
which does not exist on a normal WSL box. `IC2_WORK` defaults to
`$HOME/ic2-work`, which is fine.

## 2. Fix 1 — the broken `cli.github.com` apt repository

`setup.sh` runs `apt-get update`, and on this machine that aborts with

```
E: The repository 'https://cli.github.com/packages/deb stable Release'
   does not have a Release file.
```

because the GitHub CLI apt source is stale (404). It blocks the whole install.
Disable it for the setup run:

```bash
sudo mv /etc/apt/sources.list.d/github-cli.list \
        /etc/apt/sources.list.d/github-cli.list.disabled
```

It was already broken, so nothing is lost. Fix the URL and move it back if you
use `gh` from apt; `gh` itself is unaffected.

## 3. Fix 2 — the Wine prefix has no user profile

`setup.sh` builds the Wine prefix as **root** (`wineboot -i`), so
`C:\users\<youruser>` ends up holding only `AppData` — no `Desktop`,
`Documents`, etc. When the game later runs as your user and opens the
**File → Open** dialog, Wine cannot resolve a shell folder and logs

```
err:commdlg:IShellBrowserImpl_BrowseObject could not browse to folder
```

The dialog then shows an empty folder list, typing a name and pressing Open
does nothing, and every load times out:

```
DriverError: timeout waiting for game window after load
```

Create the profile as the user that will run the game:

```bash
DISPLAY=:99 WINEPREFIX=$HOME/ic2-work/prefix WINEARCH=win32 \
  /usr/lib/wine/wine wineboot -u
```

`wineboot -u` may not return on its own (it waits on `wineserver`); the profile
is created within a few seconds, so it is safe to interrupt it once
`C:\users\<user>\Desktop` exists. Verify:

```bash
ls ~/ic2-work/prefix/drive_c/users/$USER
# Desktop Documents Downloads ... should be present
```

After this, loads work and `move`, `end_turn` and `attack` pass.

## 4. Toolbar coordinates drift under this Wine

The toolbar buttons are wider in this Wine build than the positions recorded
in `coverage.md` / `harness/driver.py`, so the pitch accumulates and the
right-hand buttons land one slot over:

| Button | `coverage.md` x | actual x range (hover scan) | actual centre |
|---|---|---|---|
| Open | 12 | 6–24 | 15 |
| Save | 35 | 27–48 | 38 |
| End turn | 57 | 51–78 | 65 |
| News | 84 | 81–102 | 92 |
| International relations | 107 | 105–126 | 116 |
| Taxation | 129 | 129–150 | 140 |
| Balance sheet | 151 | 153–174 | 164 |
| Recruit unit | 174 | 177–198 | 188 |
| Build fleet | 196 | 201–228 | 214 |

Symptom: `python3 -m tests.test_orders` fails `recruit` and
`scripted_turn_repeats` with `timeout waiting for Army recruits dialog`,
because `TOOLBAR["recruit"] = 174` now hits **Balance sheet**.

**How to derive it at runtime.** Each toolbar button's tooltip is a named X
window, so the driver can find the buttons without hardcoding anything:

```bash
# hover across the toolbar; the tooltip window name is the button's label
for x in $(seq 6 3 240); do
  xdotool mousemove --sync $x 58; sleep 0.75
  for w in $(xdotool search --name "."); do xdotool getwindowname "$w"; done \
    | grep -vE 'Area map|Unit map|Information|Battlefield|Default IME|Imperial Conquest 2.*' \
    | grep -v '^$' | head -1 | sed "s/^/$x : /"
  xdotool mousemove --sync 600 400; sleep 0.25   # reset the tooltip
done
```

Tooltip label → driver tool name: `Open saved game`→open, `Save game
position`→save, `End player's turn`→end_turn, `News`→news, `International
relations`→relations, `Taxation`→taxation, `Balance sheet`→balance, `Recruit
unit`→recruit, `Build fleet`→build_fleet. Past `Build fleet` come the nation
icons (`Rome`, …) and `All`.

The intended fix is to calibrate once when the game starts (after a load) and
cache the map, falling back to the `coverage.md` values if the scan finds
nothing. That keeps the harness working on both renderings instead of moving
the hardcoded numbers from one to the other.

## 5. Environment variables and paths

| Name | Value used | Notes |
|---|---|---|
| `IC2_SRC` | `/home/<user>/diegoami` | where the pinned research + fixtures clones live |
| `IC2_WORK` | `/home/<user>/ic2-work` | Wine prefix, build, tests, fixtures, shots (outside git) |
| `WINEPREFIX` | `$IC2_WORK/prefix` | 32-bit prefix (`WINEARCH=win32`) |
| `DISPLAY` | `:99` | the Xvfb screen the driver starts |
| game folder | `$WINEPREFIX/drive_c/IC2` | exe, DAT, HLP, CNT, WAVS |
| base save | `$IC2_WORK/fixtures/BASE.SAV` | from `saves/run0-start-AUTO0720-seed12345.SAV` |
| Wine binary | `/usr/lib/wine/wine` | not the `/usr/bin/wine` wrapper |

Built executables land in `$IC2_WORK/build` and the game folder; the one the
driver uses is `Imperial Conquest 2 fast rollingsave seed.exe`, SHA-256
`354d8265cba1dac2a80a0a96ce76367a368e37a4e79c30eb4f0bb587b35c532f`.

## 6. Troubleshooting

- **`timeout waiting for game window after load`** — the Wine user profile is
  missing; run `wineboot -u` as your user (§3).
- **`apt-get update` fails on `cli.github.com`** — disable the repo (§2).
- **`pkill -f "Imperial Conquest"` kills your own shell** — the pattern matches
  the `pkill` command line itself. Use `pkill -f "[I]mperial Conquest"`.
- **No window appears / black screenshot** — Xvfb must be started with `setsid`
  (a plain background process is reaped between commands), and run it as the
  same user as Wine. A root-run game cannot see the user's `:99` Xvfb.
- **A load hangs after clicking Open** — dismiss the "… wants to trade with
  Rome." offer box (OK at about `640,547`) before clicking any toolbar button;
  it is modal and swallows the next click.
- **`recruit` fails** — the toolbar drift (§4).

## 7. Restart and teardown

```bash
export WINEPREFIX=$HOME/ic2-work/prefix
/usr/lib/wine/wineserver -k          # stop Wine
pkill -x Xvfb                        # stop the virtual display
python3 -m tests.test_orders         # starts both again as needed
```

Rebuild the executables after a pull of `imp_conquest_fixtures`:

```bash
cd $IC2_SRC/imp_conquest_fixtures
python3 patch_exe.py
python3 /path/to/ic2-conquest/patches/seed_patch.py "$PWD"
```
