#!/bin/bash

# Script to set up crontab and aliases

# Check if we're running as root
if [ "$(id -u)" -eq 0 ]; then
    echo "This script should not be run as root. Please run as a regular user."
    exit 1
fi

# Overwrite crontab
echo "Setting up crontab (overwriting any existing entries)..."
echo "@reboot sudo python3 /home/pi/ds/wk.py" | crontab -

# Verify crontab was set up
if crontab -l | grep -q "@reboot sudo python3 /home/pi/ds/wk.py"; then
    echo "Crontab entry successfully installed."
    echo "Warning: Any previous crontab entries have been removed."
else
    echo "Failed to install crontab entry."
    exit 1
fi

# Create the alias file
# Check if alias.txt exists
ALIAS_SOURCE="alias.txt"
if [ ! -f "$ALIAS_SOURCE" ]; then
    echo "Error: $ALIAS_SOURCE not found in current directory."
    exit 1
fi

# Create the alias file
ALIAS_FILE="/home/pi/.bash_aliases"
echo "Creating alias file from $ALIAS_SOURCE..."

# Copy the alias file contents, adding a header
echo "# Aliases generated from $ALIAS_SOURCE on $(date)" > "$ALIAS_FILE"
cat "$ALIAS_SOURCE" >> "$ALIAS_FILE"

# Make sure the alias file is sourced in .bashrc
if ! grep -q "source ~/.bash_aliases" /home/pi/.bashrc; then
    echo "Adding source command to .bashrc..."
    echo -e "\n# Source aliases if file exists" >> /home/pi/.bashrc
    echo "if [ -f ~/.bash_aliases ]; then" >> /home/pi/.bashrc
    echo "    . ~/.bash_aliases" >> /home/pi/.bashrc
    echo "fi" >> /home/pi/.bashrc
fi

# Source the alias file for current session
echo "Sourcing the alias file..."
source "$ALIAS_FILE"

echo "Setup completed successfully."
echo "Current aliases:"
grep "^alias" "$ALIAS_FILE" | sed 's/alias //'
