#!/bin/bash

set -e

SERVICE_NAME=groundstation.service
PROJECT_DIR=$(pwd)

echo "[*] Installing Ground Station from: $PROJECT_DIR"

# Ensure Redis is running
if ! systemctl is-active --quiet redis; then
    echo "[*] Starting Redis..."
    sudo systemctl start redis
    sudo systemctl enable redis
fi

# Create environment file with project path
ENV_FILE=/etc/systemd/system/groundstation.env
echo "GS_PROJECT_DIR=$PROJECT_DIR" | sudo tee $ENV_FILE > /dev/null

# Copy and configure systemd service
echo "[*] Installing systemd service..."
sudo cp $SERVICE_NAME /etc/systemd/system/

# Add EnvironmentFile to service (if not already added)
sudo sed -i '/^\[Service\]/a EnvironmentFile=/etc/systemd/system/groundstation.env' /etc/systemd/system/$SERVICE_NAME

# Reload systemd and restart the service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable groundstation.service
sudo systemctl restart groundstation.service

echo "[✓] Ground Station daemon installed and running."

# Symlink gs_ctl to /usr/local/bin for global access
BIN_LINK=/usr/local/bin/gs_ctl
SCRIPT_PATH="$PROJECT_DIR/gs_ctl.py"

echo "[*] Linking $SCRIPT_PATH to $BIN_LINK"
sudo ln -sf "$SCRIPT_PATH" "$BIN_LINK"
sudo chmod +x "$SCRIPT_PATH"
