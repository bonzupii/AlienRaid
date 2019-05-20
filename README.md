### AlienRaid
A roguelike RPG coded with python3/libtcod. You are Wrpgnyth, an alien from the Planet Zoltron who has crash landed on earth in the Australian Outback. The wildlife is trying to kill you. The object of the game is to dive as deep as possible. Good luck! 

### Main menu screenshot:

![alt text](https://raw.githubusercontent.com/bonzupii/AlienRaid/master/screenshot1.png "Main Menu")

### Gameplay screenshot:

![alt text](https://raw.githubusercontent.com/bonzupii/AlienRaid/master/screenshot2.png "Gameplay")


### To run the game in linux, open a terminal and cd into the game directory:

Make sure you have python3-pip, libsdl2-dev and libpython3-dev and all dependencies for these packages installed.

Run "pip3 install tcod" to install libtcod

### If you're using ubuntu, debian or a linux distribution based on one of these distros that uses the apt package management system, simply run the "installdeps-apt.sh" script included with this package to automatically install libtcod and all of its dependencies.

Then to launch the game run
 
./launcher.py

or

python3 launcher.py



### To run the game in windows:

Make sure you have python 3.5+ installed.

Open a command prompt or power shell then cd into the game directory.

Run "py -m pip install tcod" to install libtcod

Run "python launcher.py" to excecute the game

This game has worked on windows but it is not officially supported by the game developer. If you have problems running it in windows, holler at me on Freenode in #roguelikedev. The name is Bonzu. We'll try and see if we can get it working for you, but no promises.

### Movement keys are (Ideally viewed in raw text format, github makes this look really wonky):
 
 y   k   u
 
  \  |  / 
 
 h - z - l
 
 /   |  \
 
 b   j   n
 

You may also use the arrow keys for horizontal and vertical movement.
 

### Command keys are:

i - Open inventory.

d - Drop inventory.

z - Rest/Snooze. You will regain a small percentage of your maximum hp. Don't over-use this or the Dropbear will get you!

s - Save game.

g - Grab/Pickup items.

Left-alt + Enter - Enter full screen mode.

Esc (when in game screen or main menu) - Quit game.

Esc (when in character menu, inventory menu or when targetting) - Cancel/Close menu.

. (When standing on a trail) - Take trail to the next level. Once you advance, you can not go back.

More monsters, items and equipment types to come! Have fun and good luck!
