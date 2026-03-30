#!/bin/bash
eww kill 2>/dev/null || killall -9 eww 2>/dev/null
sleep 0.5
eww daemon &
while ! eww ping &>/dev/null; do
    sleep 0.3
done
eww open bar &
