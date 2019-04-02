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
import pyglet
from pyglet import image
from pyglet.gl import *
from game_objects import Cell, Player, UnlockAnimation, FinishedAnimation, HelloAnimation, SunglassesAnimation
from cloud_tools import sync_needed, player_sync

import os
import pickle
import random
import configparser
import common


def create_cells(board):
    """
    We'll assign cells to a 2-dimensional list: common.matrix[row][column]
    """
    common.matrix = [[0 for c in range(board.cells_in_row)] for r in range(board.cells_in_row)]

    """
    We need to check how many cells of each type should be created for the puzzle could be solved.
    The board.cell_resources list holds the values corresponding to current board dimensions.
    """
    resources = board.cell_resources.copy()

    batch = pyglet.graphics.Batch()
    common.cells_list = []
    for row in range(board.cells_in_row):
        for column in range(board.cells_in_row):

            success = False
            cell_type = 0

            while not success:
                cell_type = random.randint(0, 5)
                if resources[cell_type] > 0:
                    success = True
                    resources[cell_type] -= 1

            cell = Cell(board, cell_type, row, column)
            cell.batch = batch
            common.cells_list.append(cell)

            common.matrix[row][column] = cell  # add to the matrix

    return batch


def create_cells_bitmaps(file):
    common.cell_bitmaps = []
    img = image.load(file)
    for i in range(8):
        common.cell_bitmaps.append(img.get_region(i * 216, 0, 216, 216))


def select_highlighted_cells(board, selector_row, selector_column):
    """Selection order:
       | 2 | 3 |
       |---|---|
       | 0 | 1 |
    """
    deselect_all_cells()

    """selector_row, selector_column designate position of cell #0 (in the matrix[row][col] & on the board)"""
    board.sel_0 = common.matrix[selector_row][selector_column]
    board.sel_1 = common.matrix[selector_row][selector_column + 1]
    board.sel_2 = common.matrix[selector_row + 1][selector_column]
    board.sel_3 = common.matrix[selector_row + 1][selector_column + 1]

    if board.sel_0 is not None:
        board.sel_0.select()
    if board.sel_1 is not None:
        board.sel_1.select()
    if board.sel_2 is not None:
        board.sel_2.select()
    if board.sel_3 is not None:
        board.sel_3.select()


def rotate_selection_right(board, panel):
    for cell in cells_being_rotated(board):
        if cell is not None:
            cell.visible = False

    if common.rotation_group.rotation < 90:
        common.rotation_group.rotation += 10
    else:
        selection_rotated_right(board)
        common.rotation_direction = None

        for cell in cells_being_rotated(board):
            if cell is not None:
                cell.visible = True

        clear_to_delete(board)
        mark_and_delete(board, panel)


def rotate_selection_left(board, panel):
    for cell in cells_being_rotated(board):
        if cell is not None:
            cell.visible = False

    if common.rotation_group.rotation > -90:
        common.rotation_group.rotation -= 10
    else:
        selection_rotated_left(board)
        common.rotation_direction = None

        for cell in cells_being_rotated(board):
            if cell is not None:
                cell.visible = True

        clear_to_delete(board)
        mark_and_delete(board, panel)


def clear_to_delete(board):
    for row in range(board.cells_in_row):
        for col in range(board.cells_in_row):
            cell = common.matrix[row][col]
            if cell is not None:
                common.matrix[row][col].clear_to_delete()


