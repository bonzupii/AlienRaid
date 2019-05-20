#!/bin/bash
# -*- coding: utf-8 -*-
#
#  installdeps-apt.sh
#  
#  Copyright 2019 Bonzu <bonzupii@protonmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#  
#  
echo "AlienRaid Copyright (C) 2019  Bonzu <bonzupii@protonmail.com>"
echo "This program comes with ABSOLUTELY NO WARRANTY."
echo "This is free software, and you are welcome to redistribute it under"
echo "certain conditions."
echo "See enclosed LICENSE.md for details."
echo " "
echo "Checking for apt package manager..."
command -v apt >/dev/null 2>&1 || { echo >&2 "Apt package manager not found. This dependency installer only works on systems with the apt package management system. Aborting."; exit 1; }
echo "Apt package manager found. Installation can continue."
declare -a packages=("python3-pip" "libsdl2-dev" "libpython3-dev")
for i in "${packages[@]}"; do
    if ! dpkg-query -W -f='${Status}' $i 2>/dev/null | grep -q "ok installed"; then
        echo "$i is not installed, would you like to install it now? (Y/N)"
        read response
        if [[ $response == [yY]* ]]; then
            sudo apt install "$i"
        else
            echo "Installation aborted."
            echo "Please note that this installation script will not work without the $i package."
            exit
        fi
    else
        echo "The $i package has already been installed."
    fi
done
echo "Updating pip3 setuptools..."
sudo pip3 install --upgrade setuptools
echo "Installing python libtcod..."
pip3 install --user tcod

