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
import requests
from threading import Thread
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


def player_create(name, password):
    old = common.player.online
    common.player.online = common.SYNCING
    url = 'http://nwg.pl/puzzle/player.php?action=create&pname=' + name + '&ppswd=' + password
    if common.rc.debug_mode:
        print(url)
    try:
        response = requests.get(url, headers=common.headers)
        if common.rc.debug_mode:
            print(response.content)
        response_text = response.text
    except requests.exceptions.RequestException as e:
        response_text = "Error: " + str(e)

    if response_text == "player_created":
        common.player_dialog.set_message(common.lang["player_created"])

    elif response_text == "player_exists":
        common.player_dialog.set_message(common.lang["player_exists"])

    elif response_text == 'failed_creating':
        common.player_dialog.set_message(common.lang["player_failed_creating"])

    common.player.online = old


def player_delete(name, password):
    common.player.online = common.SYNCING
    url = 'http://nwg.pl/puzzle/player.php?action=delete&pname=' + name + '&ppswd=' + password
    if common.rc.debug_mode:
        print(url)
    try:
        response = requests.get(url, headers=common.headers)
        if common.rc.debug_mode:
            print(response.content)
        response_text = response.text
    except requests.exceptions.RequestException as e:
        response_text = "Error: " + str(e)

    if response_text == "player_deleted":
        common.player_dialog.set_message(common.lang["player_deleted"])
        return True  # Success

    elif response_text == "failed_deleting":
        common.player_dialog.set_message(common.lang["player_delete_failed"])
        return False  # Failure

    elif response_text == 'no_player_wrong_pass':
        common.player_dialog.set_message(common.lang["player_delete_no_player"])
        return False  # Failure


def top_ten_update(password=None):
    print("Loading scores...", end=" ")
    url = 'http://nwg.pl/puzzle/top.php'
    if internet_on():
        async_request('get', url, headers=common.headers, pwd=password, callback=lambda r, p: top_ten_result(r, p))


def top_ten_result(result, password=None):
    print(" Done")
    txt = result.content.decode("utf-8")
    if txt.startswith('top_ten'):
        data = txt.split("#")
        output = common.lang["top_ten"] + ":\n\n"
        for i in range(1, len(data)):
            output += data[i] + "\n"

        # It would be cool to update the TopList sprite here, but we can not do if on the async thread :/
        # We need an intermediary variable.
        common.top10_content = output


def player_password(name, password, new_password):
    common.player.online = common.SYNCING
    url = 'http://nwg.pl/puzzle/player.php?action=password&pname=' + name + '&ppswd=' + password + '&pnewpass=' + new_password
    if common.rc.debug_mode:
        if common.rc.debug_mode:
            if common.rc.debug_mode:
                print(url)
    if internet_on():
        async_request('get', url, headers=common.headers, pwd=new_password, callback=lambda r, p: password_result(r, p))
    else:
        common.player.online = common.OFFLINE


def password_result(result, new_password):
    txt = result.content.decode("utf-8")
    if common.rc.debug_mode:
        print(txt)

    if txt.startswith('password_changed'):
        common.player.password = new_password

        with open(common.player_filename, 'wb') as output:
            pickle.dump(common.player, output, pickle.HIGHEST_PROTOCOL)

        if common.settings_dialog.is_open:
            common.settings_dialog.hide()


def player_login(name, password):
    common.player.online = common.SYNCING
    url = 'http://nwg.pl/puzzle/player.php?action=login&pname=' + name + '&ppswd=' + password
    if common.rc.debug_mode:
        print(url)
    if internet_on():
        async_request('get', url, headers=common.headers, pwd=password, callback=lambda r, p: login_result(r, p))
    else:
        common.player.online = common.OFFLINE


