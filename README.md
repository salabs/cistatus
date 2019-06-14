CISTATUS
========

# Demo
![](demos/cistatus_demo.gif)

# About

cistatus is a tool that can explicitly set the pull request check status into github pull requests. For example, if you have multiple checks within a single job but you wish to expose each of those steps as separate checks in github, you can use this tool to expose those extra steps.

cistatus can dig relevant information from the enviroment variables exposed by most ci systems. Currently supported:

 * Azure Devops
 * Travis
 * CircleCI
 * AppVeyor
 * Shippable
 * CodeBuild

This means that if cistatus is executed within build nodes of any of these systems,  repository, pr and sha information is read from the environment variables.

# Why

Use-case for writing this came out of frustration to expose multiple test reports into a github pull request itself from Azure DevOps pipeline builds. With cistatus, one could now have a overall status check exposed in the pull request - if needed - and then add additional checks that each can link into a specific result set without the need to go dig deep in the build artifacts or build logs.


Installation
============

```
pip install cistatus
```

Integration
===========

cistatus has functionality to automatically detect the CI system that it's running on. This happens by checking of 'unique' environment variable of the said ci system and this requires no configuration from the user.

When CI system is detected, a commit sha, repository name and pr values are read off from corresponding environment variables of said ci environment. Eg, if you want to run cistatus from your local shell,  only then you are required to pass in all mandatory command line arguments.

With this approach, when running the script from within any ci slave,  you only need to pass in the status flag to set the checks' status.


Usage
=====

```
[-h] [--repo REPO] [--sha SHA] [--pr PR] [--token TOKEN]
--status {pending,success,error,failure} [--url URL]
[--description DESCRIPTION] [--context CONTEXT]

Set Build Status

optional arguments:
  -h, --help            show this help message and exit
  --repo REPO           user/repo
  --sha SHA
  --pr PR
  --token TOKEN         Github API Token
  --status {pending,success,error,failure}
  --url URL             Job url
  --description DESCRIPTION
                        Job Description
  --context CONTEXT     Job context
```

## --repo
This flag sets the github repository where the status of the pr should be set at. If cistatus detects that its running in any of the supported environments,
this parameter is mandatory as value is read from appropriate environment file but it can still be overwritten from the command line.


## --sha
This flag sets the the commit sha of the pr request. If cistatus detects that its running in any of the supported environments,
this parameter is mandatory as value is read from appropriate environment file but it can still be overwritten from the command line.

## --pr
This flag sets the pull requests number where status is set. If cistatus detects that its running in any of the supported environments,
this parameter is mandatory as value is read from appropriate environment file but it can still be overwritten from the command line.

## --token
This flag sets the personal authentication token. Value can be also set into `GITHUB_ACCESS_TOKEN` environment variable which is adviced if you do not want to leak the token into possibly public build logs.

## --context

This flag sets the string shown as context of the check. Defaults to `default`

## --description

This flag sets the longder description of the context. Defaults to `CI Status`

## --url

This flag sets the url for "Details" link in context  / description for the check.
