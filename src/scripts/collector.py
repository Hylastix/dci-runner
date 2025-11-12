#!/usr/bin/env python

# ------------------------------------------------------------------
# File: collector.py
# Project: scripts
# Created Date: 4 Aug 2025
# Author: Clemens Albrecht
# -----
# Last Modified: 18 Sep 2025
# Modified By: Clemens Albrecht
# -----
# Copyright (c) 2025 Hylastix GmbH
# ------------------------------------------------------------------

import json
import os
import subprocess
import re
from time import sleep
from datetime import datetime
from typing import TypeVar, Type

import requests
import msgspec

projectName = os.environ.get("PROJECT_NAME")
projectVersion = os.environ.get("PROJECT_VERSION")
githubUrl = os.environ.get("GITHUB_URL")
githubToken = os.environ.get("GITHUB_TOKEN")
purl = os.environ.get("PURL")
sonarToken = os.environ.get("SONAR_TOKEN")
sonarHost = os.environ.get("SONAR_HOST")
librariesToken = os.environ.get("LIBRARIES_TOKEN")
sourceDir = os.environ.get("SOURCE_DIR")


class Version(msgspec.Struct):
    number: str
    published_at: datetime


# Init measurements dict
measurements = {
    "vulnDensity": 0.0,
    "secDensity": 0.0,
    "bugDensity": 0.0,
    "smellDensity": 0.0,
    "commentDensity": 0.0,
    "hasLicense": 0.0,
    "usesCI": 0.0,
    "codeCoverage": 0.0,
    "busFactor": 0.0,
    "releaseFrequency": 0.0,
    "managesDeps": 0.0,
    "popularity": 0.0,
}


T = TypeVar("T")


def get_measure_value(key: str, measures: dict, value_type: Type[T]) -> T:
    value: str = next(measure for measure in measures if measure["metric"] == key)[
        "value"
    ]

    return value_type(value)


def get_scorecard_value(key: str, checks: dict) -> int:
    value: str = next(check for check in checks if check["name"] == key)["score"]
    return int(value)


# Wait for anaysis to be completed
ceUrl = f"{sonarHost}/api/ce/component"
querystring = {"component": f"{projectName}"}
headers = {"Authorization": f"Bearer {sonarToken}"}
while True:
    resp = requests.request("GET", ceUrl, headers=headers, params=querystring)
    if resp.status_code == 200:
        data = resp.json()
        if not data["queue"] and data["current"]["status"] == "SUCCESS":
            break
    else:
        print("Can't reach sonarqube")
        exit("1")

    sleep(20)


# Retrieve Sonarqube Measurements
sonarUrl = f"{sonarHost}/api/measures/component"
querystring = {
    "component": f"{projectName}",
    "metricKeys": "code_smells,bugs,comment_lines_density,coverage,lines,vulnerabilities",
}
headers = {"Authorization": f"Bearer {sonarToken}"}
response = requests.request("GET", sonarUrl, headers=headers, params=querystring)
measures = response.json()["component"]["measures"]

if not measures:
    exit(2)

# Lines of Code for normalization########################
loc = get_measure_value("lines", measures, float)  #
#########################################################

securityIssues = get_measure_value("vulnerabilities", measures, int) / loc
measurements["secDensity"] = 1.0 - min((securityIssues / 27.0), 1.0)

bugs = get_measure_value("bugs", measures, int) / loc
measurements["bugDensity"] = 1.0 - min((bugs / 27.0), 1.0)

codeSmells = get_measure_value("code_smells", measures, int) / loc
measurements["smellDensity"] = 1.0 - min((codeSmells / 27.0), 1.0)

commentDensity = get_measure_value("comment_lines_density", measures, float)
measurements["commentDensity"] = commentDensity / 100.0

coverage = get_measure_value("coverage", measures, float)
measurements["codeCoverage"] = coverage

# Retrieve CVE infos
osvUrl = "https://api.osv.dev/v1/query"
payload = {"package": {"purl": purl}, "version": projectVersion}
headers = {"Content-Type": "application/json"}
response = requests.request("POST", osvUrl, json=payload, headers=headers)
if not response.json():
    cves = 0
else:
    cves = len(response.json()["vulns"]) / loc
measurements["vulnDensity"] = 1.0 - min((cves / 27), 1.0)

# Calculate bus factor
completedProcess = subprocess.run(
    args=["/usr/local/bin/bus-factor", "summary", "--type", "avl"],
    capture_output=True,
    cwd=sourceDir,
)
result = json.loads(completedProcess.stdout)
busFactor = int(result["value"]) / 10.0
measurements["busFactor"] = min(busFactor, 1.0)

# Get scorecard scores
completedProcess: subprocess.CompletedProcess = subprocess.run(
    args=[
        "/usr/local/bin/scorecard",
        "--format",
        "json",
        "--repo",
        f"{githubUrl}",
        "--checks",
        "License,CI-Tests,Dependency-Update-Tool",
    ],
    env={"GITHUB_AUTH_TOKEN": githubToken},
    capture_output=True,
)
result = json.loads(completedProcess.stdout)
checks = result["checks"]

usesCI = get_scorecard_value("CI-Tests", checks)
measurements["usesCI"] = usesCI / 10.0

hasLicense = get_scorecard_value("License", checks)
measurements["hasLicense"] = hasLicense / 10.0

managesDeps = get_scorecard_value("Dependency-Update-Tool", checks)
measurements["managesDeps"] = managesDeps / 10.0

# Get popularity and releases from libraries.io
librariesUrl = f"https://libraries.io/api/Pypi/{projectName}"
querystring = {"api_key": librariesToken}
response = requests.request("GET", librariesUrl, params=querystring).json()
stars = response["stars"]
popularity = stars / 3800.0
measurements["popularity"] = min(popularity, 1.0)

numReleases = len(response["versions"])

versions: list[Version] = msgspec.json.decode(
    json.dumps(response["versions"]), type=list[Version]
)
versions.sort(key=lambda v: v.published_at)

firstRelease = versions[0]
lastRelease = versions[-1]

diff = lastRelease.published_at - firstRelease.published_at
age = diff.days
releaseFrequency = ((numReleases / age) * 365) / 36.0
measurements["releaseFrequency"] = min(releaseFrequency, 1.0)

print(json.dumps(measurements))
