#!/bin/bash
set -e

echo "================================"
echo "Installing Dotfiles (Openbox)"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

error()   { echo -e "${RED}✗ $1${NC}"; }
success() { echo -e "${GREEN}✓ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Install base packages
echo "Installing base-devel..."
sudo pacman -S --needed --noconfirm base-devel git

# Check / install AUR helper
if ! command -v yay &> /dev/null && ! command -v paru &> /dev/null; then
    echo "Installing yay (AUR helper)..."
    git clone https://aur.archlinux.org/yay.git /tmp/yay
    cd /tmp/yay && makepkg -si --noconfirm
    cd -
fi
AUR_HELPER=$(command -v yay || command -v paru)

# Backup existing configs
BACKUP_DIR=~/dotfiles_backup_$(date +%Y%m%d_%H%M%S)
echo "Backing up existing configs to $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"
[ -d ~/.config ]  && cp -r ~/.config  "$BACKUP_DIR/"
[ -d ~/.themes ]  && cp -r ~/.themes  "$BACKUP_DIR/"
[ -d ~/.local ]   && cp -r ~/.local   "$BACKUP_DIR/"

# Install system packages
echo "Installing system packages..."
sudo pacman -S --needed --noconfirm \
    openbox alacritty dunst rofi feh scrot xclip xdotool dex \
    brightnessctl playerctl lm_sensors xsettingsd \
    python python-pip python-pipx fish redshift inotify-tools \
    jq bc rsync fastfetch pamixer python-xlib \
    networkmanager network-manager-applet blueman bluez bluez-utils \
    pipewire pipewire-pulse xorg-xprop ffmpeg \
    xcompmgr qt5ct pcmanfm imagemagick neovim wmctrl

# Install fonts
echo "Installing fonts..."
sudo pacman -S --needed --noconfirm \
    noto-fonts noto-fonts-cjk noto-fonts-emoji noto-fonts-extra \
    ttf-jetbrains-mono ttf-fira-code ttf-dejavu \
    ttf-liberation ttf-font-awesome

# Install AUR packages
echo "Installing AUR packages..."
$AUR_HELPER -S --needed --noconfirm \
    eww-git \
    mpdris2 \
    ttf-jetbrains-mono-nerd \
    ttf-iosevka-nerd \
    ttf-twemoji \
    ueberzugpp \
    m3wal \
    fastcompmgr

# Install custom fonts
if [ -d "fonts" ]; then
    echo "Installing custom fonts..."
    FONT_DIR="$HOME/.local/share/fonts"
    mkdir -p "$FONT_DIR"
    cp -rf fonts/* "$FONT_DIR"
    fc-cache -fv
    success "Custom fonts installed"
fi

# Install Tela icon theme
echo "Installing Tela icon theme..."
git clone https://github.com/vinceliuice/Tela-icon-theme.git /tmp/Tela-icon-theme
cd /tmp/Tela-icon-theme && ./install.sh
cd -
success "Tela icon theme installed"

# Set fish as default shell
echo "Setting fish as default shell..."
sudo chsh -s "$(which fish)" "$USER"
export PATH="$HOME/.local/bin:$PATH"

# Create necessary directories
echo "Creating directories..."
mkdir -p ~/.config
mkdir -p ~/.local/share
mkdir -p ~/.themes
mkdir -p ~/.cache

# Copy .config
if [ -d ".config" ]; then
    echo "Copying .config..."
    rsync -av --exclude='*.tmp' .config/ ~/.config/
    success ".config copied"
fi

# Copy .local/share (GTK theme FlatColor)
if [ -d ".local/share" ]; then
    echo "Copying .local/share (GTK themes)..."
    rsync -av .local/share/ ~/.local/share/
    success ".local/share copied"
fi

# Copy .themes (Openbox themes)
if [ -d ".themes" ]; then
    echo "Copying .themes..."
    rsync -av .themes/ ~/.themes/
    success ".themes copied"
fi

# Copy wallpapers
if [ -d "Wallpapers" ] || [ -d "wallpapers" ]; then
    echo "Copying wallpapers..."
    mkdir -p ~/Pictures
    [ -d "Wallpapers" ] && cp -r Wallpapers ~/Pictures/
    [ -d "wallpapers" ] && cp -r wallpapers ~/Pictures/
    success "Wallpapers copied"
fi

# Make scripts executable
echo "Setting permissions..."
find ~/.config -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} \; 2>/dev/null
success "Permissions set"

# Initialize m3wal with default wallpaper
echo ""
echo "================================"
echo "Initializing m3wal..."
echo "================================"

WALLPAPER=$(find ~/Pictures/Wallpapers ~/Pictures/wallpapers -type f \( -iname "*.jpg" -o -iname "*.png" \) 2>/dev/null | head -n 1)

if [ -n "$WALLPAPER" ]; then
    echo "Applying wallpaper: $WALLPAPER"
    m3wal "$WALLPAPER" --full
    success "Wallpaper and theme applied"
else
    warning "No wallpaper found, skipping m3wal initialization"
    echo "Run 'm3wal /path/to/wallpaper.jpg --full' manually later"
fi

# Final message
echo ""
echo "================================"
echo "Installation Complete!"
echo "================================"
echo "Backup saved at: $BACKUP_DIR"
echo ""
echo "Installed components:"
echo "openbox, rofi, dunst, fastcompmgr"
echo "alacritty, feh, xsettingsd"
echo "eww, m3wal, mpdris2"
echo "blueman, networkmanager"
echo "Nerd Fonts & icon fonts"
echo "FlatColor GTK theme"
echo "Openbox themes"
echo ""
echo "Next steps:"
echo "1. Logout and login again"
echo "2. Choose Openbox as a WM"
echo "3. Change wallpaper: m3wal /path/to/wallpaper.jpg --full"
echo ""
echo "================================"
