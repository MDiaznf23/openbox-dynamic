#!/bin/bash

is_fullscreen() {
    fullscreen_count=$(i3-msg -t get_tree 2>/dev/null | jq '[.. | select(.window? != null and .fullscreen_mode? == 1)] | length' 2>/dev/null)
    
    if [ "$fullscreen_count" -gt 0 ]; then
        return 0
    else
        return 1
    fi
}

prev_state="not_fullscreen"
while true; do
    if is_fullscreen; then
        if [ "$prev_state" != "fullscreen" ]; then
            eww close bar 2>/dev/null
            eww close topbar 2>/dev/null
            prev_state="fullscreen"
        fi
    else
        if [ "$prev_state" != "not_fullscreen" ]; then
            eww open bar 2>/dev/null
            eww open topbar 2>/dev/null
            prev_state="not_fullscreen"
        fi
    fi
    
    sleep 0.3
done
