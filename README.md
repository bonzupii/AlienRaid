# AlienRaid
A roguelike RPG coded with python3/libtcod. You are Wrpgnyth, an alien from the Planet Zoltron who has crash landed on earth in the Australian Outback. The wildlife is trying to kill you. The object of the game is to dive as deep as possible. Good luck! 

To run the game in linux, open a terminal and cd into the game directory, then run:

./engine.py

or

python3 engine.py

If you get an error message saying engine.py isn't excecutable, run "chmod +x engine.py" then run "./engine.py" again.


To run the game in windows:

Make sure you have python 3.5+ installed.

Open a command prompt or power shell then cd into the game directory.

Run "python engine.py".

This game has worked on windows but it is not officially supported by the game developer. If you have problems running it in windows, holler at me on Freenode in #roguelikedev. The name is Bonzu. We'll try and see if we can get it working for you, but no promises.

Movement keys are (Ideally viewed in raw text format, github makes this look really wonky):
 
 y   k   u
 
  \  |  / 
 
 h - z - l
 
 /  |  \
 
 b   j   n
 

You may also use the arrow keys for horizontal and vertical movement.
 

Command keys are:

i - Open inventory.

d - Drop inventory.

z - Rest/Snooze. You will regain a small percentage of your maximum hp. Don't over-use this or the Dropbear will get you!

g - Grab/Pickup items.

Left-alt + Enter - Enter full screen mode.

Esc (when in game screen or main menu) - Quit game.

Esc (when in character menu, inventory menu or when targetting) - Cancel/Close menu.

. (When standing on a trail) - Take trail to the next level. Once you advance, you can not go back.

If you are having trouble with the including libtcod libraries, try running "pip3 install tcod" and then delete the directory "libtcodpy" from the base game directory, then delete libtcod.so, libtcod.so.0, libtcod.so.0.0.0, libtcod.dll, libtcod-gui.dll and SDL2.dll from the base game directory.

More monsters, items and equipment types to come! Have fun and good luck!
