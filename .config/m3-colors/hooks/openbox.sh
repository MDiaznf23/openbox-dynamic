#!/bin/bash

theme_dir="$HOME/.themes/hade/openbox-3"
eww_dir="$HOME/.config/eww"

# Copy themerc sesuai mode
cp "$HOME/.cache/m3-colors/openbox-$M3_MODE" "$theme_dir/themerc"

# Reload openbox
openbox --reconfigure
