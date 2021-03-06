#!/usr/bin/env python
# _*_ coding: utf-8 _*_

"""
A puzzle game which utilizes the python-pyglet library

Author: Piotr Miller
e-mail: nwg.piotr@gmail.com
Website: http://nwg.pl
Project: https://github.com/nwg-piotr/squarely
License: GPL3

https://github.com/adamlwgriffiths/Pyglet/blob/master/examples/text_input.py
"""

import pyglet


class Rectangle(object):
    """Draws a rectangle into a batch."""

    def __init__(self, x1, y1, x2, y2, batch):
        self.vertex_list = batch.add(4, pyglet.gl.GL_QUADS, None,
                                     ('v2i', [x1, y1, x2, y1, x2, y2, x1, y2]),
                                     ('c4B', [0, 0, 0, 0,] * 4))


class TextWidget(object):
    def __init__(self, text, x, y, width, font_size, batch, is_password):

        color = (0, 0, 0, 0) if is_password else (255, 255, 255, 255)

        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document.set_style(0, len(self.document.text), dict(color=color, font_size=font_size))
        font = self.document.get_font()
        height = font.ascent - font.descent

        self.layout = pyglet.text.layout.IncrementalTextLayout(self.document, width, height, multiline=False,
                                                               batch=batch)
        self.caret = pyglet.text.caret.Caret(self.layout, color=(255, 255, 255))

        self.layout.x = x
        self.layout.y = y

    def hit_test(self, x, y):
        return (0 < x - self.layout.x < self.layout.width and
                0 < y - self.layout.y < self.layout.height)

    def update(self, text):
        self.document.text = text


class PassWidget(object):
    def __init__(self, text, x, y, width, font_size, batch):

        color = (100, 100, 100, 255)

        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document.set_style(0, len(self.document.text), dict(color=color, font_size=font_size, italic=True))
        font = self.document.get_font()
        height = font.ascent - font.descent

        self.layout = pyglet.text.layout.IncrementalTextLayout(self.document, width, height, multiline=False,
                                                               batch=batch)
        self.caret = pyglet.text.caret.Caret(self.layout, color=(255, 255, 255))

        self.layout.x = x
        self.layout.y = y
        self.area = None

        # Rectangular outline
        #pad = 10
        #self.rectangle = Rectangle(x - pad, y - pad, x + width + pad, y + height + pad, batch)

    def hit_test(self, x, y):
        return (0 < x - self.layout.x < self.layout.width and
                0 < y - self.layout.y < self.layout.height)

    def update(self, text):
        self.document.text = text
