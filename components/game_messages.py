#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Message and message log (pygame palette colors, no libtcod)."""

import textwrap

from renderer import palette as C


class Message:
    def __init__(self, text, color=C.WHITE):
        self.text = text
        self.color = color


class MessageLog:
    def __init__(self, x, width, height):
        self.message = []
        self.x = x
        self.width = width
        self.height = height

    def add_message(self, message):
        new_message_lines = textwrap.wrap(message.text, self.width)

        for line in new_message_lines:
            if len(self.message) == self.height:
                del self.message[0]

            self.message.append(Message(line, message.color))
