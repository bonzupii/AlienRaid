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

### Running the game (Nix)

The game runs inside a hermetic nix dev shell — nothing is installed globally.

```sh
nix develop          # resolves nixpkgs 26.05 and runs `uv sync` into .venv
.venv/bin/python launcher.py
```

All dependencies (pygame, SDL2, SDL2_image, SDL2_ttf, libGL) are provided by
the flake; `uv` resolves everything into a project-local `.venv`. There are no
version pins in `pyproject.toml` — `uv.lock` pins the resolved set.

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

Fifteen species, each with its own behaviour: territorial **Kangas** (they wind
up mighty kicks), timid **Joeys**, skittish **Wallabies**, bruiser **Wallaroos**,
ambushing **Tree Kangas**, pack-hunting **Dingoes**, cover-darting **Goannas**,
hit-and-run **Killer Bees**, pouncing **Dropbears**, venom-spitting **Taipans**,
fast **Emus**, unshakeable **Wombats**, swooping **Magpies**, lethal **Cassowaries**
and ambush **Crocodiles**. The AI uses lightweight Turochamp-style heuristics —
every species scores its options each turn with a tuned evaluation function
rather than searching deep.

### Developing

Run the test suite inside the dev shell:

```sh
nix develop -c .venv/bin/python -m unittest discover -s tests
```

`tests/render_sprite_sheet.py` renders every procedural sprite (and the
preserved font charset) into labeled PNG sheets for visual review.
