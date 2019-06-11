CISTATUS
========

cistatus is a tool that can explicitly set the pull request check status into github pull requests. For example, if you have multiple checks within a single job but you wish to expose each of those steps as separate checks in github, you can use this tool to expose those extra steps.

cistatus can dig relevant information from the enviroment variables exposed by most ci systems. Currently supported:

 * Azure Devops
 * Travis
 * CircleCI
 * AppVeyor
 * Shippable
 * CodeBuild

This means that if cistatus is executed within build nodes of any of these systems,  repository, pr and sha information is read from the environment variables.

Installation
============

```
pip install cistatus
```

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
This flag sets the personal authentication token. Value can be also set into GITHUB_ACCESS_TOKEN environment variable.

## --context

This flag sets the string shown as context of the check. 

## 

