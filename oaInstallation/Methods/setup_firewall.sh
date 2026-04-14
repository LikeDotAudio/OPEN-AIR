#!/bin/bash
# OPEN-AIR System Setup Script
# This script configures the system firewall and installs necessary networking utilities.
# Run this script with sudo to configure the system for OPEN-AIR networking.

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./setup_firewall.sh)"
  exit
fi

echo "🚀 Setting up OPEN-AIR environment..."

# Install avahi-utils for mDNS/DNS-SD discovery
echo "Installing avahi-utils for mDNS/DNS-SD discovery..."
apt update && apt install -y avahi-utils
if [ $? -ne 0 ]; then
    echo "🛑 ERROR: Failed to install avahi-utils. Please install it manually with 'sudo apt install avahi-utils'."
    exit 1
fi
echo "✅ avahi-utils installed successfully."

echo "🛡️ Configuring OPEN-AIR Firewall Rules..."

# Allow mDNS (Bonjour)
echo "Allowing mDNS (5353/udp)..."
ufw allow 5353/udp comment 'mDNS discovery'

# Allow SAP (Session Announcement Protocol)
echo "Allowing SAP Multicast (9875/udp)..."
ufw allow 9875/udp comment 'SAP announcements'

# Allow NMOS Default Ports
echo "Allowing NMOS API Ports (8085/tcp, 4000/tcp)..."
ufw allow 8085/tcp comment 'NMOS API'
ufw allow 4000/tcp comment 'NMOS API'

# Allow MQTT
echo "Allowing MQTT (1883/tcp)..."
ufw allow 1883/tcp comment 'MQTT broker'

# Allow OSC (Default Port)
echo "Allowing OSC Default (8000/udp)..."
ufw allow 8000/udp comment 'OSC default port'

echo "✅ Firewall configuration complete! Reloading UFW..."
ufw reload --no-prompt # Reload without prompting if possible
if [ $? -ne 0 ]; then
    echo "⚠️ WARNING: UFW reload failed. Please reload manually with 'sudo ufw reload'."
fi

echo "🎉 OPEN-AIR networking prerequisites are fully configured."