#!/bin/bash
WINDOW="start_menu"

if eww active-windows | grep -q "$WINDOW"; then
    eww update start_menu=false
    eww close "$WINDOW"
else
    eww update start_menu=true
    eww open "$WINDOW"
fi
