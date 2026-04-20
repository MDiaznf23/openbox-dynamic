killall eww 2>/dev/null
eww daemon
while ! eww ping &>/dev/null; do sleep 0.1; done
eww open bar

pkill -f fullscreen-monitor
python3 ~/.config/eww/scripts/fullscreen-monitor.py &
