#!/bin/bash
WINDOW="notification_center"

if eww active-windows | grep -q "$WINDOW"; then
    eww update notification_center=false
    eww close "$WINDOW"
else
    eww update notification_center=true
    eww open "$WINDOW"
fi
