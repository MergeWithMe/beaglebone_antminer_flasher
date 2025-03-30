#!/bin/bash

# Set variables
SOURCE_DIR="./tftpboot"
SOURCE_DIR2="./python_scripts"
REMOTE_USER="tftp"
REMOTE_HOST="rugged"
REMOTE_DIR="/tftpboot"
PYTHON_DIR="/python_scripts"
REMOTE_USER_GROUP="tftp:tftp"

# Ensure the source directory exists
if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "Source directory '$SOURCE_DIR' does not exist!"
    exit 1
fi

# Sync the local tftpboot to the remote server
echo "Syncing files from '$SOURCE_DIR' to '$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR'..."
rsync -av --no-times --delete --force --chown=$REMOTE_USER_GROUP $SOURCE_DIR/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

echo "Syncing files from '$SOURCE_DIR2' to '$REMOTE_USER@$REMOTE_HOST:$PYTHON_DIR'..."
rsync -av --no-times --delete --force --chown=$REMOTE_USER_GROUP $SOURCE_DIR2/ $REMOTE_USER@$REMOTE_HOST:$PYTHON_DIR/

# Check if the rsync was successful
if [[ $? -ne 0 ]]; then
    echo "Error: rsync failed!"
    exit 1
fi

echo "Sync completed successfully!"
