#!/bin/bash
echo "Does your system use the apt package management system? (Y/N)"
read response
if [[ $response == [yY]* ]]; then
    declare -a packages=("python3-pip" "libsdl2-dev" "libpython3-dev")
else
    echo "This dependency installer only works on systems with the apt package management system. Aborting."
    exit
fi
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
sudo pip3 install tcod

