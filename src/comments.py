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
    from .providers import find_ci_provider, gitroot, gitdiff, gitancestry
except ImportError:
    from providers import find_ci_provider, gitroot, gitdiff, gitancestry


try:
    from .utils import EnvDefault, valid_repo_name, valid_token, valid_pr, valid_file, valid_sha, pick, Patch
except ImportError:
    from utils import EnvDefault, valid_repo_name, valid_token, valid_pr, valid_file, valid_sha, pick, Patch


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
    position = diff.get_patch_position(filename, row)
    result = position is not None
    print(f"{filename}:{row} is in diff {result}")
    #return False
    return position is not None

def get_next(links):
    for tmpurl in links:
        if tmpurl['rel'] == 'next':
            return tmpurl['url']
    return None

def update_comments(junit = None, repo_name = None, pull_request = None, sha = None, target_branch = "master", token = None):
    url = GITHUB_PR_COMMENTS_URL.format(repo_name=repo_name, pull_request=pull_request, token=token)
    headers = {"Content-Type": "application/json"}

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
            tmp = pick(i, ["commit_id", "path", "position", "body", "original_commit_id"])
            tmp['path'] = format_filename(tmp['path'])
            if tmp['original_commit_id'] != tmp['commit_id']:
                tmp['commit_id'] = tmp['original_commit_id']
            del tmp['original_commit_id']

            existing_comments.append(tmp)
        links = result.headers.get('Link', None)
        if links:

            links = requests.utils.parse_header_links(links)
            next_url = get_next(links)
            if next_url:
                result = requests.get(next_url, headers=headers)
            else:
                break
    with open("comments.json", "w") as out:
        out.write(json.dumps(existing_comments, sort_keys=True, indent=4))

    print(f"EXISTING COMMENTS: {len(existing_comments)}")
    junit_schema = XMLSchema("data/cistatus.xsd")
    report = junit_schema.to_dict(junit)
    orig = target_branch
    for xsha in gitancestry(sha, target_branch):
        print(f"Comparing {xsha} to {orig}")
        diff_data = gitdiff(xsha, orig)
        diff = Patch(diff_data)
        for testsuite in report['testsuite']:
            payload  = dict()
            for testcase in testsuite['testcase']:
                errors = testcase.get('error', False)
                failures = testcase.get('failure', False)
                filename = format_filename(testcase['@file'])
                row = int(testcase.get('@line', 0))
                if errors or failures and change_in_diff(filename, row, diff):
                    payload  = dict()
                    payload['commit_id'] = xsha
                    payload['path'] = filename

                    payload['position'] = diff.get_patch_position(filename, row)
                    print(f"LINE: {row} POSITION: {payload['position']}")
                    if errors:
                        payload['body'] = testcase['error']['@message']
                    if failures:
                        payload['body'] = testcase['failure']['@message']
                    if payload not in existing_comments:
                        result = requests.post(url, data=json.dumps(payload), headers=headers)
                        print(result)
                        print(result.content)
                    else:
                        print("already in")
                    print("PAYLOAD: ", payload)
        orig = xsha

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
