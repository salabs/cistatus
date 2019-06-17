import argparse
import re
import os
import logging


class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if not default and envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

def is_not_none(func):
    def wrapper(*args, **kwargs):
        if args[0]:
            return func(*args, **kwargs)
        raise ValueError()

    return wrapper


@is_not_none
def valid_file(filename):
    try:
        with open(filename, 'r') as fp:
            pass
    except Exception as e:
        ## todo catch all appropriate errors here for better reporting
        raise ValueError()
    return filename


@is_not_none
def valid_repo_name(val):
    part = r"[a-z\d](?:[a-z\d]|-(?=[a-z\d])){0,38}"
    full = f"^{part}\/{part}$"
    matcher = re.compile(full)
    if matcher.match(val):
        return val
    raise ValueError()


@is_not_none
def valid_sha(val):
    part = r"[0-9a-f]{5,40}"
    full = f"^{part}$"
    matcher = re.compile(full)
    if matcher.match(val):
        return val
    raise ValueError()


@is_not_none
def valid_pr(val):
    try:
        int(val)
        return val
    except ValueError:
        raise


@is_not_none
def valid_token(val):
    part = r"[0-9a-f]{40}"
    full = f"^{part}$"
    matcher = re.compile(full)
    if matcher.match(val):
        return val
    raise ValueError()


def pick(local_dict, wanted_keys):
    d = dict()
    for key in local_dict:
        if key in wanted_keys:
            d[key] = local_dict[key]
    return d
