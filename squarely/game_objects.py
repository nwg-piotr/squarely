#!/usr/bin/python3
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
import pyglet
from pyglet.gl import *
from pyglet import image
import configparser
import common


class GameBoard:
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
        This is why this class must me instatiated first!
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

        self.status_message_y = self.base * 0.12
        self.message = None

        """Selected cells"""
        self.sel_0 = None
        self.sel_1 = None
        self.sel_2 = None
        self.sel_3 = None

        print("Rows: " + str(self.rows))
        print("Columns: " + str(self.columns))

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
        #self.opacity = 70

    def clear_to_delete(self):
        self.to_delete = False
        #self.opacity = 255


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
        animation = (pyglet.image.Animation.from_image_sequence(sequence, 0.24, False))

        super().__init__(animation)

        self.x = board.columns[2]
        self.y = board.rows[2]


class FinishedAnimation(pyglet.sprite.Sprite):
    def __init__(self, board):
        frames_source = image.load("images/smile-frames.png")
        sequence = pyglet.image.ImageGrid(frames_source, 1, 6)
        animation = (pyglet.image.Animation.from_image_sequence(sequence, 0.24, False))

        super().__init__(animation)

        self.x = board.columns[2]
        self.y = board.rows[2]


class HelloAnimation(pyglet.sprite.Sprite):
    def __init__(self, board):
        frames_source = image.load("images/hello-frames.png")
        sequence = pyglet.image.ImageGrid(frames_source, 1, 9)
        animation = (pyglet.image.Animation.from_image_sequence(sequence, 0.34, False))

        super().__init__(animation)

        self.x = board.columns[1]
        self.y = board.rows[1]
        self.scale = board.scale * 2


