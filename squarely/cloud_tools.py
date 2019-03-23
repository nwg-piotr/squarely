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
import platform
import requests
import locale
import common


# from tools import player_save, player_load

def create_player(name, password):
    os = platform.system() + " " + platform.release() + " " + str(locale.getlocale()[0]) if common.rc.allow_os_info else "forbidden"
    url = 'http://nwg.pl/puzzle/player.php?action=create&pname=' + name + '&ppswd=' + password + '&pos=' + os
    print(url)
    try:
        response = requests.get(url, headers=common.headers)
        print(response.content)
        response_text = response.text
    except requests.exceptions.RequestException as e:
        response_text = "Error: " + str(e)

    if response_text == "player_created":
        common.player.name = name
        common.player.password = password
        # player_save() todo sound preferences should not be attached to the panel, change! Maybe to the player?
