#!/bin/bash

set -e

# Define paths
ORIG_IMAGE="original_files/initramfs.bin.SD"
MODIFIED_IMAGE="original_files/modified.initramfs.bin.SD"
STAGING_DIR="filesystem_staging"

# Ensure dependencies are installed
command -v dumpimage >/dev/null 2>&1 || { echo "Error: u-boot-tools not installed."; exit 1; }
command -v mkimage >/dev/null 2>&1 || { echo "Error: u-boot-tools not installed."; exit 1; }

# Function to extract initramfs
extract() {
    local input_image=$1
    
    echo "Extracting initramfs..."
    
    # Ensure staging directory exists
    sudo mkdir -p "$STAGING_DIR"
    sudo rm -rf "$STAGING_DIR"/*
    
    # Extract the cpio archive from the uImage
    dumpimage -T ramdisk -p 0 -o extracted_initramfs.gz "$input_image"

    echo "Extracting filesystem as root..."
    sudo bash -c "cd '$STAGING_DIR' && zcat ../extracted_initramfs.gz | cpio -idm"

    rm extracted_initramfs.gz
    echo "Extraction complete. Filesystem is in '$STAGING_DIR'"
}

testextract() {
    local input_image=$1
    
    echo "Extracting initramfs..."
    
    # Ensure staging directory exists
    sudo mkdir -p "${STAGING_DIR}_test"
    sudo rm -rf "${STAGING_DIR}_test"/*
    
    # Extract the cpio archive from the uImage
    dumpimage -T ramdisk -p 0 -o extracted_initramfs.gz "$input_image"

    echo "Extracting filesystem as root..."
    sudo bash -c "cd '${STAGING_DIR}_test' && zcat ../extracted_initramfs.gz | cpio -idm"

    # Save file metadata (useful for debugging)
    sudo bash -c "cd '${STAGING_DIR}_test' && find . -printf '%P %u %g %m\n'" > "$METADATA_FILE"

    rm extracted_initramfs.gz
    echo "Extraction complete. Filesystem is in ${STAGING_DIR}_test'"
}

# Function to repack initramfs
repack() {
    echo "Creating new cpio archive..."
    
    if [ ! -d "$STAGING_DIR" ]; then
        echo "Error: '$STAGING_DIR' does not exist. Run extraction first."
        exit 1
    fi

    sudo bash -c "cd '$STAGING_DIR' && find . -print0 | cpio --null -o --format=newc | gzip > ../new_initramfs.gz"

    sudo mkimage -A arm -O linux -T ramdisk -C gzip -d new_initramfs.gz "$MODIFIED_IMAGE"
    sudo chown anonymous:anonymous $MODIFIED_IMAGE
    sudo rm new_initramfs.gz
    cp "$MODIFIED_IMAGE" tftpboot/initramfs.bin.SD
    echo "Repacking complete. New image saved as '$MODIFIED_IMAGE'"
}

# Handle command-line arguments
if [ "$1" == "extract" ]; then
    extract "$ORIG_IMAGE"
elif [ "$1" == "testextract" ]; then
    testextract "$ORIG_IMAGE"
elif [ "$1" == "extract_modified" ]; then
    extract "$MODIFIED_IMAGE"
elif [ "$1" == "repack" ]; then
    repack
else
    echo "Usage: $0 {extract_orig|extract_modified|repack}"
    exit 1
fi
