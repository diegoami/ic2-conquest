. "$(dirname "$0")/env.sh"
xdotool mousemove 638 547 click 1; sleep 1                       # dismiss offer dialog
xdotool mousemove 45 30 click 1; sleep 1; xdotool mousemove 62 51 click 1; sleep 2   # Game > End turn
xdotool mousemove 122 307 click 1                               # confirm
n=$(cat "$G/AUTOSAVE.LOG" 2>/dev/null | wc -l)
timeout 180 bash -c "until [ \$(cat '$G/AUTOSAVE.LOG' 2>/dev/null | wc -l) -gt $n ]; do sleep 2; done"; echo "wait exit=$?"
sleep 4; xdotool search --onlyvisible --name "turn" getwindowname %@ 2>/dev/null
