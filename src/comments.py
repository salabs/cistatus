import logging
import json
import argparse
import os
import requests
import sys
import re
from xmlschema import XMLSchema
from pprint import pprint
import os
from unidiff import PatchSet

try:
    from .providers import find_ci_provider, gitroot, gitdiff
except ImportError:
    from providers import find_ci_provider, gitroot, gitdiff


try:
    from .utils import EnvDefault, valid_repo_name, valid_token, valid_pr, valid_file, valid_sha, pick
except ImportError:
    from utils import EnvDefault, valid_repo_name, valid_token, valid_pr, valid_file, valid_sha, pick


GITHUB_BASE = os.environ.get("GITHUB_BASE", "https://api.github.com")
GITHUB_PR_COMMENTS_URL = GITHUB_BASE + "/repos/{repo_name}/pulls/{pull_request}/comments?access_token={token}"

ACTIVE_CI = find_ci_provider()
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def format_filename(name):
    root = gitroot()
    for f in [os.path.join(root, name), name]:
        full_name = os.path.abspath(f)
        if os.path.exists(full_name):
            return full_name[len(root)+1:]

    return name

def change_in_diff(filename, row, diff):
    def file_in_diff(fn):
        if filename == fn.path:
            return True
        elif os.path.join("a", filename) == fn.source_file:
            return True
        elif os.path.join("b", filename) == fn.target_file:
            return True
        return False

    def line_in_hunk():
        for ps in diff:
            if file_in_diff(ps):
                for hunk in ps:
                    r = range(hunk.target_start, hunk.target_start + hunk.target_length + 1)
                    if row in r:
                        return True
        return False

    b = line_in_hunk()
    return line_in_hunk()


def get_next(links):
    for tmpurl in links:
        if tmpurl['rel'] == 'next':
            return tmpurl['url']
    return None

def update_comments(junit = None, repo_name = None, pull_request = None, sha = None, target_branch = "master", token = None):
    url = GITHUB_PR_COMMENTS_URL.format(repo_name=repo_name, pull_request=pull_request, token=token)
    headers = {"Content-Type": "application/json"}

    diff = PatchSet(gitdiff(sha))

    params = dict()
    params['direction']='asc'
    params['sort']='created'
    link_extractor = r"<(?P<NEXT>.*)>; rel=\"next\", <(?P<LAST>.*).*>"
    link_matcher = re.compile(link_extractor)
    result = requests.get(url, data=json.dumps(params), headers=headers)
    existing_comments = []
    while True:
        body = json.loads(result.content.decode('utf8'))
        for i in body:
            tmp = pick(i, ["commit_id", "path", "position", "body"])
            tmp['path'] = format_filename(tmp['path'])
            existing_comments.append(tmp)
        links = result.headers.get('Link', None)
        if links:

            links = requests.utils.parse_header_links(links)
            next_url = get_next(links)
            if next_url:
                result = requests.get(next_url, headers=headers)
            else:
                break

    payload  = dict()
    matcher = r".*:\d{1,}:\d{1,}:\ .*"
    junit_schema = XMLSchema("data/cistatus.xsd")
    report = junit_schema.to_dict(junit)
    for testsuite in report['testsuite']:
        for testcase in testsuite['testcase']:
            errors = testcase.get('error', False)
            failures = testcase.get('failure', False)
            filename = format_filename(testcase['@file'])
            row = int(testcase['@line'])
            if errors or failures and change_in_diff(filename, row, diff):
                payload  = dict()
                payload['commit_id'] = sha
                payload['path'] = filename

                payload['position'] = row
                if errors:
                    payload['body'] = testcase['error']['@message']
                if failures:
                    payload['body'] = testcase['failure']['@message']
                if payload not in existing_comments:
                    result = requests.post(url, data=json.dumps(payload), headers=headers)

    return False


def main():
    parser = argparse.ArgumentParser(description='Set Review Comments')
    parser.add_argument('--repo', required=True, type=valid_repo_name, help="user/repo", action=EnvDefault, envvar=ACTIVE_CI.REPO_ENV)
    parser.add_argument('--pr', required=True, type=valid_pr, action=EnvDefault, envvar=ACTIVE_CI.PR_ENV)
    parser.add_argument('--sha', required=True, type=valid_sha, action=EnvDefault, envvar=ACTIVE_CI.SHA_ENV)
    parser.add_argument('--token', required=True, type=valid_token, help="Github API Token", action=EnvDefault, envvar="GITHUB_ACCESS_TOKEN")
    parser.add_argument('junitreport', type=valid_file, default=sys.stdin)

    args = parser.parse_args()
    print(args)
    result = update_comments(args.junitreport, args.repo, args.pr, args.sha, token=args.token)
    LOGGER.info("Succeeded: %s", result)


if __name__ == '__main__':
    main()
