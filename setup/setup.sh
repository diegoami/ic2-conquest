#!/usr/bin/env bash
# One-shot environment for ic2-conquest on Ubuntu 24.04 (run as root).
#   1. apt: wine (32-bit), Xvfb, xdotool, imagemagick, ffmpeg, tesseract (OCR of
#      message boxes), mingw (to build the win_controls dialog-control helper)
#   2. clone the pinned research + fixtures repos under $IC2_SRC (default /home/user/diegoami)
#   3. build "fast rollingsave seed" (patches/seed_patch.py on top of patch_exe.py)
#   4. a win32 Wine prefix under $IC2_WORK with the game in C:\IC2
# Nothing it fetches or builds lands in the git tree.
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
IC2_SRC=${IC2_SRC:-/home/user/diegoami}
export IC2_WORK=${IC2_WORK:-$HOME/ic2-work}
pin(){ awk -v r="$1" '$1==r{print $2}' "$HERE/setup/pins.txt"; }

# 1. packages
if [ ! -x /usr/lib/wine/wine ] || ! command -v xdotool >/dev/null || ! command -v ffmpeg >/dev/null || ! command -v tesseract >/dev/null || ! command -v i686-w64-mingw32-gcc >/dev/null; then
  dpkg --add-architecture i386
  apt-get update -q
  pkgs="wine64 wine32:i386 xvfb xdotool imagemagick ffmpeg tesseract-ocr tesseract-ocr-eng gcc-mingw-w64-i686"
  # a PPA's libgd3 blocks the i386 one on some images: pin both to Ubuntu's
  if apt-cache policy libgd3 | grep -q 'ubuntu24.04.*sury'; then
    v=$(apt-cache policy libgd3 | awk '/archive.ubuntu.com/{print prev} {prev=$1}' | head -1)
    [ -n "$v" ] && pkgs="$pkgs libgd3=$v libgd3:i386=$v"
  fi
  DEBIAN_FRONTEND=noninteractive apt-get install -y -q --allow-downgrades --no-install-recommends $pkgs
fi
pip install -q capstone pefile 2>/dev/null || true

# 2. pinned sources (read only)
for r in diegoami/imperial-conquest-2-research diegoami/imp_conquest_fixtures; do
  d="$IC2_SRC/${r#*/}"; c=$(pin "$r")
  [ -d "$d/.git" ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q "https://github.com/$r" "$d"
  if [ "$(git -C "$d" rev-parse HEAD)" != "$c" ]; then
    git -C "$d" fetch -q --depth 50 origin "$c" 2>/dev/null || git -C "$d" fetch -q origin
    git -C "$d" -c advice.detachedHead=false checkout -q "$c"
  fi
  echo "pinned $r @ $(git -C "$d" rev-parse --short HEAD)"
done
FX="$IC2_SRC/imp_conquest_fixtures"
echo "$(sha256sum "$FX/Imperial Conquest 2.exe" | cut -c1-64)" | grep -q "$(awk '$1=="original"{print $2}' "$HERE/setup/pins.txt")" \
  || { echo "original exe hash mismatch"; exit 1; }

# 3. builds (patch_exe.py's own outputs + the seeded one), in a scratch copy
B="$IC2_WORK/build"; mkdir -p "$B"
cp "$FX/patch_exe.py" "$FX/Imperial Conquest 2.exe" "$B/"
(cd "$B" && python3 patch_exe.py >/dev/null && python3 "$HERE/patches/seed_patch.py" "$B")
sha256sum "$B"/*.exe | sed "s|$B/||"
i686-w64-mingw32-gcc -O2 -o "$IC2_WORK/win_controls.exe" "$HERE/harness/win_controls.c"
i686-w64-mingw32-gcc -O2 -o "$IC2_WORK/win_slider.exe" "$HERE/harness/win_slider.c"

# 4. Wine prefix + game folder C:\IC2
export WINEPREFIX="$IC2_WORK/prefix" WINEARCH=win32 WINEDEBUG=-all
if [ ! -f "$WINEPREFIX/system.reg" ]; then
  rm -rf "$WINEPREFIX"; mkdir -p "$(dirname "$WINEPREFIX")"
  (. "$HERE/harness/env.sh"; /usr/lib/wine/wine wineboot -i >/dev/null 2>&1; /usr/lib/wine/wineserver -w)
fi
G="$WINEPREFIX/drive_c/IC2"; mkdir -p "$G"
cp "$FX/Imperial Conquest 2.dat" "$FX/Imperial Conquest 2.hlp" "$FX/Imperial Conquest 2.cnt" "$G/"
cp -r "$FX/WAVS" "$G/"
cp "$B"/*.exe "$G/"
echo "game folder: $G"
