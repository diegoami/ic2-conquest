# play out an open battle with Computer general; stop when the result dialog appears
. "$(dirname "$0")/env.sh"
timeout 240 bash -c 'until xdotool search --onlyvisible --name " v " >/dev/null 2>&1; do sleep 2; done' || { echo "no battle"; exit 1; }
sleep 2; xdotool mousemove 158 112 click 1; sleep 1
for i in $(seq 1 60); do xdotool search --onlyvisible --name "Battle ended" >/dev/null 2>&1 && break; xdotool mousemove 110 112 click 1; sleep 2; done
echo "clicks=$i"; w=$(xdotool search --onlyvisible --name "Battle ended"); import -window $w "$IC2_WORK/shots/result_$1.png"
