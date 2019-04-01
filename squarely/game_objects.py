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
from pyglet.gl import *
from pyglet import image
import configparser
import os
import common
from text_tools import *
import hashlib
import pickle
from cloud_tools import player_create, player_delete, player_login


class GameBoard(object):
    """
    This class calculates and holds window dimensions and placement, and all the game board related values
    """

    def __init__(self, cells_in_row):

        total_cells = cells_in_row * cells_in_row
        print("total_cells = " + str(total_cells))

        full_groups_capacity = cells_in_row * cells_in_row // 36
        print("full_groups_capacity = " + str(full_groups_capacity))

        cells_to_fit_as_full_groups = full_groups_capacity * 36
        print("cells_to_fit_as_full_groups = " + str(cells_to_fit_as_full_groups))

        cells_left = total_cells - cells_to_fit_as_full_groups
        print("cells_left = " + str(cells_left))

        groups_to_repeat = int(cells_left / 3)
        print("groups_to_repeat = " + str(groups_to_repeat))

        self.cell_resources = []

        for c in range(6):
            self.cell_resources.append(6 * full_groups_capacity)
        for i in range(groups_to_repeat):
            self.cell_resources[i] = self.cell_resources[i] + 3

        print("cell_resources = " + str(self.cell_resources) + "\n")

        platform = pyglet.window.get_platform()
        display = platform.get_default_display()
        screen = display.get_default_screen()
        self.window_height = int(screen.height * 0.8)
        self.window_width = int((self.window_height / 8) * 6)

        """
        This is why this class must me instantiated first!
            216 = source base square 
            23 = source cell margin
        """
        self.scale = self.window_width / (216 * cells_in_row + 23 * 2)

        self.window_pos_x = int((screen.width - self.window_width) / 2)
        self.window_pos_y = int((screen.height - self.window_height) / 2)
        self.base = int(self.window_height / 8)  # base board square dimension

        self.cells_in_row = cells_in_row

        self.margin = 23 / cells_in_row * 6 * self.scale  # 23 = source cell margin; 6 = base squares nb
        self.grid_start_y = self.base * 2 + self.margin  # board grid starts above the panel

        self.board_width = self.window_width - self.margin * 2
        self.cell_dimension = self.board_width / self.cells_in_row  # board grid square dimension
        self.btn_dimension = self.board_width / 6  # panel button square dimension

        self.scroll_step = int(self.cell_dimension) / 6

        self.columns = []  # list of x coordinates of each board column
        for row in range(self.cells_in_row):
            self.columns.append(self.margin + row * self.cell_dimension)

        self.rows = []  # list of y coordinates of each board row
        for col in range(self.cells_in_row):
            self.rows.append(self.grid_start_y + col * self.cell_dimension)

        """Selected cells"""
        self.sel_0 = None
        self.sel_1 = None
        self.sel_2 = None
        self.sel_3 = None

        print("Rows: " + str(self.rows))
        print("Columns: " + str(self.columns) + "\n")

        self.selection_made = False

        self.cells_to_drop_down = []
        self.last_cells_in_columns = []


class Cell(pyglet.sprite.Sprite):
    def __init__(self, board, cell_type, row, column):
        bitmap = common.cell_bitmaps[cell_type]
        super().__init__(bitmap)

        self.type = cell_type
        self.scale = board.scale

        self.row = row
        self.col = column

        self.y = board.rows[self.row]
        self.x = board.columns[self.col]

        self.selected = False

        self.to_delete = False

    def select(self):
        self.selected = True

    def move_up(self, board):
        self.row = self.row + 1
        common.matrix[self.row][self.col] = self
        self.y = board.rows[self.row]

    def move_left(self, board):
        self.col = self.col - 1
        common.matrix[self.row][self.col] = self
        self.x = board.columns[self.col]

    def move_down(self, board):
        self.row = self.row - 1
        common.matrix[self.row][self.col] = self
        self.y = board.rows[self.row]

    def move_right(self, board):
        self.col = self.col + 1
        common.matrix[self.row][self.col] = self
        self.x = board.columns[self.col]

    def mark_to_delete(self):
        self.to_delete = True
        # self.opacity = 70

    def clear_to_delete(self):
        self.to_delete = False
        # self.opacity = 255


class Selector(pyglet.sprite.Sprite):
    def __init__(self, board):
        super().__init__(image.load("images/selector.png"))

        self.scale = board.scale * 2
        self.row = 0
        self.column = 0

    def move(self, board, row, column):
        self.row = row
        self.column = column
        self.y = board.rows[self.row]
        self.x = board.columns[self.column]


