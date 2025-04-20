#!/bin/bash

# Production Deployment Script for Aiayer

# Exit on error
set -e

# Configuration
APP_NAME="aiayer"
APP_USER=$(whoami)
APP_GROUP="staff"
INSTALL_DIR="/opt/$APP_NAME"
LOG_DIR="/var/log/$APP_NAME"
CONFIG_DIR="/etc/$APP_NAME"
VENV_DIR="$INSTALL_DIR/venv"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [ "$(id -u)" != "0" ]; then
    error "This script must be run as root"
fi

# Create necessary directories
log "Creating directories..."
mkdir -p $INSTALL_DIR
mkdir -p $LOG_DIR
mkdir -p $CONFIG_DIR

# Set permissions
log "Setting permissions..."
chown -R $APP_USER:$APP_GROUP $INSTALL_DIR
chown -R $APP_USER:$APP_GROUP $LOG_DIR
chown -R $APP_USER:$APP_GROUP $CONFIG_DIR
chmod 755 $INSTALL_DIR
chmod 755 $LOG_DIR
chmod 755 $CONFIG_DIR

# Install system dependencies
log "Installing system dependencies..."
if command -v brew >/dev/null 2>&1; then
    brew install python3
    brew install redis
else
    error "Homebrew is not installed. Please install Homebrew first: https://brew.sh/"
fi

# Create and activate virtual environment
log "Setting up Python virtual environment..."
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Install Python dependencies
log "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy application files
log "Copying application files..."
cp -r ./* $INSTALL_DIR/
rm -rf $INSTALL_DIR/venv  # Remove the copied venv directory

# Copy configuration files
log "Copying configuration files..."
cp config/* $CONFIG_DIR/

# Create launchd service
log "Creating launchd service..."
cat > /Library/LaunchDaemons/com.$APP_NAME.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.$APP_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_DIR/bin/gunicorn</string>
        <string>--workers=4</string>
        <string>--bind=0.0.0.0:8000</string>
        <string>--timeout=120</string>
        <string>--access-logfile=$LOG_DIR/access.log</string>
        <string>--error-logfile=$LOG_DIR/error.log</string>
        <string>app:app</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/error.log</string>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/output.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>PYTHONPATH</key>
        <string>$INSTALL_DIR</string>
    </dict>
</dict>
</plist>
EOF

# Set permissions for launchd service
chown root:wheel /Library/LaunchDaemons/com.$APP_NAME.plist
chmod 644 /Library/LaunchDaemons/com.$APP_NAME.plist

# Load and start the service
log "Starting service..."
launchctl load /Library/LaunchDaemons/com.$APP_NAME.plist
launchctl start com.$APP_NAME

# Verify installation
log "Verifying installation..."
sleep 5
if curl -s http://localhost:8000/health > /dev/null; then
    log "Application is running successfully!"
else
    error "Application failed to start. Check logs at $LOG_DIR/error.log"
fi

# Print next steps
echo -e "\n${GREEN}Deployment completed successfully!${NC}"
echo -e "\nNext steps:"
echo "1. Configure your application in $CONFIG_DIR/"
echo "2. Monitor logs at $LOG_DIR/"
echo "3. Access the application at http://localhost:8000"
echo "4. To stop the service: sudo launchctl unload /Library/LaunchDaemons/com.$APP_NAME.plist"
echo "5. To start the service: sudo launchctl load /Library/LaunchDaemons/com.$APP_NAME.plist"
echo "6. To view logs: tail -f $LOG_DIR/error.log" 