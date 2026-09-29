# usage: newgame.sh <row 0..15> <out name>
. "$(dirname "$0")/env.sh"
/usr/lib/wine/wineserver -k 2>/dev/null; sleep 1; rm -f $G/AUTO*
cd $G && (setsid $W "${IC2_EXE:-Imperial Conquest 2 fast rollingsave.exe}" >/dev/null 2>&1 &)
timeout 40 bash -c 'until xdotool search --name "^Imperial Conquest 2$" >/dev/null 2>&1; do sleep 1; done'; sleep 3
xdotool mousemove 14 36 click 1; sleep 1; xdotool mousemove 30 56 click 1; sleep 3
xdotool mousemove 109 $((114 + 20*$1)) click 1; sleep 0.5; xdotool mousemove 344 194 click 1
timeout 120 bash -c "until [ -f '$G/AUTOSAVE.LOG' ]; do sleep 1; done"; sleep 2
cat $G/AUTOSAVE.LOG; xdotool search --onlyvisible --name "turn" getwindowname %@
mkdir -p "$IC2_WORK/out"; cp $G/AUTO*.SAV "$IC2_WORK/out/$2"
