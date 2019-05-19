#!/bin/bash
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

