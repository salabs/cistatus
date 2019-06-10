import logging
import json
import argparse
import os
import requests

try:
    from .providers import find_ci_provider
except ImportError:
    from providers import find_ci_provider

GITHUB_BASE = os.environ.get("GITHUB_BASE", "https://api.github.com")
GITHUB_STATUS_URL = GITHUB_BASE + "/repos/{repo_name}/statuses/{sha}?access_token={token}"
CISTATUS_API_TOKEN = os.environ.get('CISTATUS_API_TOKEN', None)
JOB_STATES = ('pending', 'success', 'error', 'failure')
ACTIVE_CI = find_ci_provider()
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def update_status(repo_name, sha, state, desc='CI Status', target_url=None, context=None, token=None):
    url = GITHUB_STATUS_URL.format(repo_name=repo_name, sha=sha, token=token)
    LOGGER.debug(ACTIVE_CI)
    params = dict()
    if desc:
        params['description'] = desc
    if state:
        params["state"] = state
    if target_url:
        params["target_url"] = target_url
    if context:
        params["context"] = context

    headers = {"Content-Type": "application/json"}
    LOGGER.debug("Setting status on %s %s to %s", repo_name, sha, state)
    result = requests.post(url, data=json.dumps(params), headers=headers)
    LOGGER.debug("Response: %s", result.status_code)
    return result.status_code in [200, 201]

def is_not_none(val):
    if val:
        return val
    raise ValueError("Value must be provided")


def main():
    require_values = ACTIVE_CI.ci_type == "CIBase"

    require_token = CISTATUS_API_TOKEN is None

    parser = argparse.ArgumentParser(description='Set Build Status')
    parser.add_argument('--repo', required=require_values, type=is_not_none, default=ACTIVE_CI.repo, help="user/repo")
    parser.add_argument('--sha', required=require_values, type=is_not_none, default=ACTIVE_CI.commit_sha)
    parser.add_argument('--pr', required=require_values, type=is_not_none, default=ACTIVE_CI.pr)
    parser.add_argument('--status', choices=JOB_STATES, required=True)
    parser.add_argument('--url', help="Job url")
    parser.add_argument('--description', help="Job Description", default="CI Status")
    parser.add_argument('--context', help="Job context", default="default")
    parser.add_argument('--token', required=require_token, default=CISTATUS_API_TOKEN, help="Github API Token")

    args = parser.parse_args()

    result = update_status(args.repo, args.sha, args.status, desc=args.description, target_url=args.url, context=args.context, token=args.token)
    LOGGER.info("Succeeded: %s", result)

if __name__ == '__main__':
    main()
