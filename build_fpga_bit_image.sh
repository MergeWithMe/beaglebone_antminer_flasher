#!/bin/sh

# Set the source directory and target device
FPGA_DIR="fpgabit"     # Directory containing FPGA bitstream files
PARTITION_SIZE=83886080  # Partition size in bytes (0x5000000 bytes = 80 MB)
IMAGE_NAME="./tftpboot/fpgabit.img"  # Output image file name
MOUNT_POINT="/tmp/fat32"  # Temporary mount point for creating the FAT32 partition

sudo mkdir -p $MOUNT_POINT
sudo rm $IMAGE_NAME

# Step 1: Create an empty file for the FAT32 partition with the correct size
dd if=/dev/zero of=$IMAGE_NAME bs=$PARTITION_SIZE count=1 status=progress

# Step 2: Create a FAT32 filesystem inside the image file
mkfs.vfat -F 32 $IMAGE_NAME

# Step 3: Mount the image file to a temporary directory
mkdir -p $MOUNT_POINT
sudo mount -o loop $IMAGE_NAME $MOUNT_POINT

# Step 4: Copy the contents of the fpgabit folder to the mounted partition
sudo cp -r $FPGA_DIR/* $MOUNT_POINT/

# Step 5: Unmount the image and clean up
sudo umount $MOUNT_POINT
sudo rm -rf $MOUNT_POINT
