# Source me. Headless Wine + Xvfb session for the game.
#   IC2_WORK : scratch root (Wine prefix, screenshots); never inside the git tree
#   G        : the game folder inside the prefix (exe, DAT, WAVS, saves)
export IC2_WORK=${IC2_WORK:-$HOME/ic2-work}
export DISPLAY=${DISPLAY_IC2:-:99} WINEPREFIX=$IC2_WORK/prefix WINEDEBUG=-all
G=$WINEPREFIX/drive_c/IC2
W=/usr/lib/wine/wine
mkdir -p "$IC2_WORK/shots"
shot(){ import -window root "$IC2_WORK/shots/$1.png"; }
pgrep -x Xvfb >/dev/null || { rm -f /tmp/.X99-lock; (setsid Xvfb :99 -screen 0 1280x1024x24 >/dev/null 2>&1 &); sleep 2; }
