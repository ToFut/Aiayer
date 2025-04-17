#!/bin/bash

# Backup Script for Aiayer

# Exit on error
set -e

# Configuration
APP_NAME="aiayer"
BACKUP_DIR="/var/backups/$APP_NAME"
CONFIG_DIR="/etc/$APP_NAME"
LOG_DIR="/var/log/$APP_NAME"
INSTALL_DIR="/opt/$APP_NAME"
RETENTION_DAYS=30

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

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Generate backup filename with timestamp
BACKUP_FILE="$BACKUP_DIR/${APP_NAME}_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

# Create backup
log "Creating backup..."
tar -czf $BACKUP_FILE $CONFIG_DIR $LOG_DIR $INSTALL_DIR/config

# Verify backup
if [ -f $BACKUP_FILE ]; then
    log "Backup created successfully: $BACKUP_FILE"
else
    error "Backup creation failed"
fi

# Clean up old backups
log "Cleaning up old backups..."
find $BACKUP_DIR -name "${APP_NAME}_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Print backup information
echo -e "\nBackup Information:"
echo "Backup file: $BACKUP_FILE"
echo "Size: $(du -h $BACKUP_FILE | cut -f1)"
echo "Contents:"
tar -tvf $BACKUP_FILE | head -n 5
echo "..."
echo -e "\nNext backup will be cleaned up after $RETENTION_DAYS days"

# Optional: Upload to remote storage
# Uncomment and configure the following section if you want to upload backups to a remote server
# REMOTE_USER="backup_user"
# REMOTE_HOST="backup.example.com"
# REMOTE_DIR="/backups/$APP_NAME"
# 
# log "Uploading backup to remote server..."
# scp $BACKUP_FILE $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/
# 
# if [ $? -eq 0 ]; then
#     log "Backup uploaded successfully"
# else
#     error "Backup upload failed"
# fi 