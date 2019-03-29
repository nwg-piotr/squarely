#!/usr/bin/env python
# _*_ coding: utf-8 _*_

"""
A puzzle game which utilizes the python-pyglet library

Author: Piotr Miller
e-mail: nwg.piotr@gmail.com
Website: http://nwg.pl
Project: https://github.com/nwg-piotr/squarely
License: GPL3

Dependencies (Arch Linux): python-pyglet, ' python-requests', optionally avbin7 (AUR) - to play compressed sound
"""
from game_objects import *
from tools import *
from text_tools import *
from cloud_tools import player_login, player_sync, top_ten_update
from pyglet.window import key
import locale

import datetime


def main():
    pyglet.options['audio'] = ('openal', 'pulse', 'silent')

    """OS-dependent preferences location (in Linux: ~/.config/common.app_name/)"""
    common.app_dir = pyglet.resource.get_settings_path(common.app_name)
    if not os.path.exists(common.app_dir):
        os.makedirs(common.app_dir)

    common.rc = RuntimeConfig()

    """Let's preload English dictionary and overwrite with localized values if found"""
    common.lang = Language('en_EN')
    """Running with LC_ALL=C will return (None, None)"""
    localization = locale.getlocale()[0] if locale.getlocale()[0] is not None else 'en_EN'
    if localization != 'en_EN':
        overwrite_lang(localization)

    """Create resources"""
    if os.path.isfile('images/cells-' + str(common.rc.cells_set) + '.png'):
        create_cells_bitmaps('images/cells-' + str(common.rc.cells_set) + '.png')
    else:
        create_cells_bitmaps('images/cells-0.png')
    common.fx = Sounds()

    """
    Load stored player data or create new file if not found; 
    The player_load() function returns True if player exists: set the hello message accordingly.
    """
    hello_msg = common.lang["intro_wb"] if player_load() else common.lang["intro_welcome"]
    print(common.player.name, common.player.scores)

    """The GameBoard class calculates and holds many values used by other classes and MUST be instantiated first"""
    common.board = GameBoard(6 + common.level * 3)  # 6 + n * 3

    common.summary_batch = pyglet.graphics.Batch()
    common.summary_bar = SummaryBar(common.board, 0, 0)

    window = create_game_window(common.board)
    cursor_hand = window.get_system_mouse_cursor(window.CURSOR_HAND)
    cursor_default = window.get_system_mouse_cursor(window.CURSOR_DEFAULT)

    common.intro_batch = pyglet.graphics.Batch()
    intro_bcg = IntroRotator(common.board)

    panel = Panel(common.board)  # Control panel class. Let's pre-select the first not-yet-finished level
    for i in range(len(common.player.scores)):
        if common.player.scores[i] is None:
            panel.selected_level = i
            common.level = i
            panel.level_select(i)
            break
    update_scores(panel)

    common.player.online = common.OFFLINE
    if common.player.name != 'Anonymous':
        player_login(common.player.name, common.player.password)

    common.player_dialog_batch = pyglet.graphics.Batch()
    common.player_dialog = PlayerDialog(window, common.board)
    common.player_confirmation = PlayerConfirmation(common.board)

    common.top10_content = common.lang["top_ten_loading"]
    common.top_list_batch = pyglet.graphics.Batch()
    common.top_list = TopList(common.board)

    if common.intro:
        intro_hello(hello_msg)
        common.fx.play(panel, "hello")

    @window.event
    def on_draw():
        window.clear()
        panel.draw()

        if common.label is not None:
            common.label.draw()

        if common.playing:
            if common.rc.background_draw:
                intro_bcg.draw()

            if common.cells_batch is not None:
                common.cells_batch.draw()

            if common.rotation_group is not None and common.rotation_direction is not None:
                common.rotation_group.draw()

            if not common.scrolling:
                if common.cursor_in and common.cursor_in_board and common.board.selection_made:
                    common.selector.draw()

            if common.summary_bar is not None and common.summary_bar.visible:
                common.summary_bar.draw()

        elif common.intro:
            common.intro_batch.draw()
            if common.intro_sprite is not None:
                common.intro_sprite.draw()
            if common.intro_message is not None:
                common.intro_message.draw()

        elif common.dialog:
            intro_bcg.draw()

        if common.dialog:
            common.player_dialog_batch.draw()
            if common.player_confirmation is not None and common.player_confirmation.visible:
                common.player_confirmation.draw()

        if common.top10:
            intro_bcg.draw()
            common.top_list_batch.draw()

    @window.event
    def on_mouse_enter(x, y):
        common.cursor_in = True

    @window.event
    def on_mouse_leave(x, y):
        common.board.message = None
        common.cursor_in = False
        deselect_all_cells()

    @window.event
    def on_mouse_motion(x, y, dx, dy):
        common.cursor_in_board = y >= common.board.grid_start_y

        if common.cursor_in_board:
            common.summary_bar.hide()

            if common.player_dialog.is_open:
                common.player_dialog.refresh_label(x, y)

            if common.rotation_direction is None:

                counter = 0
                if common.board.sel_0 is not None:
                    counter += 1
                if common.board.sel_1 is not None:
                    counter += 1
                if common.board.sel_2 is not None:
                    counter += 1
                if common.board.sel_3 is not None:
                    counter += 1

                """common.board.sel_0 and common.board.sel_1 happened to be selected, that should not happen ever!"""
                common.board.selection_made = counter >= 3 and common.board.sel_0 is not None and common.board.sel_1 is not None
                if common.board.selection_made:
                    common.board.message = "Left/right click to rotate"
                else:
                    common.board.message = None

                window.set_mouse_cursor(cursor_hand)

                row, column = 0, 0
                for i in range(len(common.board.rows) - 1):
                    if y < common.board.rows[i + 1]:
                        continue
                    else:
                        row = i
                for i in range(len(common.board.columns) - 1):
                    if x < common.board.columns[i + 1]:
                        continue
                    else:
                        column = i

                if common.selector is not None:
                    common.selector.move(common.board, row, column)
                    select_highlighted_cells(common.board, row, column)

        else:
            common.board.message = None
            window.set_mouse_cursor(cursor_default)
            common.board.selection_made = False
            deselect_all_cells()

            panel.check_selection(x, y)

    @window.event
    def on_mouse_release(x, y, button, modifiers):
        common.cells_deleted = False

        if common.cursor_in_board and common.playing:
            if common.board.selection_made:
                if button == pyglet.window.mouse.LEFT:
                    common.fx.play(panel, "rotate")
                    backup(common.board)
                    common.rotation_group = RotationGroup(common.board)
                    common.rotation_direction = "left"
                    deselect_all_cells()
                    common.board.selection_made = False

                elif button == pyglet.window.mouse.RIGHT:
                    common.fx.play(panel, "rotate")
                    backup(common.board)
                    common.rotation_group = RotationGroup(common.board)
                    common.rotation_direction = "right"
                    deselect_all_cells()
                    common.board.selection_made = False

        else:
            if panel.button_start.selected:
                if common.player_dialog.is_open:
                    common.player_dialog.close()
                if common.top_list.is_open:
                    common.top_list.hide()
                common.level = panel.selected_level
                common.fx.play(panel, "start")
                new_game()
                mark_and_delete(common.board, panel)

            elif panel.button_undo.selected:
                common.fx.play(panel, "undo")
                restore(common.board)

            elif panel.button_up.selected:
                common.fx.play(panel, "key")
                panel.level_up()

            elif panel.button_down.selected:
                if panel.selected_level > 0:
                    common.fx.play(panel, "key")
                    panel.level_down()

            elif panel.button_music.selected:
                common.fx.play(panel, "key")
                common.rc.switch_music(panel)
                common.rc.save()
                common.rc.load()

            elif panel.button_sound.selected:
                common.fx.play(panel, "key")
                common.rc.switch_sounds(panel)
                common.rc.save()
                common.rc.load()

            elif panel.button_name.selected:
                if not common.player_dialog.is_open:
                    common.player_dialog.open()
                else:
                    common.player_dialog.close()

            elif panel.button_cloud.selected:
                if common.player.name != 'Anonymous':
                    player_sync(common.player.name, common.player.password)

            elif panel.button_2.selected:
                if not common.top_list.visible:
                    top_ten_update(common.top_list.label)
                    common.top_list.show()
                else:
                    common.top_list.hide()

        if common.player_dialog.is_open:
            common.player_dialog.click(panel, x, y)

        if common.top_list.is_open:
            common.top_list.click(x, y)

    @window.event
    def on_mouse_scroll(x, y, scroll_x, scroll_y):
        if common.summary_bar is not None and common.summary_bar.y > 0:
            common.summary_bar.show()

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == key.H:
            if common.summary_bar is not None:
                common.summary_bar.show()

    def update(dt):
        if common.intro or common.dialog or common.top10 or common.playing and common.rc.background_draw and common.rc.background_rotate:
            # We won't say "Welcome back" to anonymous players!
            if isinstance(common.intro_sprite, HelloAnimation):  # Are we still in the Hello animation?
                common.intro_message.text = common.lang["intro_wb"] if common.player.name != 'Anonymous' else \
                    common.lang["intro_welcome"]

            if intro_bcg.rotation < 360:
                intro_bcg.rotation += 0.25
            else:
                intro_bcg.rotation = 0

        if common.rotation_direction == "right":
            rotate_selection_right(common.board, panel)
        elif common.rotation_direction == "left":
            rotate_selection_left(common.board, panel)

        update_scores(panel)

        if common.scrolling:
            common.scroll_counter += common.board.scroll_step
            if common.scroll_counter >= common.board.cell_dimension:
                cells_dropped(common.board)
                common.fx.play(panel, "drop")
                deselect_all_cells()
                clear_to_delete(common.board)
                mark_and_delete(common.board, panel)
            else:
                for cell in common.board.cells_to_drop_down:
                    cell.y -= common.board.scroll_step

        if common.top_list.visible:
            common.top_list.refresh(common.top10_content)

        common.label = pyglet.text.Label(
            str(int(pyglet.clock.get_fps())),
            font_name='DejaVu Sans Mono',
            font_size=10,
            x=10, y=10,
            anchor_x='center', anchor_y='center')

    pyglet.clock.schedule_interval(update, 0.03)
    pyglet.app.run()


def create_game_window(board):
    window = pyglet.window.Window()
    window.width = board.window_width
    window.height = board.window_height
    window.set_location(board.window_pos_x, board.window_pos_y)
    window.set_caption("squarely")

    return window


def new_game():
    player_load()
    for i in range(len(common.cells_list)):
        common.cells_list[i].delete()

    common.board = GameBoard(6 + common.level * 3)
    common.cells_batch = create_cells(common.board)
    common.selector = Selector(common.board)
    common.backup_matrix = None
    common.backup_values = None
    common.scores[common.level] = 0

    common.summary_bar.hide()
    common.intro = False
    common.playing = True
    common.summary_bar.y = 0  # To mark that it has not yet been shown since the game started (still keeps old values!)


if __name__ == "__main__":
    main()
