# squarely
Having nothing better to do, I decided to give a try to the [pyglet](https://bitbucket.org/pyglet/pyglet) library, 
and the result was this puzzle game. It's currently in beta development stage, available for testing as 
[squarely](https://aur.archlinux.org/packages/squarely) in Arch Linux AUR repository.


The game board consists of 6 types of cells in `6 + n * 3` columns x `6 + n * 3`. Each 2 x 2 group, if contains at 
least 3 cells, can be rotated left or right (left/right mouse click), 90 degrees in one step. 3 or more cells of the 
same type, arranged in a horizontal row, disappear. All the cells above fall down. The game objective is to destroy all 
the cells and unlock the next level. Next board size will be `n+3 x n+3`.

![screen](http://nwg.pl/squarely/wiki/l1.png)

See the gameplay on YouTube: https://youtu.be/ZaYMBqo60Qk

## Controls:

- left / right click: rotate a group left or right;
- middle click | scroller | H key: display the summary bar;
- Escape key: exit current dialog / exit the game;
- F key: turn FPS display on/off.

## Optional argument:

- `-lang ln_LN`: forces use of a certain translation strings (currently just en_EN and pl_PL available)

## Runtime configuration:

You may edit the `~/.config/squarely/squarelyrc` file to set some more things:

```text
[runtime]
force_lang = en_EN
debug_mode = True
safe_mode = True
show_fps = False
```

- `debug_mode`: turns on more talkative display in the terminal;
- `safe_mode`: tries to revert a board misbehaviour that happens when loosing animation frames; turn on on less 
powerful machines.

Other files in the `~/.config/squarely` folder store local data of the player currently signed in, and preferences.
Deletion of the `player.pkl` file results in signing the player out. All the scores should be safe on the server.