def mark_and_delete(board, panel):
    board.cells_to_drop_down = []
    deselect_all_cells()
    cells_in_types = [0, 0, 0, 0, 0, 0]
    warn = False

    finished = False
    while not finished:
        """Find 3 or more cells of the same type placed side by side and mark them to delete
           (in all rows for now, to be changed when tested)"""
        for row in range(board.cells_in_row):
            for col in range(1, board.cells_in_row - 1):
                cell = common.matrix[row][col]
                cell_before = common.matrix[row][col - 1]
                cell_after = common.matrix[row][col + 1]
                if cell is not None and cell_before is not None and cell_after is not None:
                    if cell.type == cell_before.type and common.matrix[row][col].type == cell_after.type:
                        cell.mark_to_delete()
                        cell_before.mark_to_delete()
                        cell_after.mark_to_delete()

        """Find and delete cells marked to delete in the 1st row containing such"""
        r = None
        for row in range(board.cells_in_row):
            for col in range(board.cells_in_row):
                if common.matrix[row][col] is not None and common.matrix[row][col].to_delete:
                    r = row
                    common.cells_deleted = True
                    break
            if r is not None:
                break

        if r is not None:
            """Delete marked cells in row given from the display batch and from the matrix"""
            for col in range(board.cells_in_row):
                if common.matrix[r][col] is not None:
                    if common.matrix[r][col].to_delete:
                        common.matrix[r][col].batch = None
                        common.matrix[r][col] = None

        """Now we need to find the first row with empty cell(s)"""
        row = first_with_empty_cells(board)[1]  # first row w/ empty cells and cells above
        if row is not None:
            columns = columns_to_drop(board, row)  # *** We'll be dropping these columns before re-checking the board!
            mark_to_drop(board, columns, row)
            break
        else:
            finished = True
            summary_row = first_with_empty_cells(board)[0]

        cells_left = 0
        for row in range(board.cells_in_row):
            for col in range(board.cells_in_row):
                cell = common.matrix[row][col]
                if cell is not None:
                    cells_in_types[cell.type] += 1
                    cells_left += 1

        common.summary_backup = common.summary.copy()
        common.summary = []
        for left in cells_in_types:
            if left >= 3 or left == 0:
                common.summary.append(str(left))
            else:
                common.summary.append(str(left) + ":(")
                warn = True
        if summary_row is not None and common.cells_deleted:
            common.summary_bar.new(common.board, summary_row)
            common.summary_bar.refresh(common.summary[0], common.summary[1], common.summary[2],common.summary[3], common.summary[4], common.summary[5])
            if warn:
                common.fx.play("warning")
            common.summary_bar.show()

        if cells_left == 0:
            common.game_state.playing = False
            player_save_results(panel)
            player_load()


def first_with_empty_cells(board):
    """
    :param board:
    :return: tuple of (first row w/ empty cells, first row w/ empty cells and some cells above)
    """
    first_at_all = None
    first_with_cells_above = None
    for row in range(board.cells_in_row):
        for col in range(board.cells_in_row):
            if common.matrix[row][col] is None:
                if first_at_all is None:  # mark at the 1st iteration only
                    first_at_all = row
                for r in range(row, board.cells_in_row):  # Check if there are any cells above
                    if common.matrix[r][col] is not None:
                        first_with_cells_above = row
    return first_at_all, first_with_cells_above


def columns_to_drop(board, marked_row):
    """list of indices of columns placed above empty spots of marked_row"""
    columns = []
    for col in range(board.cells_in_row):
        if common.matrix[marked_row][col] is None:
            columns.append(col)
    return columns


"""
The rotation code (2 functions below) could probably be shortened. However, everything I had written would give 
unexpected results. That's why I decided to put on readability.
"""


def selection_rotated_left(board):
    if board.sel_0 is not None and board.sel_1 is not None and board.sel_2 is not None and board.sel_3 is not None:
        """All 4 cells full, just rotate"""
        board.sel_0.move_right(board)
        board.sel_1.move_up(board)
        board.sel_2.move_down(board)
        board.sel_3.move_left(board)
    else:
        if board.sel_0 is None:
            print("board.sel_0 should never be None!")

        elif board.sel_1 is None:
            print("board.sel_1 should never be None!")

        elif board.sel_2 is None:
            clear_at = board.sel_0.row, board.sel_0.col
            board.sel_3.move_left(board)
            board.sel_1.move_up(board)
            board.sel_0.move_right(board)
            common.matrix[clear_at[0]][clear_at[1]] = None

        elif board.sel_3 is None:
            clear_at = board.sel_2.row, board.sel_2.col
            board.sel_1.move_up(board)
            board.sel_0.move_right(board)
            board.sel_2.move_down(board)
            common.matrix[clear_at[0]][clear_at[1]] = None

    if common.scores[common.level] is None:
        common.scores[common.level] = 0
    common.scores[common.level] += 1


