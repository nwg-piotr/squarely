# squarely
Having nothing better to do, I decided to give a try to Pyglet. I'm coding a simple puzzle game.
Feel free to contribute to the project if you find it funny / interesting enough.

The game board consists of 6 types of cells in `6 + n * 3` columns x `6 + n * 3`. Each 2 x 2 group, if contains at 
least 3 cells, can be rotated left or right (left/right mouse click), 90 degrees in one step. 3 or more cells of the 
same type, arranged in a horizontal row, disappear. All the cells above fall down. The game objective is to destroy all 
the cells and unlock the next level. Next board size will be `n+3 x n+3`.

![screen](http://nwg.pl/squarely/wiki/screen1.png)

Some work still left to do. See the current development state in action: https://youtu.be/kkd3cE-pYDI

The game is being developed on Arch Linux with [Pycharm Community Edition](https://www.jetbrains.com/pycharm/download).
The PKGBUILD file and/or the testing package you'll find in the `dist` folder. No packages for other Linux 
distributions available at the moment, but you can always clone the project to give it a try.
