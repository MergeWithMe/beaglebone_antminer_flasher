#!/bin/bash

IDE=am335x-boneblack-blackmainer
SRC=$IDE.dts
DST=../tftpboot/am335x-boneblack-fpgaplatform.dtb

dtc -O dtb -b 0 -o $DST $SRC