def selection_rotated_right(board):
    if board.sel_0 is not None and board.sel_1 is not None and board.sel_2 is not None and board.sel_3 is not None:
        board.sel_0.move_up(board)
        board.sel_1.move_left(board)
        board.sel_2.move_right(board)
        board.sel_3.move_down(board)
    else:
        if board.sel_0 is None:
            print("board.sel_0 should never be None!")

        elif board.sel_1 is None:
            print("board.sel_1 should never be None!")

        elif board.sel_2 is None:
            clear_at = board.sel_3.row, board.sel_3.col
            board.sel_0.move_up(board)
            board.sel_1.move_left(board)
            board.sel_3.move_down(board)
            common.matrix[clear_at[0]][clear_at[1]] = None

        elif board.sel_3 is None:
            clear_at = board.sel_1.row, board.sel_1.col
            board.sel_2.move_right(board)
            board.sel_0.move_up(board)
            board.sel_1.move_left(board)
            common.matrix[clear_at[0]][clear_at[1]] = None

    common.scores[common.level] += 1


def mark_to_drop(board, columns, target_row):
    """Find last cell of each column"""
    board.last_cells_in_columns = []
    for col in columns:
        for row in range(target_row + 1, board.cells_in_row):
            """Wow, that's gonna be a little bit screwed up condition!"""
            if row < board.cells_in_row - 1 and common.matrix[row + 1][col] is None or row == board.cells_in_row - 1:
                val = col, row
                board.last_cells_in_columns.append(val)
                break

    """Now we know which columns to scroll down, and at which cells on to become None when columns dropped"""
    board.cells_to_drop_down = []  # this list hold cells that need to be dropped down
    for item in board.last_cells_in_columns:
        col = item[0]
        for row in range(target_row + 1, item[1] + 1):
            cell = common.matrix[row][col]
            if cell is not None:
                board.cells_to_drop_down.append(common.matrix[row][col])

    common.scrolling = True
    common.scroll_counter = 0


def cells_dropped(board):
    for cell in board.cells_to_drop_down:
        cell.move_down(board)

    for item in board.last_cells_in_columns:
        common.matrix[item[1]][item[0]] = None

    common.scrolling = False


def deselect_all_cells():
    for cell in common.cells_list:
        cell.selected = False


def cells_being_rotated(board):
    return [board.sel_0, board.sel_1, board.sel_2, board.sel_3]


def backup(board):
    """For simplicity we'll store undo data in identical 2-dimensional list as the matrix itself"""
    common.backup_matrix = [[0 for c in range(board.cells_in_row)] for r in range(board.cells_in_row)]
    common.backup_values = []  # linear list to store attributes of each cell
    for row in range(board.cells_in_row):
        for col in range(board.cells_in_row):
            cell = common.matrix[row][col]
            common.backup_matrix[row][col] = cell
            values = None  # also store None, to preserve the list order
            if cell is not None:
                values = cell.row, cell.col, cell.x, cell.y, cell.selected, cell.to_delete
            common.backup_values.append(values)


def restore(board):
    if common.backup_matrix is not None:
        idx = 0  # Position on the list we stored cell attributes to
        for row in range(board.cells_in_row):
            for col in range(board.cells_in_row):
                cell = common.backup_matrix[row][col]
                common.matrix[row][col] = cell
                if cell is not None:
                    cell.batch = common.cells_batch
                    values = common.backup_values[idx]
                    cell.row = values[0]
                    cell.col = values[1]
                    cell.x = values[2]
                    cell.y = values[3]
                    cell.selected = values[4]
                    cell.to_delete = values[5]
                idx += 1
        common.backup_matrix = None
        common.scores[common.level] -= 1

    if common.summary:
        for i in range(len(common.summary_backup)):
            common.summary[i] = common.summary_backup[i]
        common.summary_bar.refresh(common.summary[0], common.summary[1], common.summary[2],common.summary[3], common.summary[4], common.summary[5])
        common.summary_bar.show()


