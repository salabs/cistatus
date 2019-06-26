import argparse
import re
import os
import logging



FILE_NAME_LINE = re.compile(r'^\+\+\+ b/(?P<file_name>.+)')
RANGE_INFORMATION_LINE = re.compile(r'^@@ .+\+(?P<line_number>\d+),')
MODIFIED_LINE = re.compile(r'^\+(?!\+|\+)')
NOT_REMOVED_OR_NEWLINE_WARNING = re.compile(r'^[^-\\]')


logger = logging.getLogger(__name__)


class Patch(object):
    """
    Parses the body of a diff and returns the lines that changed as well as their "position",
    as outlined by GitHub here: https://developer.github.com/v3/pulls/comments/#create-a-comment
    """

    def __init__(self, body=''):
        print(f"BODYLEN: {len(body)}")
        if type(body) == list:
            self.body = "\n".join(body)
        else:
            self.body = body

    @property
    def changed_lines(self):
        """
        A list of dicts in the format:
            {
                'file_name': str,
                'content': str,
                'line_number': int,
                'position': int
            }
        """
        lines = []
        file_name = ''
        line_number = 0
        patch_position = -1
        found_first_information_line = False

        for i, content in enumerate(self.body.splitlines()):
            range_information_match = RANGE_INFORMATION_LINE.search(content)
            file_name_line_match = FILE_NAME_LINE.search(content)

            if file_name_line_match:
                file_name = file_name_line_match.group('file_name')
                found_first_information_line = False
            elif range_information_match:
                line_number = int(range_information_match.group('line_number'))
                if not found_first_information_line:
                    # This is the first information line. Set patch position to 1 and start counting
                    patch_position = 0
                    found_first_information_line = True
            elif MODIFIED_LINE.search(content):
                line = {
                    'file_name': file_name,
                    'content': content,
                    'line_number': line_number,
                    'position': patch_position
                }

                lines.append(line)
                line_number += 1
            elif NOT_REMOVED_OR_NEWLINE_WARNING.search(content) or content == '':
                line_number += 1

            patch_position += 1

        return lines

    def get_patch_position(self, file_name, line_number):
        matching_lines = [line for line in self.changed_lines
                          if line['file_name'] == file_name and line['line_number'] == line_number]

        if len(matching_lines) == 0:
            return None
        elif len(matching_lines) == 1:
            return matching_lines[0]['position']
        else:
            logger.warning('Invalid patch or build.')
            logger.warning('Multiple matching lines found for {file_name} on line '
                           '{line_number}'.format(file_name=file_name, line_number=line_number))



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