def login_result(result, password):
    txt = result.content.decode("utf-8")
    if common.rc.debug_mode:
        print(txt)

    if txt.startswith('login_ok'):
        common.player.online = common.ONLINE
        # we need numerical values of scores we've just read
        data = txt.split(",")
        name = data[1]
        scores_txt = data[2].split(":")
        # Scores stored in the cloud
        common.player.cloud_scores = []
        for item in scores_txt:
            try:
                common.player.cloud_scores.append(int(item))
            except ValueError:
                common.player.cloud_scores.append(None)

        # update player credentials: we'll need them to update scores
        common.player.name = name
        common.player.password = password

        # Resolve possible conflicts
        synchronize = sync_needed()

        # Now we should have all the scores locally locally up to date. Let's save...
        with open(common.player_filename, 'wb') as output:
            pickle.dump(common.player, output, pickle.HIGHEST_PROTOCOL)

        # ...and sync to the cloud if necessary
        if synchronize:
            player_sync(name, password)

        if common.player_dialog.is_open:
            common.player_dialog.close(name)

    else:
        common.player.online = common.OFFLINE
        # As we are on another thread, the label.text can not be updated from here (crashes).
        # We're unable to use the set_message method, so the label will stay out od date until mouse moved :(
        if txt == 'no_such_player':
            common.player_dialog.message = common.lang["player_no_such"]
        elif txt == 'wrong_pswd':
            common.player_dialog.message = common.lang["player_wrong_password"]
        else:
            common.player_dialog.message = common.lang["player_login_failed"]


def sync_needed():
    """
    We need to resolve conflicts between what's stored online and local scores. The criteria will be values.
    The player could have stored results on another machine or offline. To keep things simple, let each better
    (lower) value overwrite the worse one. Let's start from sorting things locally.
    """
    needed = False
    for i in range(len(common.player.cloud_scores)):

        local = common.player.scores[i]
        remote = common.player.cloud_scores[i]

        # Compare values if both are numbers; overwrite worse (higher) with better
        if local and remote:
            if remote < local:
                local = remote  # just update the local value
                if common.rc.debug_mode:
                    print("updating local value")
                common.scores[i] = local  # also update the temporary list
                common.player.scores[i] = local  # and the player scores
            elif local < remote:
                needed = True  # Let's sync local scores to the cloud when ready
                if common.rc.debug_mode:
                    print("Sync: local < remote ")

        # In case we have no local value:
        if remote and not local:  # we have None local value locally, remote counterpart present
            local = remote  # just update tle local value
            common.player.scores[i] = local  # update local score
            common.scores[i] = local  # and also the temporary list

        if local and not remote:  # we have a local value, remote counterpart absent
            needed = True
            if common.rc.debug_mode:
                print("Sync: local and not remote ")

    if common.rc.debug_mode:
        print("Local: ", common.player.scores)
        print("Remote: ", common.player.cloud_scores)
        print("Upload to the server?", needed)

    return needed


def player_sync(name, password):
    # We will not reload from the cloud, so let's update the helper online scores list this way
    for i in range(len(common.player.scores)):
        common.player.cloud_scores[i] = common.player.scores[i]

    common.player.online = common.SYNCING

    url = 'http://nwg.pl/puzzle/player.php?action=update&pname=' + name + '&ppswd=' + password

    for i in range(len(common.player.scores)):
        if common.player.scores[i]:
            url += '&ps' + str(i) + "=" + str(common.player.scores[i])

    # print(url)
    if internet_on():
        async_request('get', url, headers=common.headers, callback=lambda r, p: sync_result(r, p))
    else:
        common.player.online = common.OFFLINE


def sync_result(result, password):
    txt = result.content.decode("utf-8")
    if common.rc.debug_mode:
        print(txt)
    if txt == 'scores_updated' or txt == 'no_result':
        common.player.online = common.ONLINE
    else:
        common.player.online = common.OFFLINE
        if common.rc.debug_mode:
            print("Could not sync")


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
        if common.player.name != 'Anonymous':
            common.player.online = common.ONLINE
        return True
    except Exception as e:
        if common.rc.debug_mode:
            print('Couldnt resolve host 8.8.8.8', e)
        common.player.online = common.OFFLINE
        return False