def player_load():
    exists = False
    common.app_dir = pyglet.resource.get_settings_path(common.app_name)
    common.player_filename = os.path.join(common.app_dir, common.player_filename)
    if not os.path.exists(common.player_filename):
        print(str(common.player_filename) + " file not found, creating Anonymous player...")
        common.player = Player("Anonymous", None, [None, None, None, None, None, None])
        with open(common.player_filename, 'wb') as output:
            pickle.dump(common.player, output, pickle.HIGHEST_PROTOCOL)
    else:
        exists = True

    with open(common.player_filename, 'rb') as input_data:
        common.player = pickle.load(input_data)
        for i in range(len(common.scores)):
            common.scores[i] = common.player.scores[i]
        common.player.online = common.ONLINE
    return exists


def player_save_results(panel):
    """Level finished successfully"""
    unlocked = None
    if common.player.scores[common.level] is None:
        unlocked = common.level + 1 + 1  # And the next level is... (in human-readable 1-6 range)

    if common.player.scores[common.level] is None or common.player.scores[common.level] is not None and common.scores[
            common.level] < common.player.scores[common.level]:  # First or best score on this level

        """Update score for this level, save all"""
        common.player.scores[common.level] = common.scores[common.level]
        player_save()

    common.game_state.intro = True
    if unlocked:
        if unlocked < 7:
            common.fx.play("unlocked")
            intro_level_unlocked(unlocked)  # Next level unlocked, notify!
        else:
            common.fx.play("unlocked")
            intro_sunglasses()  # No new level to unlock
    else:
        common.fx.play("level")
        intro_level_finished(common.level + 1, common.scores[common.level])  # Just show the result

    # Save to the cloud IF ANY BETTER RESULT ACHIEVED
    if common.player.name != "Anonymous" and sync_needed():
        player_sync(common.player.name, common.player.password)


def player_save():
    with open(common.player_filename, 'wb') as output:
        pickle.dump(common.player, output, pickle.HIGHEST_PROTOCOL)


def update_scores(panel):
    panel.update_score_labels()
    update_levels_display(panel)


def update_levels_display(panel):
    panel.set_lock_state(0, False)
    if common.player.scores[0] is not None:
        panel.set_lock_state(1, False)
    if common.player.scores[1] is not None:
        panel.set_lock_state(2, False)
    if common.player.scores[2] is not None:
        panel.set_lock_state(3, False)
    if common.player.scores[3] is not None:
        panel.set_lock_state(4, False)
    if common.player.scores[4] is not None:
        panel.set_lock_state(5, False)


def intro_label(board, message):
    label = pyglet.text.Label(
        message,
        width=int(board.cell_dimension * 3),
        multiline=True,
        align='center',
        color=(255, 255, 255, 255),
        font_name='DejaVu Sans Mono',
        font_size=36 * board.scale,
        x=board.columns[3], y=board.rows[2],
        anchor_x='center', anchor_y='center')
    return label


def intro_hello(message):
    common.intro_sprite = HelloAnimation(common.board)
    common.intro_message = intro_label(common.board, message)


def intro_level_unlocked(level):
    common.intro_sprite = UnlockAnimation(common.board)
    common.intro_message = intro_label(common.board, common.lang["intro_level_unlocked"].format(level))


def intro_level_finished(level, moves):
    common.intro_sprite = FinishedAnimation(common.board)
    common.intro_message = intro_label(common.board, common.lang["intro_level_in"].format(level, moves))


def intro_sunglasses():
    common.intro_sprite = SunglassesAnimation(common.board)
    common.intro_message = intro_label(common.board, common.lang["intro_incredible"])


def overwrite_lang(localization):
    if os.path.isfile("languages/" + localization):
        print("Reading lang " + localization)
        config = configparser.ConfigParser()
        with open('languages/' + localization) as f:
            config.read_file(f)

        if config.has_section("lang"):
            options = config.options("lang")
            for key in options:
                value = config.get("lang", key)
                common.lang[key] = value
    else:
        print("Couldn't find translation for " + localization)

