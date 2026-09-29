. "$(dirname "$0")/env.sh"
# open: File > Open, type name, Enter, dismiss offer dialog if any
xdotool mousemove 14 36 click 1; sleep 1; xdotool mousemove 30 72 click 1; sleep 2
xdotool mousemove 636 450 click 1; sleep 0.5; xdotool type --delay 30 "$1"; xdotool key Return; sleep 5
