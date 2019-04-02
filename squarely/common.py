#!/usr/bin/env python
# _*_ coding: utf-8 _*_

"""
A puzzle game which utilizes the python-pyglet library

Author: Piotr Miller
e-mail: nwg.piotr@gmail.com
Website: http://nwg.pl
Project: https://github.com/nwg-piotr/squarely
License: GPL3
"""
OFFLINE = 0
SYNCING = 1
ONLINE = 2

dev_mode = False

lang = None  # language dictionary
avbin = False  # being set True if playing intro sound in ogg format does not crash
app_name = "squarely"  # determines the ~/.config/game_folder name
app_dir = None
player_filename = 'player.pkl'
player = None
scores = [None, None, None, None, None, None]

player_dialog = None
player_confirmation = None
settings_dialog = None

board = None
selector = None
cell_bitmaps = []
cells_batch = None
intro_batch = None
player_dialog_batch = None
top_list_batch = None
top_list = None
settings_batch = None
cells_list = []
matrix = None  # 2-dimensional list [row] [col] to assign cells (or None if the spot empty)
rotation_group = None
rotation_direction = None
cursor_in = False
cursor_in_board = False
scrolling = False
scroll_counter = 0
backup_matrix = None
backup_values = None
level = 0
level_max = 5  # 6 in human-readable format :)

summary = []  # list of text labels to display in the summary bar
summary_backup = []  # backup for the list above (for Undo)
summary_bar = None
summary_batch = None
cells_deleted = False

fx = None
label = None

# Game states
game_state = None

top10_content = ""

intro_sprite = None
intro_message = None

headers = {'User-Agent': 'SquarelyTheGame'}  # prevent php scripts from simple access via a browser
message = None

settings = None
