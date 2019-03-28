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
    # print(url)
    try:
        response = requests.get(url, headers=common.headers)
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
    # print(url)
    try:
        response = requests.get(url, headers=common.headers)
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


def top_ten(password=None):
    print("\nAsking server for scores...")
    url = 'http://nwg.pl/puzzle/player.php?action=display&plimit=10'
    if internet_on():
        async_request('get', url, headers=common.headers, pwd=password, callback=lambda r, p: top_ten_result(r, p))


def top_ten_result(result, password=None):
    txt = result.content.decode("utf-8")
    if txt.startswith('top_10'):
        # print(txt)
        levels = txt[7:].split("#")
        #print(levels)
        level0 = levels[0][:-1].split(":")
        level1 = levels[1][:-1].split(":")
        level2 = levels[2][:-1].split(":")
        level3 = levels[3][:-1].split(":")
        level4 = levels[4][:-1].split(":")
        level5 = levels[5][:-1].split(":")

        output_l0 = "Level 1: "
        for i in range(len(level0)):
            elements = level0[i].split(",")
            output_l0 += str(i + 1) + ". " + elements[0] + " (" + str(elements[1]) + ") "

        output_l1 = "Level 2: "
        for i in range(len(level1)):
            elements = level1[i].split(",")
            output_l1 += str(i + 1) + ". " + elements[0] + " (" + str(elements[1]) + ") "

        output_l2 = "Level 3: "
        for i in range(len(level2)):
            elements = level2[i].split(",")
            output_l2 += str(i + 1) + ". " + elements[0] + " (" + str(elements[1]) + ") "

        output_l3 = "Level 4: "
        for i in range(len(level3)):
            elements = level3[i].split(",")
            output_l3 += str(i + 1) + ". " + elements[0] + " (" + str(elements[1]) + ") "

        output_l4 = "Level 5: "
        for i in range(len(level4)):
            elements = level4[i].split(",")
            output_l4 += str(i + 1) + ". " + elements[0] + " (" + str(elements[1]) + ") "

        output_l5 = "Level 6: "
        for i in range(len(level5)):
            elements = level5[i].split(",")
            if len(elements) > 1:
                output_l5 += str(i + 1) + ". " + elements[0] + " (" + str(elements[1]) + ") "

        print(output_l0)
        print(output_l1)
        print(output_l2)
        print(output_l3)
        print(output_l4)
        print(output_l5)

        txt = common.lang["top_ten"] + "\n" + output_l0 + "\n" + output_l1
        common.top10_content = txt


def player_login(name, password):
    common.player.online = common.SYNCING
    url = 'http://nwg.pl/puzzle/player.php?action=login&pname=' + name + '&ppswd=' + password
    #print(url)
    if internet_on():
        async_request('get', url, headers=common.headers, pwd=password, callback=lambda r, p: login_result(r, p))
    else:
        common.player.online = common.OFFLINE


def login_result(result, password):
    txt = result.content.decode("utf-8")
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

        # update and save player credentials: we'll need them to update scores
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

        common.player_dialog.close(name)

    else:
        common.player.online = common.OFFLINE
        # For some mysterious reason the label.text can not be updated from here (crashes),
        # so we won't use the set_message method. The label will stay out od date until mouse moved :(
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
                common.scores[i] = local  # and also update the temporary list
            elif local < remote:
                needed = True  # Let's sync local scores to the cloud when ready
                print("Sync: local < remote ")

        # In case we have no local value:
        if remote and not local:  # we have None local value locally, remote counterpart present
            local = remote  # just update tle local value
            common.player.scores[i] = local  # update local score
            common.scores[i] = local  # and also the temporary list

        if local and not remote:  # we have a local value, remote counterpart absent
            needed = True
            print("Sync: local and not remote ")

    print("Local: ", common.player.scores)
    print("Remote: ", common.player.cloud_scores)
    print("Do we need to sync?", needed)

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
    print(txt)
    if txt == 'scores_updated' or txt == 'no_result':
        common.player.online = common.ONLINE
    else:
        common.player.online = common.OFFLINE
        print("COULD NOT SYNC")


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
