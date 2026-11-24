// Note: This installer script was generated with AI assistance.

#!/usr/bin/env bash
# CardFerry installer for Raspberry Pi OS
# Usage: bash install.sh   (run as your normal user, NOT with sudo)
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$(id -u)" -eq 0 ]; then
    echo "Please run this script without sudo: bash install.sh"
    echo "It asks for your password when it needs administrator rights."
    exit 1
fi
APP_USER="$(id -un)"

echo "==> Installing system packages"
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev build-essential i2c-tools
sudo apt-get install -y python3-rpi.gpio || echo "python3-rpi.gpio not available via apt, pip will build RPi.GPIO instead."

echo "==> Creating virtual environment and installing Python packages"
python3 -m venv --system-site-packages "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "==> Enabling I2C"
if command -v raspi-config >/dev/null 2>&1; then
    sudo raspi-config nonint do_i2c 0
else
    echo "raspi-config not found. Please enable I2C manually (see README)."
fi
sudo usermod -aG i2c,gpio "$APP_USER"

echo "==> Creating backup folder /backup-data"
sudo mkdir -p /backup-data
sudo chown "$APP_USER":"$APP_USER" /backup-data

echo "==> Creating users file"
if [ ! -f "$APP_DIR/src/users.json" ]; then
    cp "$APP_DIR/src/users.example.json" "$APP_DIR/src/users.json"
    echo "Created src/users.json - please edit it and enter your users."
else
    echo "src/users.json already exists, leaving it untouched."
fi

echo
read -r -p "Start CardFerry automatically at boot? [y/N] " ANSWER
if [[ "$ANSWER" =~ ^[Yy]$ ]]; then
    sudo tee /etc/systemd/system/CardFerry.service >/dev/null <<EOF
[Unit]
Description=CardFerry SD card backup station
After=multi-user.target

[Service]
User=$APP_USER
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/src/main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable CardFerry.service
    echo "Autostart enabled."
fi

echo
echo "Done. Please reboot now so that I2C and the group changes take effect:"
echo "    sudo reboot"
echo "Then edit src/users.json and start CardFerry with:"
echo "    $APP_DIR/venv/bin/python $APP_DIR/src/main.py"