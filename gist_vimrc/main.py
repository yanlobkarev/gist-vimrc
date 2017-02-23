# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os.path
import argparse
from gist import GistAPI, gist


authenticate = gist.authenticate


try:
    import configparser
except ImportError:
    import ConfigParser as configparser


def alternative_config(default):
    """Return the path to the config file in .config directory
    Argument:
        default: the default to use if ~/.config/gist does not exist.
    """
    config_path = os.path.expanduser('~/.config/gist')
    if os.path.isfile(config_path):
        return config_path
    else:
        return default


def xdg_data_config(default):
    """Return the path to the config file in XDG user config directory
    Argument:
        default: the default to use if either the XDG_DATA_HOME environment is
            not set, or the XDG_DATA_HOME directory does not contain a 'gist'
            file.
    """
    config = os.environ.get('XDG_DATA_HOME', '').strip()
    if config != '':
        config_path = os.path.join(config, 'gist')
        if os.path.isfile(config_path):
            return config_path

    return default


class TokenDiscoveryException(ValueError):
    pass


def init_api(token=None):
    if not token:
        config = configparser.ConfigParser()
        config_path = os.path.expanduser('~/.gist')
        config_path = alternative_config(config_path)
        config_path = xdg_data_config(config_path)
        try:
            with open(config_path) as fp:
                config.readfp(fp)
                token = config.get('gist', 'token')
        except Exception as e:
            message = 'Unable to load configuration file: {0}'.format(e)
            raise TokenDiscoveryException(message)

    gapi = MyAPI(token=token, editor='nvim')
    return gapi


def overwrite_token(token):
    config_path = os.path.expanduser('~/.gist')
    with open(config_path, 'w') as config:
        config.write("[gist]\ntoken: " + token)
        # todo: log message


class MyAPI(GistAPI):
    @authenticate.patch
    def update(self, request, gist, vimrc):
        filename = os.path.split(vimrc)[-1]
        content = open(vimrc, 'r').read()
        request.data = json.dumps({
            'description': gist.desc,
            'files': {filename: {'content': content}}
        })
        # ugly huck
        sep = 'gists'
        url = request.url
        request.url = url[:url.index(sep) + len(sep)]
        return self.send(request, gist.id).json()['html_url']


def create(api, vimrc):
    filename = os.path.split(vimrc)[-1]
    content = open(vimrc, 'r').read()
    data = {filename: {'content': content}}
    return api.create(filename, data)


def get(api, vimrc):
    filename = os.path.split(vimrc)[-1]
    gists = list(filter(lambda g: g.desc == filename, api.list()))
    if len(gists) > 0:
        # TODO: notify if found several same named gists
        return gists[0]


def push(api, vimrc):
    vim_gist = get(api, vimrc)
    if vim_gist:
        res = api.update(vim_gist, vimrc)
    else:
        res = create(api, vimrc)
    return bool(res)


class NoGistToPullError(ValueError):
    pass


def pull(api, vimrc):
    vim_gist = get(api, vimrc)
    if not vim_gist:
        raise NoGistToPullError()

    filename = os.path.split(vimrc)[-1]
    if vim_gist:
        content = api.content(vim_gist.id)[filename]
        with open(vimrc, 'wb') as vimrc_file:
            vimrc_file.write(content.encode('utf-8'))


def get_args():
    parser = argparse.ArgumentParser()

    def is_valid_file(arg):
        if not os.path.exists(arg):
            parser.error("The file %s does not exist!" % arg)
        return arg
    parser.add_argument('command', type=str, choices=['push', 'pull'])
    parser.add_argument('--vimrc', dest='vimrc', type=is_valid_file, help='A vimrc file path.')
    parser.add_argument('--token', dest='token', type=str, nargs='?', help='A github gist token.')
    return parser.parse_args()


RET_OK = 0
RET_STALETOKEN = 1
RET_UNKNOWNERROR = 2
RET_NOGISTTOPULL = 3


def main():
    args = get_args()
    try:
        api = init_api(token=args.token)
        globals().get(args.command)(api, args.vimrc)
    except TokenDiscoveryException:
        return RET_STALETOKEN
    except Exception as e:
        # TODO: add logging
        return RET_UNKNOWNERROR
    except NoGistToPullError:
        return RET_NOGISTTOPULL
    else:
        if args.token:
            overwrite_token(args.token)
        return RET_OK
