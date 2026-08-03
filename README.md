### AlienRaid

A roguelike RPG. You are **Wrpgnyth**, an alien from the planet Zoltron who
crash-landed in the Australian Outback. Your ship is in pieces — the Antimatter
Core, the Navigation Computer, the Power Coupling and the Hull Plating were torn
loose and scattered deep in the earth. Salvage all four parts, fight your way
back to the surface, and repair your ship before a kanga turns your entrails
into extrails.

The deeper you dive, the meaner the wildlife gets. And don't rest too long —
the Dropbear is always listening.

### Main menu screenshot:

![alt text](https://raw.githubusercontent.com/bonzupii/AlienRaid/master/screenshot1.png "Main Menu")

### Gameplay screenshot:

![alt text](https://raw.githubusercontent.com/bonzupii/AlienRaid/master/screenshot2.png "Gameplay")

### Running the game

Open a terminal in the game directory and run:

```sh
nix develop
python launcher.py
```

The first `nix develop` takes a little while — it builds pygame and the SDL
libraries from the nix store, and nothing is installed on your system. The
window is resizable — the view scales to fit while keeping the game's aspect
ratio, so it plays fine no matter how your window manager sizes it.

Not using Nix? Install Python 3.11+ and pygame (`pip install pygame` or
`uv sync`), then run `python launcher.py`.

### Movement keys

```
 y   k   u

  \  |  /

 h - z - l

 /   |  \

 b   j   n
```

The arrow keys work for horizontal and vertical movement too.

### Command keys

- `i` — Open inventory.
- `d` — Drop inventory.
- `z` — Rest/Snooze. Regains a small percentage of your maximum HP. Don't over-use it, or the Dropbear will get you.
- `s` — Save game.
- `g` — Grab/Pickup items.
- `.` — Take the trail (descend/ascend) when standing on it; install salvaged parts when standing on your ship.
- Left-alt + Enter — Toggle full screen.
- Esc — Quit (in game or main menu); cancel/close menus; leave the victory or death screen.

Ship parts are recovered automatically when you step onto them. Salvage all
four, return to the surface and use the ship to escape!

### The wildlife

Seventeen species, each with its own behaviour: territorial **Kangas** (they
wind up mighty kicks), timid **Joeys**, skittish **Wallabies**, bruiser
**Wallaroos**, ambushing **Tree Kangas**, pack-hunting **Dingoes**, cover-darting
**Goannas**, hit-and-run **Killer Bees**, pouncing **Dropbears**, quilled
**Echidnas** (they prick anyone who hits them), venom-spitting **Taipans**,
fast **Emus**, venomous **Funnel-web Spiders**, unshakeable **Wombats**, swooping
**Magpies**, lethal **Cassowaries** and ambush **Crocodiles**.

### ALIENRAID PARODY / FAIR-USE NOTICE

AlienRaid is an unofficial, non-commercial, fan-made parody. Its
Men in Black-inspired elements -- the black-suit agent "J", the
neuralyzer device, and the "MIB" name -- appear solely for parody
and homage, under fair-use / fair-dealing principles.

AlienRaid is not affiliated with, endorsed, sponsored, or licensed
by Sony Pictures, Columbia Pictures, Marvel/Malibu Comics, or any
other owner of the Men in Black franchise. No claim is made to any
of their trademarks or copyrights; all such names and elements
remain the property of their respective owners. The in-game agent
is an original pixel-art caricature, not a likeness of any real
actor.

All original AlienRaid content is (C) 2019-2026 Bonzupii, GPLv3.

A personal note: Will Smith, if you're seeing this, big honor. Big fan
of your work, you handsome studmuffin.