class SummaryBar(pyglet.sprite.Sprite):
    def __init__(self, board, x, y):
        bcg = pyglet.image.load("images/bar-bcg.png").get_texture()
        bcg.width = board.base * 4
        bcg.height = int(board.base / 3)
        self.joint_image = pyglet.image.Texture.create(2592, 216)
        self.joint_image.blit_into(common.cell_bitmaps[0], 0, 0, 0)
        self.joint_image.blit_into(common.cell_bitmaps[1], 429 * 1, 0, 0)
        self.joint_image.blit_into(common.cell_bitmaps[2], 429 * 2, 0, 0)
        self.joint_image.blit_into(common.cell_bitmaps[3], 429 * 3, 0, 0)
        self.joint_image.blit_into(common.cell_bitmaps[4], 429 * 4, 0, 0)
        self.joint_image.blit_into(common.cell_bitmaps[5], 429 * 5, 0, 0)

        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        self.joint_image.width = board.base * 4
        self.joint_image.height = board.base // 3
        super().__init__(bcg, subpixel=True)

        self.x = board.base
        self.y = y
        self.batch = None

        step = self.joint_image.width / 12
        self.l0 = self.lbl("0", step, self.image.height // 2)
        self.l1 = self.lbl("0", step * 3, self.image.height // 2)
        self.l2 = self.lbl("0", step * 5, self.image.height // 2)
        self.l3 = self.lbl("0", step * 7, self.image.height // 2)
        self.l4 = self.lbl("0", step * 9, self.image.height // 2)
        self.l5 = self.lbl("0", step * 11, self.image.height // 2)
        self.visible = False

    def draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.image.blit(self.x, self.y)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.joint_image.blit(self.x, self.y)
        self.l0.draw()
        self.l1.draw()
        self.l2.draw()
        self.l3.draw()
        self.l4.draw()
        self.l5.draw()

    def new(self, board, row):
        self.y = board.rows[row] + board.margin
        self.visible = False

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def refresh(self, c0, c1, c2, c3, c4, c5):
        self.l0.text = c0
        self.l0.y = self.y + self.image.height // 2
        self.l1.text = c1
        self.l1.y = self.y + self.image.height // 2
        self.l2.text = c2
        self.l2.y = self.y + self.image.height // 2
        self.l3.text = c3
        self.l3.y = self.y + self.image.height // 2
        self.l4.text = c4
        self.l4.y = self.y + self.image.height // 2
        self.l5.text = c5
        self.l5.y = self.y + self.image.height // 2

    def lbl(self, text, x, y):
        label = pyglet.text.Label(
            text,
            font_name='DejaVu Sans Mono',
            font_size=int(24 * common.board.scale),
            x=self.x + x, y=y,
            anchor_x='left', anchor_y='center')
        return label


class RotationGroup(pyglet.sprite.Sprite):
    def __init__(self, board):

        super().__init__(self.join_images(board))

        self.image.anchor_x = self.image.width // 2
        self.image.anchor_y = self.image.height // 2

        """Either the board.sel_1 or board.sel_13cell should always be full"""
        if board.sel_0 is not None:
            self.x = board.columns[board.sel_0.col + 1]
            self.y = board.rows[board.sel_0.row + 1]
        else:
            self.x = board.columns[board.sel_3.col]
            self.y = board.rows[board.sel_3.row]

        self.rotation = 0

    def join_images(self, board):
        img0 = pyglet.image.load("images/cell-empty.png")
        img1 = pyglet.image.load("images/cell-empty.png")
        img2 = pyglet.image.load("images/cell-empty.png")
        img3 = pyglet.image.load("images/cell-empty.png")
        joint_image = pyglet.image.Texture.create(216 * 2, 216 * 2)
        if board.sel_0 is not None:
            img0 = common.cell_bitmaps[board.sel_0.type]
        if board.sel_1 is not None:
            img1 = common.cell_bitmaps[board.sel_1.type]
        if board.sel_2 is not None:
            img2 = common.cell_bitmaps[board.sel_2.type]
        if board.sel_3 is not None:
            img3 = common.cell_bitmaps[board.sel_3.type]
        joint_image.blit_into(img0, 0, 0, 0)
        joint_image.blit_into(img1, 216, 0, 0)
        joint_image.blit_into(img2, 0, 216, 0)
        joint_image.blit_into(img3, 216, 216, 0)

        texture = joint_image.get_texture()
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        texture.width = board.cell_dimension * 2
        texture.height = board.cell_dimension * 2

        return texture


class IntroRotator(pyglet.sprite.Sprite):
    def __init__(self, board):
        super().__init__(image.load("images/intro-rotator.png"))

        self.image.width = board.base * 6
        self.image.height = board.base * 6
        self.image.anchor_x = self.image.width // 2
        self.image.anchor_y = self.image.height // 2
        self.x = board.base * 3
        self.y = board.base * 5
        self.batch = common.intro_batch


class UnlockAnimation(pyglet.sprite.Sprite):
    def __init__(self, board):
        frames_source = image.load("images/unlock-frames.png")
        sequence = pyglet.image.ImageGrid(frames_source, 1, 6)
        animation = (pyglet.image.Animation.from_image_sequence(sequence, 0.24, True))

        super().__init__(animation)

        self.x = board.margin + board.base
        self.y = board.margin + board.base * 3
        self.scale = board.scale * 2


class FinishedAnimation(pyglet.sprite.Sprite):
    def __init__(self, board):
        frames_source = image.load("images/smile-frames.png")
        sequence = pyglet.image.ImageGrid(frames_source, 1, 8)
        animation = (pyglet.image.Animation.from_image_sequence(sequence, 0.24, True))

        super().__init__(animation)

        self.x = board.margin + board.base
        self.y = board.margin + board.base * 3
        self.scale = board.scale * 2


class HelloAnimation(pyglet.sprite.Sprite):
    def __init__(self, board):
        frames_source = image.load("images/hello-frames.png")
        sequence = pyglet.image.ImageGrid(frames_source, 1, 9)
        animation = (pyglet.image.Animation.from_image_sequence(sequence, 0.34, False))

        super().__init__(animation)

        self.x = board.margin + board.base
        self.y = board.margin + board.base * 3
        self.scale = board.scale * 2


class SunglassesAnimation(pyglet.sprite.Sprite):
    def __init__(self, board):
        frames_source = image.load("images/sunglasses-frames.png")
        sequence = pyglet.image.ImageGrid(frames_source, 1, 6)
        animation = (pyglet.image.Animation.from_image_sequence(sequence, 0.24, False))

        super().__init__(animation)

        self.x = board.margin + board.base
        self.y = board.margin + board.base * 3
        self.scale = board.scale * 2


class PlayerConfirmation(pyglet.sprite.Sprite):
    def __init__(self, board):
        frames_source = image.load("images/player-confirm.png")
        sequence = pyglet.image.ImageGrid(frames_source, 1, 2)
        animation = (pyglet.image.Animation.from_image_sequence(sequence, 0.5, True))
        super().__init__(animation)
        self.x = board.base * 2
        self.y = board.base * 4
        self.scale = board.scale * 1.04
        self.visible = False

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False


class TopList(pyglet.sprite.Sprite):
    def __init__(self, board):
        super().__init__(image.load("images/top-list.png"))

        self.scale = board.scale
        self.x = board.columns[0]
        self.y = board.rows[0]
        self.visible = False
        self.batch = common.top_list_batch

        self.old_playing = False
        self.old_intro = False
        self.old_dialog = False
        self.old_settings = False

        self.is_open = False

        self.close_area = self.x + self.width - board.base, self.y + self.height - board.base, self.x + self.width, self.y + self.height

        self.label = pyglet.text.Label(
            common.lang["top_ten_loading"],
            font_name='DejaVu Sans Mono',
            color=(255, 255, 255, 255),
            font_size=int(24 * self.scale),
            width=500,
            multiline=True,
            align="left",
            x=self.x + board.cell_dimension // 2, y=self.y + self.width - board.cell_dimension // 2,
            anchor_x='left', anchor_y='top', batch=self.batch)

    def click(self, x, y):
        if self.is_in(x, y, self.close_area):
            self.hide()

    def is_in(self, x, y, area):
        return area[0] < x < area[2] and area[1] < y < area[3]

    def refresh(self, text):
        self.label.text = text

    def show(self):
        if common.player_dialog.is_open:
            common.player_dialog.close()

        self.label.text = common.top10_content

        self.old_playing = common.is_playing
        self.old_intro = common.is_intro
        self.old_dialog = common.is_dialog
        self.old_settings = common.is_settings
        common.is_playing = False
        common.is_intro = False
        common.is_dialog = False
        common.is_settings = False

        self.visible = True
        self.is_open = True
        common.top10 = True

    def hide(self):
        common.is_playing = self.old_playing
        common.is_intro = self.old_intro
        common.is_dialog = self.old_dialog
        common.is_settings = self.old_settings
        common.top10 = False

        self.visible = False
        self.is_open = False


class SettingsDialog(object):
    def __init__(self, window, board):
        self.old_playing = False
        self.old_intro = False
        self.old_dialog = False
        self.old_top10 = False

        self.window = window
        self.board = board

        img_background = pyglet.image.load('images/settings-bcg.png')
        self.img_checkbox_unchecked = pyglet.image.load('images/checkbox-unchecked.png')
        self.img_checkbox_checked = pyglet.image.load('images/checkbox-checked.png')
        img_go = pyglet.image.load('images/btn-go.png')

        frames_source = image.load("images/btn-go-free.png")
        sequence = pyglet.image.ImageGrid(frames_source, 1, 2)
        self.go_animation0 = (pyglet.image.Animation.from_image_sequence(sequence, 0.5, True))

        frames_source = image.load("images/btn-go-clicked.png")
        sequence = pyglet.image.ImageGrid(frames_source, 1, 2)
        self.go_animation1 = (pyglet.image.Animation.from_image_sequence(sequence, 0.5, True))

        self.btn_x = board.base * 5
        self.y_step = board.base / 2
        self.label_x = board.base * 3

        self.batch = common.settings_batch
        self.visible = False
        self.is_open = False

        self.background = pyglet.sprite.Sprite(img_background)
        self.background.scale = board.scale
        self.background.x = board.columns[0]
        self.background.y = board.rows[0]
        self.background.batch = self.batch

        self.draw_bcg_checkbox = pyglet.sprite.Sprite(
            self.img_checkbox_checked if common.settings.background_draw else self.img_checkbox_unchecked)
        self.draw_bcg_checkbox.scale = board.scale
        self.draw_bcg_checkbox.x = self.btn_x
        self.draw_bcg_checkbox.y = board.rows[0] + self.y_step * 7
        self.draw_bcg_checkbox.batch = self.batch
        self.v_middle = self.draw_bcg_checkbox.height // 2  # should be suitable to reuse
        self.draw_bcg_label = self.add_label(common.lang["settings_draw_background"],
                                             self.draw_bcg_checkbox.y + self.v_middle)
        self.draw_bcg_checkbox.area = self.draw_bcg_checkbox.x, self.draw_bcg_checkbox.y, self.draw_bcg_checkbox.x + self.draw_bcg_checkbox.width, self.draw_bcg_checkbox.y + self.draw_bcg_checkbox.height

        self.rotate_bcg_checkbox = pyglet.sprite.Sprite(
            self.img_checkbox_checked if common.settings.background_rotate else self.img_checkbox_unchecked)
        self.rotate_bcg_checkbox.scale = board.scale
        self.rotate_bcg_checkbox.x = self.btn_x
        self.rotate_bcg_checkbox.y = board.rows[0] + self.y_step * 6
        self.rotate_bcg_checkbox.batch = self.batch
        self.rotate_bcg_label = self.add_label(common.lang["settings_rotate_background"],
                                               self.rotate_bcg_checkbox.y + self.v_middle)
        self.rotate_bcg_checkbox.area = self.rotate_bcg_checkbox.x, self.rotate_bcg_checkbox.y, self.rotate_bcg_checkbox.x + self.rotate_bcg_checkbox.width, self.rotate_bcg_checkbox.y + self.rotate_bcg_checkbox.height

        self.play_music_checkbox = pyglet.sprite.Sprite(
            self.img_checkbox_checked if common.settings.play_music else self.img_checkbox_unchecked)
        self.play_music_checkbox.scale = board.scale
        self.play_music_checkbox.x = self.btn_x
        self.play_music_checkbox.y = board.rows[0] + self.y_step * 5
        self.play_music_checkbox.batch = self.batch
        self.play_music_label = self.add_label(common.lang["settings_play_music"],
                                               self.play_music_checkbox.y + self.v_middle)
        self.play_music_checkbox.area = self.play_music_checkbox.x, self.play_music_checkbox.y, self.play_music_checkbox.x + self.play_music_checkbox.width, self.play_music_checkbox.y + self.play_music_checkbox.height

        self.play_fx_checkbox = pyglet.sprite.Sprite(
            self.img_checkbox_checked if common.settings.play_fx else self.img_checkbox_unchecked)
        self.play_fx_checkbox.scale = board.scale
        self.play_fx_checkbox.x = self.btn_x
        self.play_fx_checkbox.y = board.rows[0] + self.y_step * 4
        self.play_fx_checkbox.batch = self.batch
        self.play_jingle_label = self.add_label(common.lang["settings_play_jingle"],
                                                self.play_fx_checkbox.y + self.v_middle)
        self.play_fx_checkbox.area = self.play_fx_checkbox.x, self.play_fx_checkbox.y, self.play_fx_checkbox.x + self.play_fx_checkbox.width, self.play_fx_checkbox.y + self.play_fx_checkbox.height

        self.play_warnings_checkbox = pyglet.sprite.Sprite(
            self.img_checkbox_checked if common.settings.play_warnings else self.img_checkbox_unchecked)
        self.play_warnings_checkbox.scale = board.scale
        self.play_warnings_checkbox.x = self.btn_x
        self.play_warnings_checkbox.y = board.rows[0] + self.y_step * 3
        self.play_warnings_checkbox.batch = self.batch
        self.play_warnings_label = self.add_label(common.lang["settings_play_warnings"],
                                                  self.play_warnings_checkbox.y + self.v_middle)
        self.play_warnings_checkbox.area = self.play_warnings_checkbox.x, self.play_warnings_checkbox.y, self.play_warnings_checkbox.x + self.play_warnings_checkbox.width, self.play_warnings_checkbox.y + self.play_warnings_checkbox.height

        self.password_go_btn = pyglet.sprite.Sprite(self.go_animation0)
        self.password_go_btn.scale = board.scale
        self.password_go_btn.x = self.btn_x
        self.password_go_btn.y = board.rows[0] + self.y_step * 1
        self.password_go_btn.batch = self.batch
        self.password_go_btn.area = self.password_go_btn.x, self.password_go_btn.y, self.password_go_btn.x + self.password_go_btn.width, self.password_go_btn.y + self.password_go_btn.height
        self.password_go_btn.clicked = False

        self.password_field = PassWidget(common.lang["settings_new_password"], int(board.base * 1.5), int(self.password_go_btn.y + self.password_go_btn.height // 4),
                                         int(board.base * 3), 40 * board.scale, self.batch)
        self.password_field.area = self.password_field.layout.x, self.password_field.layout.y, self.password_field.layout.x + self.password_field.layout.width, self.password_field.layout.y + self.password_field.layout.height

        self.close_area = self.background.x + self.background.width - board.base, self.background.y + self.background.height - board.base, self.background.x + self.background.width, self.background.y + self.background.height

        self.previews = self.create_cells_preview(self)
        self.cells_preview = pyglet.sprite.Sprite(self.previews[common.settings.cells_set])
        self.cells_preview.x = board.base
        self.cells_preview.y = board.rows[0] + self.y_step * 8.5
        self.cells_preview.scale = board.scale * 0.7
        self.cells_preview.anchor_x = 'center'
        self.cells_preview.batch = self.batch
        self.cells_preview.area = self.cells_preview.x, self.cells_preview.y, self.cells_preview.x + self.cells_preview.width, self.cells_preview.y + self.cells_preview.y + self.cells_preview.height

    @staticmethod
    def create_cells_preview(self):
        found = True
        previews = []
        i = 0
        while found:
            if os.path.exists("images/cells-" + str(i) + ".png"):
                img = pyglet.image.load("images/cells-" + str(i) + ".png").get_texture()
                img.width = 216 * 6
                img.height = 216
                previews.append(img)
                i += 1
            else:
                found = False
        return previews

    @staticmethod
    def update_cells_bitmaps(self):
        img = image.load("images/cells-" + str(common.settings.cells_set) + ".png")
        for i in range(8):
            common.cell_bitmaps[i] = img.get_region(i * 216, 0, 216, 216)
        for cell in common.cells_list:
            cell.image = common.cell_bitmaps[cell.type]

    def go_btn_click(self):
        if self.password_go_btn.clicked:
            print("Saving password")
            self.hide()
        else:
            pswd = self.password_field.document.text
            if len(pswd) >= 6 and not pswd == common.lang["settings_new_password"]:
                self.password_go_btn.clicked = True
            else:
                self.password_field.document.text = common.lang["settings_new_password"]
                self.window.remove_handlers(self.password_field.caret)
                self.password_field.caret.visible = False
        self.password_go_btn.image = self.go_animation1 if self.password_go_btn.clicked else self.go_animation0

    def show(self):
        self.password_field.document.text = common.lang["settings_new_password"]
        self.window.remove_handlers(self.password_field.caret)
        self.password_field.caret.visible = False
        self.password_go_btn.clicked = False
        self.password_go_btn.image = self.go_animation0

        self.old_playing = common.is_playing
        self.old_intro = common.is_intro
        self.old_dialog = common.is_dialog
        self.old_top10 = common.top10
        common.is_playing = False
        common.is_intro = False
        common.is_dialog = False
        common.top10 = False
        common.is_settings = True

        self.visible = True
        self.is_open = True

    def hide(self):
        common.is_playing = self.old_playing
        common.is_intro = self.old_intro
        common.is_dialog = self.old_dialog
        common.top10 = self.old_top10
        common.is_settings = False
        self.visible = False
        self.is_open = False

    def add_label(self, text, y):
        return pyglet.text.Label(
            text,
            font_name='DejaVu Sans Mono',
            color=(220, 220, 220, 255),
            font_size=int(38 * self.board.scale),
            x=self.label_x, y=y,
            anchor_x='center', anchor_y='center', batch=self.batch)

    def is_in(self, x, y, area):
        return area[0] < x < area[2] and area[1] < y < area[3]

    def click(self, x, y):
        if self.is_in(x, y, self.draw_bcg_checkbox.area):
            common.settings.background_draw = not common.settings.background_draw
            common.settings.save()
            self.refresh()

        if self.is_in(x, y, self.rotate_bcg_checkbox.area):
            common.settings.background_rotate = not common.settings.background_rotate
            common.settings.save()
            self.refresh()

        if self.is_in(x, y, self.play_music_checkbox.area):
            common.settings.play_music = not common.settings.play_music
            common.settings.save()
            self.refresh()

        if self.is_in(x, y, self.play_fx_checkbox.area):
            common.settings.play_fx = not common.settings.play_fx
            common.settings.save()
            self.refresh()

        if self.is_in(x, y, self.play_warnings_checkbox.area):
            common.settings.play_warnings = not common.settings.play_warnings
            common.settings.save()
            self.refresh()

        if self.is_in(x, y, self.cells_preview.area):
            if common.settings.cells_set < len(self.previews) - 1:
                common.settings.cells_set += 1
            else:
                common.settings.cells_set = 0
            self.cells_preview.image = self.previews[common.settings.cells_set]
            common.settings.save()
            self.update_cells_bitmaps(self)
            self.refresh()

        if self.is_in(x, y, self.password_field.area):
            self.window.push_handlers(self.password_field.caret)
            if self.password_field.document.text == common.lang["settings_new_password"]:
                self.password_field.document.text = ""

        if self.is_in(x, y, self.password_go_btn.area):
            self.go_btn_click()

        if self.is_in(x, y, self.close_area):
            self.hide()

    def refresh(self):
        self.draw_bcg_checkbox.image = self.img_checkbox_checked if common.settings.background_draw else self.img_checkbox_unchecked
        self.rotate_bcg_checkbox.image = self.img_checkbox_checked if common.settings.background_rotate else self.img_checkbox_unchecked
        self.play_music_checkbox.image = self.img_checkbox_checked if common.settings.play_music else self.img_checkbox_unchecked
        self.play_fx_checkbox.image = self.img_checkbox_checked if common.settings.play_fx else self.img_checkbox_unchecked
        self.play_warnings_checkbox.image = self.img_checkbox_checked if common.settings.play_warnings else self.img_checkbox_unchecked


class Settings(object):
    def __init__(self):
        self.file = common.app_dir + "/settings.pkl"
        self.cells_set = 0
        self.background_draw = True
        self.background_rotate = False
        self.play_music = True
        self.play_fx = True
        self.play_warnings = True
        self.muted = False

    def load(self):
        if not os.path.isfile(self.file):
            self.save()

        with open(self.file, 'rb') as input_data:
            settings = pickle.load(input_data)

        self.cells_set = settings.cells_set
        self.background_draw = settings.background_draw
        self.background_rotate = settings.background_rotate
        self.play_music = settings.play_music
        self.play_fx = settings.play_fx
        self.play_warnings = settings.play_warnings
        self.muted = settings.muted

    def save(self):
        with open(self.file, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)

    def switch_muted(self, panel):
        self.muted = not self.muted
        panel.button_sound.image = panel.img_sound if not self.muted else panel.img_sound_off
        self.save()


class PlayerDialog(pyglet.sprite.Sprite):
    def __init__(self, window, board):
        super().__init__(image.load("images/player-dialog.png"))

        self.window = window
        self.is_open = False
        # we need to know what to do after the dialog is closed
        self.old_intro_state = False
        self.old_playing_state = False
        self.old_top10_state = False

        self.image.width = board.base * 4
        self.image.height = board.base * 3.5
        self.base_square = board.base * self.scale
        self.x = board.base * 1
        self.y = board.base * 4

        self.batch = common.player_dialog_batch

        self.old_player_name = None

        self.name_field = TextWidget(common.player.name, int(self.x + self.base_square * 0.6),
                                     int(self.y + self.base_square * 2.37), self.base_square * 2.7,
                                     40 * common.board.scale, self.batch, False)

        self.pass_field = TextWidget('', int(self.x + self.base_square * 0.6), int(self.y + self.base_square * 1.37),
                                     self.base_square * 2.7, 40 * common.board.scale, self.batch, True)

        self.label = pyglet.text.Label(
            common.lang["player_account"],
            font_name='DejaVu Sans Mono',
            color=(255, 255, 255, 255),
            font_size=int(12 * self.scale),
            x=self.base_square * 3, y=self.y - self.base_square // 2,
            anchor_x='center', anchor_y='center', batch=self.batch)

        """Area rectangles (x1, y1, x2, y2)"""
        self.area_add = self.x, self.y, self.x + self.base_square, self.y + self.base_square
        self.area_delete = self.x + self.base_square, self.y, self.x + self.base_square * 2, self.y + self.base_square
        self.area_login = self.x + self.base_square * 2, self.y, self.x + self.base_square * 3, self.y + self.base_square
        self.area_logout = self.x + self.base_square * 3, self.y, self.x + self.base_square * 4, self.y + self.base_square
        self.area_password = self.x, self.y + self.base_square, self.x + self.base_square * 4, self.y + self.base_square * 2
        self.area_name = self.x, self.y + self.base_square * 2, self.x + self.base_square * 4, self.y + self.base_square * 3
        self.area_close = self.x + self.base_square * 3.5, self.y + self.base_square * 3, self.x + self.base_square * 4, self.y + self.base_square * 3.5

        self.message = common.lang["player_account"]

    def open(self):
        if not self.is_open:
            if common.top_list.is_open:
                common.top_list.hide()
            self.old_player_name = common.player.name
            self.name_field.update('')
            pswd = common.player.password if common.player.password is not None else ""
            self.pass_field.update('')

            self.set_message(common.lang["player_account"])

            self.is_open = True

            self.old_intro_state = common.is_intro
            self.old_playing_state = common.is_playing
            self.old_top10_state = common.top10
            common.is_intro = False
            common.is_playing = False
            common.top10 = False
            common.is_dialog = True

            if common.player_confirmation:
                common.player_confirmation.hide()

    def close(self, new_player_name=None):
        if self.is_open:
            self.is_open = False
            common.is_intro = self.old_intro_state
            common.is_playing = self.old_playing_state
            common.top10 = self.old_top10_state
            common.is_dialog = False
            # Change the player name if login successful (as we use the same field to show error msg and player name)
            if new_player_name:
                common.player.name = new_player_name
            else:
                common.player.name = self.old_player_name
                common.player.online = common.ONLINE

    def is_in(self, x, y, area):
        return area[0] < x < area[2] and area[1] < y < area[3]

    def refresh_label(self, x, y):
        if self.is_in(x, y, self.area_add):
            self.label.text = common.lang["player_add"]
        elif self.is_in(x, y, self.area_delete):
            self.label.text = common.lang["player_delete"]
        elif self.is_in(x, y, self.area_login):
            self.label.text = common.lang["player_login"]
        elif self.is_in(x, y, self.area_logout):
            self.label.text = common.lang["player_logout"]
        elif self.is_in(x, y, self.area_password):
            self.label.text = common.lang["player_password"]
        elif self.is_in(x, y, self.area_name):
            self.label.text = common.lang["player_name"]
        elif self.is_in(x, y, self.area_close):
            self.label.text = common.lang["close"]
        else:
            self.label.text = self.message

    def click(self, panel, x, y):
        if self.is_in(x, y, self.area_close):
            self.close()

        elif self.is_in(x, y, self.area_name):
            self.close_confirmation()
            self.pass_field.caret.visible = False
            self.name_field.caret.visible = True
            self.window.push_handlers(self.name_field.caret)  # set focus

        elif self.is_in(x, y, self.area_password):
            self.close_confirmation()
            self.name_field.caret.visible = False
            self.pass_field.caret.visible = True
            self.window.push_handlers(self.pass_field.caret)

        elif self.is_in(x, y, self.area_add):
            self.close_confirmation()
            self.new_player()

        elif self.is_in(x, y, self.area_delete):
            if not common.player_confirmation.visible:
                common.player_confirmation.show()
            else:
                self.close_confirmation()
                self.delete_player(panel)

        elif self.is_in(x, y, self.area_login):
            self.close_confirmation()
            self.login_player()

        elif self.is_in(x, y, self.area_logout):
            self.close_confirmation()
            self.logout_player(panel)

        else:
            self.close_confirmation()
            self.set_message(common.lang["player_account"])

    def close_confirmation(self):
        if common.player_confirmation and common.player_confirmation.visible:
            common.player_confirmation.hide()

    def set_message(self, msg):
        self.message = msg
        self.label.text = self.message

    def new_player(self):
        name = self.name_field.document.text
        pswd = self.pass_field.document.text
        name_ok = name.upper() != "ANONYMOUS" and len(name) >= 3
        pass_ok = len(pswd) >= 6
        if name_ok and pass_ok:
            self.message = common.lang["player_creating"]
            player_create(name, hashlib.md5(pswd.encode('utf-8')).hexdigest())  # in cloud_tools
        else:
            msg = ""
            if not name_ok:
                msg += common.lang["player_wrong_name"]
            if not pass_ok:
                msg += " " + common.lang["player_wrong_pass"]
            self.message = msg
            self.label.text = self.message

    def delete_player(self, panel):
        name = self.name_field.document.text
        logout = name == common.player.name  # Are we deleting the signed in player?
        pswd = self.pass_field.document.text
        name_ok = name.upper() != "ANONYMOUS" and len(name) >= 3
        pass_ok = len(pswd) >= 6
        if name_ok and pass_ok:
            self.message = common.lang["player_deleting"]
            if player_delete(name, hashlib.md5(pswd.encode('utf-8')).hexdigest()) and logout:  # in cloud_tools
                self.logout_player(panel)
        else:
            msg = ""
            if not name_ok:
                msg += common.lang["player_wrong_name"]
            if not pass_ok:
                msg += " " + common.lang["player_wrong_pass"]
            self.message = msg
            self.label.text = self.message
        if common.player.name != 'Anonymous':
            common.player.online = common.ONLINE

    def login_player(self):
        name = self.name_field.document.text
        pswd = self.pass_field.document.text
        name_ok = name.upper() != "ANONYMOUS" and len(name) >= 3
        pass_ok = len(pswd) >= 6
        if name_ok and pass_ok:
            self.set_message(common.lang["player_logging_in"].format(name))
            player_login(name, hashlib.md5(pswd.encode('utf-8')).hexdigest())  # in cloud_tools
        else:
            msg = ""
            if not name_ok:
                msg += common.lang["player_wrong_name"]
            if not pass_ok:
                msg += " " + common.lang["player_wrong_pass"]
            self.message = msg
            self.label.text = self.message

    def logout_player(self, panel):
        common.player.online = common.OFFLINE
        self.close("Anonymous")
        common.scores = [None, None, None, None, None, None]
        common.player.scores = [None, None, None, None, None, None]
        common.player.password = None

        with open(common.player_filename, 'wb') as output:
            pickle.dump(common.player, output, pickle.HIGHEST_PROTOCOL)

        panel.update_score_labels()


class Panel(object):
    """
    We use 2 bottom base rows as the control panel area.
    """

    def __init__(self, board):
        self.batch = pyglet.graphics.Batch()
        self.margin = board.margin
        self.btn_dim = board.btn_dimension
        self.btn_half = board.btn_dimension / 2

        self.base = board.base
        self.scale = board.window_width / (216 * 6 + 23 * 2)

        txt = str(6 + common.level * 3)
        self.border_size_txt = txt + "x" + txt

        self.label_x = self.margin + self.btn_dim * 5 + self.btn_dim / 2
        self.label_y = self.margin * 3

        panel_image = pyglet.image.load('images/panel.png')
        self.background = panel_image.get_texture()
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        self.background.width = board.base * 6
        self.background.height = board.base * 2

        self.intro_message = None  # This will be a label, drawn in not None

        self.img_sound = self.bcg_image(pyglet.image.load('images/btn-sound.png')).get_region(0, 0, 216, 216)
        self.img_sound_off = self.bcg_image(pyglet.image.load('images/btn-sound.png')).get_region(216, 0, 216, 216)
        self.img_settings = self.bcg_image(pyglet.image.load('images/btn-settings.png'))
        self.img_undo = self.bcg_image(pyglet.image.load('images/btn-undo.png'))
        self.img_up = self.bcg_image(pyglet.image.load('images/btn-up.png'))
        self.img_down = self.bcg_image(pyglet.image.load('images/btn-down.png'))
        self.img_start = self.bcg_image(pyglet.image.load('images/btn-start.png'))

        self.img_text = self.bcg_image_triple(pyglet.image.load('images/btn-text.png'))
        self.img_online = self.bcg_image_half(pyglet.image.load('images/btn-online.png'))
        self.img_offline = self.bcg_image_half(pyglet.image.load('images/btn-offline.png'))
        self.img_syncing = self.bcg_image_half(pyglet.image.load('images/btn-syncing.png'))
        self.img_top10 = self.bcg_image_half(pyglet.image.load('images/btn-top10.png'))
        self.img_website = self.bcg_image_half(pyglet.image.load('images/btn-website.png'))

        self.img_locked = self.bcg_image(pyglet.image.load('images/locked.png'))
        self.img_unlocked = self.bcg_image(pyglet.image.load('images/unlocked.png'))
        self.img_locked.width = board.base
        self.img_locked.height = board.base / 3
        self.img_unlocked.width = board.base
        self.img_unlocked.height = board.base / 3

        self.button_settings = pyglet.sprite.Sprite(self.img_settings)
        self.button_settings.x = self.margin
        self.button_settings.y = self.margin
        self.button_settings.batch = self.batch
        self.button_settings.area = self.button_settings.x, self.button_settings.y, self.button_settings.x + \
                                    self.btn_dim, self.button_settings.y + self.btn_dim
        self.button_settings.selected = False

        self.button_sound = pyglet.sprite.Sprite(self.img_sound if not common.settings.muted else self.img_sound_off)
        self.button_sound.x = self.margin + self.btn_dim
        self.button_sound.scale = self.scale
        self.button_sound.y = self.margin
        self.button_sound.batch = self.batch
        self.button_sound.area = self.button_sound.x, self.button_sound.y, self.button_sound.x + \
                                 self.btn_dim, self.button_sound.y + self.btn_dim
        self.button_sound.selected = False

        self.button_undo = pyglet.sprite.Sprite(self.img_undo)
        self.button_undo.x = self.margin + self.btn_dim * 2
        self.button_undo.y = self.margin
        self.button_undo.batch = self.batch
        self.button_undo.area = self.button_undo.x, self.button_undo.y, self.button_undo.x + \
                                self.btn_dim, self.button_undo.y + self.btn_dim
        self.button_undo.selected = False

        self.button_down = pyglet.sprite.Sprite(self.img_down)
        self.button_down.x = self.margin + self.btn_dim * 3
        self.button_down.y = self.margin
        self.button_down.batch = self.batch
        self.button_down.area = self.button_down.x, self.button_down.y, self.button_down.x + \
                                self.btn_dim, self.button_down.y + self.btn_dim
        self.button_down.selected = False

        self.button_up = pyglet.sprite.Sprite(self.img_up)
        self.button_up.x = self.margin + self.btn_dim * 4
        self.button_up.y = self.margin
        self.button_up.batch = self.batch
        self.button_up.area = self.button_up.x, self.button_up.y, self.button_up.x + \
                              self.btn_dim, self.button_up.y + self.btn_dim
        self.button_up.selected = False

        self.button_start = pyglet.sprite.Sprite(self.img_start)
        self.button_start.x = self.margin + self.btn_dim * 5
        self.button_start.y = self.margin
        self.button_start.batch = self.batch
        self.button_start.area = self.button_start.x, self.button_start.y, self.button_start.x + \
                                 self.btn_dim, self.button_start.y + self.btn_dim
        self.button_start.selected = False

        self.button_name = pyglet.sprite.Sprite(self.img_text)
        self.button_name.x = self.margin
        self.button_name.y = self.margin + self.btn_dim
        self.button_name.batch = self.batch
        self.button_name.area = self.button_name.x, self.button_name.y, self.button_name.x + \
                                self.btn_dim * 3, self.button_name.y + self.btn_half
        self.button_name.selected = False

        self.button_name.label = pyglet.text.Label(
            common.player.name,
            font_name='DejaVu Sans Mono',
            color=(87, 87, 120, 255),
            font_size=int(34 * self.scale),
            x=self.button_name.x + self.button_name.image.width // 2,
            y=self.button_name.y + self.button_name.image.height // 2,
            anchor_x='center', anchor_y='center', batch=self.batch)

        self.button_cloud = pyglet.sprite.Sprite(self.img_offline)
        self.button_cloud.x = self.margin + self.btn_dim * 3
        self.button_cloud.y = self.margin + self.btn_dim
        self.button_cloud.batch = self.batch
        self.button_cloud.area = self.button_cloud.x, self.button_cloud.y, self.button_cloud.x + \
                                 self.btn_dim, self.button_cloud.y + self.btn_half
        self.button_cloud.selected = False
        self.button_cloud.online = False

        self.update_user_label()  # check if it's necessary

        self.button_top10 = pyglet.sprite.Sprite(self.img_top10)
        self.button_top10.x = self.margin + self.btn_dim * 4
        self.button_top10.y = self.margin + self.btn_dim
        self.button_top10.batch = self.batch
        self.button_top10.area = self.button_top10.x, self.button_top10.y, self.button_top10.x + \
                                 self.btn_dim, self.button_top10.y + self.btn_half
        self.button_top10.selected = False

        self.button_website = pyglet.sprite.Sprite(self.img_website)
        self.button_website.x = self.margin + self.btn_dim * 5
        self.button_website.y = self.margin + self.btn_dim
        self.button_website.batch = self.batch
        self.button_website.area = self.button_website.x, self.button_website.y, self.button_website.x + \
                                   self.btn_dim, self.button_website.y + self.btn_half
        self.button_website.selected = False

        """Level score buttons"""
        self.level_display_y = self.margin * 2 + self.btn_dim * 1.5

        self.display_l0 = pyglet.sprite.Sprite(self.img_locked)
        self.display_l0.x = self.margin
        self.display_l0.y = self.level_display_y
        self.display_l0.batch = self.batch
        self.display_l0.locked = True
        self.display_l0.label = self.score_label(self.display_l0, "L0")

        self.display_l1 = pyglet.sprite.Sprite(self.img_locked)
        self.display_l1.x = self.margin + self.btn_dim
        self.display_l1.y = self.level_display_y
        self.display_l1.batch = self.batch
        self.display_l1.locked = True
        self.display_l1.label = self.score_label(self.display_l1, "L1")

        self.display_l2 = pyglet.sprite.Sprite(self.img_locked)
        self.display_l2.x = self.margin + self.btn_dim * 2
        self.display_l2.y = self.level_display_y
        self.display_l2.batch = self.batch
        self.display_l2.locked = True
        self.display_l2.label = self.score_label(self.display_l2, "L2")

        self.display_l3 = pyglet.sprite.Sprite(self.img_locked)
        self.display_l3.x = self.margin + self.btn_dim * 3
        self.display_l3.y = self.level_display_y
        self.display_l3.batch = self.batch
        self.display_l3.locked = True
        self.display_l3.label = self.score_label(self.display_l3, "L3")

        self.display_l4 = pyglet.sprite.Sprite(self.img_locked)
        self.display_l4.x = self.margin + self.btn_dim * 4
        self.display_l4.y = self.level_display_y
        self.display_l4.batch = self.batch
        self.display_l4.locked = True
        self.display_l4.label = self.score_label(self.display_l4, "L4")

        self.display_l5 = pyglet.sprite.Sprite(self.img_locked)
        self.display_l5.x = self.margin + self.btn_dim * 5
        self.display_l5.y = self.level_display_y
        self.display_l5.batch = self.batch
        self.display_l5.locked = True
        self.display_l5.label = self.score_label(self.display_l5, "L5")

        self.highlight_level(common.level)
        self.selected_level = 0

        self.label = pyglet.text.Label(
            "",
            font_name='DejaVu Sans Mono',
            font_size=20 * board.scale,
            x=board.board_width // 2, y=24 * self.scale,
            anchor_x='center', anchor_y='center', batch=self.batch)

    def set_lock_state(self, level, is_locked):
        if level == 0:
            self.display_l0.locked = is_locked
            self.display_l0.image = self.img_locked if is_locked else self.img_unlocked
        elif level == 1:
            self.display_l1.locked = is_locked
            self.display_l1.image = self.img_locked if is_locked else self.img_unlocked
        elif level == 2:
            self.display_l2.locked = is_locked
            self.display_l2.image = self.img_locked if is_locked else self.img_unlocked
        elif level == 3:
            self.display_l3.locked = is_locked
            self.display_l3.image = self.img_locked if is_locked else self.img_unlocked
        elif level == 4:
            self.display_l4.locked = is_locked
            self.display_l4.image = self.img_locked if is_locked else self.img_unlocked
        elif level == 5:
            self.display_l5.locked = is_locked
            self.display_l5.image = self.img_locked if is_locked else self.img_unlocked

    def update_score_labels(self):
        self.display_l0.label = self.score_label(self.display_l0, "L1: " + str(common.scores[0])) if common.scores[
                                                                                                         0] is not None else self.score_label(
            self.display_l0, "L1:")

        if common.scores[1] is not None:
            self.display_l1.label = self.score_label(self.display_l1, "L2: " + str(common.scores[1]))
            self.display_l1.image = self.img_unlocked
        else:
            self.display_l1.label = self.score_label(self.display_l1, "L2:")
            self.display_l1.image = self.img_locked

        if common.scores[2] is not None:
            self.display_l2.label = self.score_label(self.display_l2, "L3: " + str(common.scores[2]))
            self.display_l2.image = self.img_unlocked
        else:
            self.display_l2.label = self.score_label(self.display_l2, "L3:")
            self.display_l2.image = self.img_locked

        if common.scores[3] is not None:
            self.display_l3.label = self.score_label(self.display_l3, "L4: " + str(common.scores[3]))
            self.display_l3.image = self.img_unlocked
        else:
            self.display_l3.label = self.score_label(self.display_l3, "L4:")
            self.display_l3.image = self.img_locked

        if common.scores[4] is not None:
            self.display_l4.label = self.score_label(self.display_l4, "L5: " + str(common.scores[4]))
            self.display_l4.image = self.img_unlocked
        else:
            self.display_l4.label = self.score_label(self.display_l4, "L5:")
            self.display_l4.image = self.img_locked

        if common.scores[5] is not None:
            self.display_l5.label = self.score_label(self.display_l5, "L6: " + str(common.scores[5]))
            self.display_l5.image = self.img_unlocked
        else:
            self.display_l5.label = self.score_label(self.display_l5, "L6:")
            self.display_l5.image = self.img_locked

        self.update_user_label()  # check if it's necessary

    def update_user_label(self):
        self.button_name.label.text = common.player.name
        self.button_name.label.color = (255, 255, 255, 255) if common.player.name != "Anonymous" else (87, 87, 120, 255)
        if common.player.online == common.ONLINE:
            self.button_cloud.image = self.img_online
        elif common.player.online == common.OFFLINE:
            self.button_cloud.image = self.img_offline
        elif common.player.online == common.SYNCING:
            self.button_cloud.image = self.img_syncing
        # self.button_cloud.image = self.img_online if common.player.online else self.img_offline

    def score_label(self, sprite, txt):
        label = pyglet.text.Label(
            txt,
            font_name='DejaVu Sans Mono',
            font_size=int(24 * self.scale),
            x=sprite.x + self.margin * 1.5, y=sprite.y + sprite.image.height // 2,
            anchor_x='left', anchor_y='center')
        return label

    def highlight_level(self, which):
        self.display_l0.color = (255, 255, 255)
        self.display_l1.color = (255, 255, 255)
        self.display_l2.color = (255, 255, 255)
        self.display_l3.color = (255, 255, 255)
        self.display_l4.color = (255, 255, 255)
        self.display_l5.color = (255, 255, 255)
        if which == 0:
            self.display_l0.color = (255, 100, 0)
        elif which == 1:
            self.display_l1.color = (255, 100, 0)
        elif which == 2:
            self.display_l2.color = (255, 100, 0)
        elif which == 3:
            self.display_l3.color = (255, 100, 0)
        elif which == 4:
            self.display_l4.color = (255, 100, 0)
        elif which == 5:
            self.display_l5.color = (255, 100, 0)

    def set_selection(self, button, value):
        if value:
            button.selected = True
            button.color = 255, 100, 0
        else:
            button.selected = value
            button.color = 255, 255, 255

    def is_selected(self, x, y, area):
        return area[0] < x < area[2] and area[1] < y < area[3]

    def check_selection(self, x, y):
        # Game control buttons
        self.set_selection(self.button_sound, self.is_selected(x, y, self.button_sound.area))
        self.set_selection(self.button_settings, self.is_selected(x, y, self.button_settings.area))
        self.set_selection(self.button_undo, self.is_selected(x, y, self.button_undo.area))
        self.set_selection(self.button_down, self.is_selected(x, y, self.button_down.area))
        self.set_selection(self.button_up, self.is_selected(x, y, self.button_up.area))
        self.set_selection(self.button_start, self.is_selected(x, y, self.button_start.area))
        # Player account buttons
        self.set_selection(self.button_name, self.is_selected(x, y, self.button_name.area))
        self.set_selection(self.button_cloud, self.is_selected(x, y, self.button_cloud.area))
        self.set_selection(self.button_top10, self.is_selected(x, y, self.button_top10.area))
        self.set_selection(self.button_website, self.is_selected(x, y, self.button_website.area))

        if self.button_sound.selected:
            self.label.text = common.lang["panel_sounds"]
        elif self.button_settings.selected:
            self.label.text = common.lang["settings"]
        elif self.button_undo.selected:
            self.label.text = common.lang["panel_undo"]
        elif self.button_down.selected:
            self.label.text = common.lang["panel_level_down"]
        elif self.button_up.selected:
            self.label.text = common.lang["panel_level_up"]
        elif self.button_start.selected:
            self.label.text = common.lang["panel_start"] + " " + self.border_size_txt
        elif self.button_name.selected:
            self.label.text = common.lang["player_account"]
        elif self.button_cloud.selected:
            if common.player.online == common.ONLINE:
                self.label.text = common.lang["panel_force_sync"]
            elif common.player.online == common.OFFLINE:
                self.label.text = common.lang["player_offline"]
            elif common.player.online == common.SYNCING:
                self.label.text = common.lang["player_syncing"]
        elif self.button_top10.selected:
            self.label.text = common.lang["top_ten"]
        elif self.button_website.selected:
            self.label.text = common.lang["website"]
        else:
            self.label.text = ""

    def level_up(self):
        if self.selected_level < common.level_max:
            self.selected_level += 1
            txt = str(6 + self.selected_level * 3)
            self.border_size_txt = txt + "x" + txt
            self.highlight_level(self.selected_level)

    def level_down(self):
        if self.selected_level > 0:
            self.selected_level -= 1
            txt = str(6 + self.selected_level * 3)
            self.border_size_txt = txt + "x" + txt
            self.highlight_level(self.selected_level)

    def level_select(self, level):
        self.selected_level = level
        txt = str(6 + self.selected_level * 3)
        self.border_size_txt = txt + "x" + txt
        self.highlight_level(self.selected_level)

    def bcg_image(self, source):
        texture = source.get_texture()
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        texture.width = self.btn_dim
        texture.height = self.btn_dim
        return texture

    def bcg_image_half(self, source):
        texture = source.get_texture()
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        texture.width = self.btn_dim
        texture.height = self.btn_dim / 2
        return texture

    def bcg_image_triple(self, source):
        texture = source.get_texture()
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        texture.width = self.btn_dim * 3
        texture.height = self.btn_dim / 2
        return texture

    def draw(self):
        self.background.blit(0, 0)
        self.batch.draw()
        self.display_l0.label.draw()
        self.display_l1.label.draw()
        self.display_l2.label.draw()
        self.display_l3.label.draw()
        self.display_l4.label.draw()
        self.display_l5.label.draw()


class Sounds(object):
    def __init__(self):
        self.key = pyglet.media.StaticSource(pyglet.media.load('sounds/key.wav', streaming=False))
        self.drop = pyglet.media.StaticSource(pyglet.media.load('sounds/drop.wav', streaming=False))
        self.rotate = pyglet.media.StaticSource(pyglet.media.load('sounds/rotate.wav', streaming=False))
        self.undo = pyglet.media.StaticSource(pyglet.media.load('sounds/undo.wav', streaming=False))
        self.warning = pyglet.media.StaticSource(pyglet.media.load('sounds/warning.wav', streaming=False))
        self.start = pyglet.media.StaticSource(pyglet.media.load('sounds/start.wav', streaming=False))
        self.level = pyglet.media.StaticSource(pyglet.media.load('sounds/level.wav', streaming=False))
        self.unlocked = pyglet.media.StaticSource(pyglet.media.load('sounds/unlocked.wav', streaming=False))
        try:
            """As this sound is being played first, let's check if the avbin library works"""
            self.hello = pyglet.media.StaticSource(pyglet.media.load('sounds/hello.ogg', streaming=False))
            common.avbin = True
        except:
            print("The avbin library not installed or doesn't work: soundtrack turned off :(")
            self.hello = pyglet.media.StaticSource(pyglet.media.load('sounds/hello.wav', streaming=False))

    def play(self, panel, fx):
        if not common.settings.muted:
            if fx == "key":
                self.key.play()
            if fx == "drop":
                self.drop.play()
            if fx == "rotate":
                self.rotate.play()
            if fx == "undo":
                self.undo.play()
            if fx == "hello":
                self.hello.play()
            if fx == "warning":
                self.warning.play()
            if fx == "start":
                self.start.play()
            if fx == "level":
                self.level.play()
            if fx == "unlocked":
                self.unlocked.play()


class Player(object):
    def __init__(self, name, password, scores):
        self.name = name
        self.password = password
        self.scores = scores
        self.cloud_scores = None
        self.online = common.OFFLINE


class Language(dict):
    def __init__(self, which):
        config = configparser.ConfigParser()
        with open('languages/' + which) as f:
            config.read_file(f)

        values = {}
        if config.has_section("lang"):
            options = config.options("lang")
            for key in options:
                value = config.get("lang", key)
                values[key] = value
        super().__init__(values)
