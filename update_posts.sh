#!/bin/bash

echo "mounting nook"
sudo mount /dev/sda /mnt
echo "running python"
sudo python3 main.py
echo "unmounting nook"
sudo umount /dev/sda
