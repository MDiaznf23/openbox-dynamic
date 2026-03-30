#!/bin/bash

get_workspaces() {
  total=$(xprop -root _NET_NUMBER_OF_DESKTOPS | awk '{print $3}')
  current=$(xprop -root _NET_CURRENT_DESKTOP | awk '{print $3}')

  result="["
  for i in $(seq 0 $((total - 1))); do
    focused="false"
    [ "$i" -eq "$current" ] && focused="true"
    [ $i -gt 0 ] && result+=","
    result+="{\"num\":$((i+1)),\"focused\":$focused}"
  done
  result+="]"
  echo "$result"
}

get_workspaces

xprop -root -spy _NET_CURRENT_DESKTOP _NET_NUMBER_OF_DESKTOPS 2>/dev/null | while read -r _; do
  get_workspaces
done
