#!/bin/sh

flash_nand() {
    filename="$1"
    mtdnum="$2"

    wget "http://192.168.100.1/$filename" -O "$filename" || { echo "Download failed"; return 1; }
    flash_eraseall "/dev/mtd$mtdnum" >/dev/null 2>&1
    nandwrite -p "/dev/mtd$mtdnum" "$filename"
    rm -f "$filename"
}

flash_nand fpgabit.img 10

