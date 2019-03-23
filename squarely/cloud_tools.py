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
import pickle
import common


def create_player(name, password, dialog):
    os = platform.system() + " " + platform.release() + " " + str(
        locale.getlocale()[0]) if common.rc.allow_os_info else "forbidden"
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
        with open(common.player_filename, 'wb') as output:
            pickle.dump(common.player, output, pickle.HIGHEST_PROTOCOL)
        dialog.label.text = common.lang["player_created"]

    elif response_text == 'failed_creating':
        dialog.set_message(common.lang["player_failed_creating"])
