#!/bin/bash
WIN_ID="$1"

active_id=$(xprop -root _NET_ACTIVE_WINDOW | grep -oP '0x[0-9a-f]+' | head -1)
active_dec=$(printf '%d' "$active_id" 2>/dev/null || echo 0)
win_dec=$(printf '%d' "$WIN_ID" 2>/dev/null || echo 0)

state=$(xprop -id "$WIN_ID" _NET_WM_STATE 2>/dev/null)

if echo "$state" | grep -q "HIDDEN"; then
  # Kalau minimize → restore dan focus
  xdotool windowmap "$WIN_ID"
  wmctrl -i -a "$WIN_ID"
elif [ "$win_dec" -eq "$active_dec" ]; then
  # Kalau sudah aktif → minimize
  xdotool windowminimize "$WIN_ID"
else
  # Kalau tidak aktif → focus
  wmctrl -i -a "$WIN_ID"
fi
