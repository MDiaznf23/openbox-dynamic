#!/bin/bash
WINDOW="calendar_window"

if eww active-windows | grep -q "$WINDOW"; then
    eww update calendar_window=false
    eww close "$WINDOW"
else
    eww update calender_window=true
    eww open "$WINDOW"
fi
