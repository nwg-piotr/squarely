#!/usr/bin/env python
# _*_ coding: utf-8 _*_

"""
A puzzle game which utilizes the python-pyglet library

Author: Piotr Miller
e-mail: nwg.piotr@gmail.com
Website: http://nwg.pl
Project: https://github.com/nwg-piotr/squarely
License: GPL3

Dependencies (Arch Linux): python-pyglet, avbin7 (AUR package necessary to play compressed sound files)
"""
lang = None  # language dictionary
avbin = False  # being set True if playing intro sound in ogg format does not crash
app_name = "squarely"  # determines the ~/.config/game_folder name
app_dir = None
player_filename = 'player.pkl'
player = None
scores = [None, None, None, None, None, None]

rc = None

board = None
selector = None
cell_bitmaps = []
cells_batch = None
intro_batch = None
player_dialog_batch = None
cells_list = []
matrix = None
rotation_group = None
rotation_direction = None
cursor_in = False
cursor_in_board = False
scrolling = False
scroll_counter = 0
backup_matrix = None
backup_values = None
level = 0
level_max = 5

summary = []  # backup list of text labels to display in the summary bar
summary_backup = []  # backup for the list above
summary_bar = None
summary_batch = None
cells_deleted = False

fx = None
label = None
playing = False
intro = True
dialog = False

intro_sprite = None
intro_message = None
