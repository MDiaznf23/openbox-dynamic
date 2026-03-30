#!/bin/bash
WINDOW="control_center_window"

if eww active-windows | grep -q "$WINDOW"; then
    eww update control_center_window=false
    eww close "$WINDOW"
else
    # Tutup panel lain dulu
    eww close wifi_window
    eww close bluetooth_window
    eww close audio_window

    eww update control_center_window=true
    eww open "$WINDOW"
fi
