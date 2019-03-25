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
from threading import Thread
import locale
import pickle
import common
import socket

from requests import get, post, put, patch, delete, options, head

request_methods = {
    'get': get,
    'post': post,
    'put': put,
    'patch': patch,
    'delete': delete,
    'options': options,
    'head': head,
}


def player_create(name, password, dialog):
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
        dialog.label.text = common.lang["player_created"]
        dialog.message = common.lang["player_created"]
    elif response_text == "player_exists":
        dialog.label.text = common.lang["player_exists"]
        dialog.message = common.lang["player_exists"]

    elif response_text == 'failed_creating':
        dialog.set_message(common.lang["player_failed_creating"])


def player_login(name, password):
    url = 'http://nwg.pl/puzzle/player.php?action=login&pname=' + name + '&ppswd=' + password
    print(url)
    if internet_on():
        async_request('get', url, headers=common.headers, pwd=password, callback=lambda r, p: login_result(r, p))
    else:
        common.player.online = False
        common.player.name = common.lang["player_offline"]


def login_result(result, password):
    txt = result.content.decode("utf-8")
    print(txt)
    if txt.startswith('login_ok'):
        common.player.online = True
        # we need numerical values of scores we've just read
        data = txt.split(",")
        name = data[1]
        scores_txt = data[2].split(":")
        common.player.cloud_scores = []
        for item in scores_txt:
            try:
                common.player.cloud_scores.append(int(item))
            except ValueError:
                common.player.cloud_scores.append(None)
        print(common.player.cloud_scores)
        # update and save player data
        common.player.name = name
        common.player.password = password

        for i in range(len(common.player.cloud_scores)):
            if common.player.cloud_scores[i] is not None:
                common.player.scores[i] = common.player.cloud_scores[i]
                common.scores[i] = common.player.cloud_scores[i]

        with open(common.player_filename, 'wb') as output:
            pickle.dump(common.player, output, pickle.HIGHEST_PROTOCOL)

        common.player_dialog.close(name)

    else:
        common.player.online = False
        if txt == 'no_such_player':
            common.player.name = common.lang["player_no_such"]
        elif txt == 'wrong_pswd':
            common.player.name = common.lang["player_wrong_password"]
        else:
            common.player.name = common.lang["player_login_failed"]


def async_request(method, *args, callback=None, pwd=None, timeout=15, **kwargs):
    """ Credits go to @kylebebak at https://stackoverflow.com/a/44917020/4040598

    Makes request on a different thread, and optionally passes response to a
    `callback` function when request returns.
    """
    method = request_methods[method.lower()]
    if callback:
        def callback_with_args(response, *args, **kwargs):
            callback(response, pwd)
        kwargs['hooks'] = {'response': callback_with_args}
    kwargs['timeout'] = timeout
    thread = Thread(target=method, args=args, kwargs=kwargs)
    thread.start()


def internet_on(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as e:
        print(e)
        return False