class Panel:
    """
    We use 2 bottom rows of the game board as the control panel area. Let's leave it as is util the time comes.
    """
    def __init__(self, board):
        self.batch = pyglet.graphics.Batch()
        self.margin = board.margin
        self.btn_dim = board.btn_dimension

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

        self.music_on = True
        self.sounds_on = True

        self.intro_message = None  # This will be a label, drawn in not None

        self.img_sound = self.bcg_image(pyglet.image.load('images/btn-sound.png')).get_region(0, 0, 216, 216)
        self.img_sound_off = self.bcg_image(pyglet.image.load('images/btn-sound.png')).get_region(216, 0, 216, 216)
        self.img_music = self.bcg_image(pyglet.image.load('images/btn-music.png')).get_region(0, 0, 216, 216)
        self.img_music_off = self.bcg_image(pyglet.image.load('images/btn-music.png')).get_region(216, 0, 216, 216)
        self.img_undo = self.bcg_image(pyglet.image.load('images/btn-undo.png'))
        self.img_up = self.bcg_image(pyglet.image.load('images/btn-up.png'))
        self.img_down = self.bcg_image(pyglet.image.load('images/btn-down.png'))
        self.img_start = self.bcg_image(pyglet.image.load('images/btn-start.png'))

        self.img_locked = self.bcg_image(pyglet.image.load('images/locked.png'))
        self.img_unlocked = self.bcg_image(pyglet.image.load('images/unlocked.png'))
        self.img_locked.width = board.base
        self.img_locked.height = board.base / 3
        self.img_unlocked.width = board.base
        self.img_unlocked.height = board.base / 3

        self.button_sound = pyglet.sprite.Sprite(self.img_sound)
        self.button_sound.x = self.margin
        self.button_sound.scale = self.scale
        self.button_sound.y = self.margin
        self.button_sound.batch = self.batch
        self.button_sound.area = self.button_sound.x, self.button_sound.y, self.button_sound.x + \
                                 self.btn_dim, self.button_sound.y + self.btn_dim
        self.button_sound.selected = False

        self.button_music = pyglet.sprite.Sprite(self.img_music)
        self.button_music.scale = self.scale
        self.button_music.x = self.margin + self.btn_dim
        self.button_music.y = self.margin
        self.button_music.batch = self.batch
        self.button_music.area = self.button_music.x, self.button_music.y, self.button_music.x + \
                                 self.btn_dim, self.button_music.y + self.btn_dim
        self.button_music.selected = False

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
        self.display_l0.label = self.score_label(self.display_l0, "L1: " + str(common.scores[0])) if common.scores[0] is not None else self.score_label(self.display_l0, "L1:")
        self.display_l1.label = self.score_label(self.display_l1, "L2: " + str(common.scores[1])) if common.scores[1] is not None else self.score_label(self.display_l1, "L2:")
        self.display_l2.label = self.score_label(self.display_l2, "L3: " + str(common.scores[2])) if common.scores[2] is not None else self.score_label(self.display_l2, "L3:")
        self.display_l3.label = self.score_label(self.display_l3, "L4: " + str(common.scores[3])) if common.scores[3] is not None else self.score_label(self.display_l3, "L4:")
        self.display_l4.label = self.score_label(self.display_l4, "L5: " + str(common.scores[4])) if common.scores[4] is not None else self.score_label(self.display_l4, "L5:")
        self.display_l5.label = self.score_label(self.display_l5, "L6: " + str(common.scores[5])) if common.scores[5] is not None else self.score_label(self.display_l5, "L6:")

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

    def deselect_all(self):
        """For use just in case the cursor left the panel area too fast to be detected"""
        self.set_selection(self.button_sound, False)
        self.set_selection(self.button_music, False)
        self.set_selection(self.button_undo, False)
        self.set_selection(self.button_down, False)
        self.set_selection(self.button_up, False)
        self.set_selection(self.button_start, False)

    def check_selection(self, x, y):
        self.set_selection(self.button_sound,
                           self.button_sound.area[0] < x < self.button_sound.area[2] and self.button_sound.area[1] < y <
                           self.button_sound.area[3])

        self.set_selection(self.button_music,
                           self.button_music.area[0] < x < self.button_music.area[2] and self.button_music.area[1] < y <
                           self.button_music.area[3])

        self.set_selection(self.button_undo,
                           self.button_undo.area[0] < x < self.button_undo.area[2] and self.button_undo.area[1] < y <
                           self.button_undo.area[3] and common.backup_matrix is not None)

        self.set_selection(self.button_down,
                           self.button_down.area[0] < x < self.button_down.area[2] and self.button_down.area[1] < y <
                           self.button_down.area[3] and self.selected_level > 0)

        self.set_selection(self.button_up,
                           self.button_up.area[0] < x < self.button_up.area[2] and self.button_up.area[1] < y <
                           self.button_up.area[3] and common.level < common.level_max)

        self.set_selection(self.button_start,
                           self.button_start.area[0] < x < self.button_start.area[2] and self.button_start.area[1] < y <
                           self.button_start.area[3])

        if self.button_sound.selected:
            common.board.message = common.lang["panel_sounds"]
        elif self.button_music.selected:
            if common.avbin:
                common.board.message = common.lang["panel_music"]
            else:
                common.board.message = common.lang["panel_music_missing"]
        elif self.button_undo.selected:
            common.board.message = common.lang["panel_undo"]
        elif self.button_down.selected:
            common.board.message = common.lang["panel_level_down"]
        elif self.button_up.selected:
            common.board.message = common.lang["panel_level_up"]
        elif self.button_start.selected:
            common.board.message = common.lang["panel_start"] + " " + self.border_size_txt
        else:
            common.board.message = None

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

    def switch_sounds(self):
        self.sounds_on = not self.sounds_on
        self.button_sound.image = self.img_sound if self.sounds_on else self.img_sound_off

    def switch_music(self):
        self.music_on = not self.music_on
        self.button_music.image = self.img_music if self.music_on else self.img_music_off

    def draw(self):
        self.background.blit(0, 0)
        self.batch.draw()
        self.display_l0.label.draw()
        self.display_l1.label.draw()
        self.display_l2.label.draw()
        self.display_l3.label.draw()
        self.display_l4.label.draw()
        self.display_l5.label.draw()


class Sounds:
    def __init__(self):
        self.key = pyglet.media.StaticSource(pyglet.media.load('sounds/key.wav', streaming=False))
        self.drop = pyglet.media.StaticSource(pyglet.media.load('sounds/drop.wav', streaming=False))
        self.rotate = pyglet.media.StaticSource(pyglet.media.load('sounds/rotate.wav', streaming=False))
        self.undo = pyglet.media.StaticSource(pyglet.media.load('sounds/undo.wav', streaming=False))
        #self.hello = pyglet.media.StaticSource(pyglet.media.load('sounds/hello.ogg', streaming=False))

    def play(self, panel, fx):
        if panel.sounds_on:
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


class Player(object):
    def __init__(self, name, password, scores):
        self.name = name
        self.password = password
        self.scores = scores


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
