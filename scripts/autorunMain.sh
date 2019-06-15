#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home

cd /
cd home/pi/RoombaGit/scripts
sudo lxterminal --command="sudo python3 /home/pi/RoombaGit/scripts/cleaning.py"

cd /