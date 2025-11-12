'''
File: client.py
Project: client
Created Date: 4 Aug 2025
Author: Clemens Albrecht
-----
Last Modified: 18 Sep 2025
Modified By: Clemens Albrecht
-----
Copyright (c) 2025 Hylastix GmbH
------------------------------------------------------------------
'''

import json
import structlog

from urllib3 import PoolManager
from urllib.parse import urlencode

log: structlog.stdlib.BoundLogger = structlog.get_logger()


class Client:
    def __init__(self, http: PoolManager, host: str, port: str):
        self.http = http
        self.host = host
        self.port = port
        self.token = ""

    def login(self, username: str, password: str):
        url = f"http://{self.host}:{self.port}/login"
        body = {"username": username, "password": password}

        resp = self.http.request(
            "POST",
            url=url,
            body=urlencode(body),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status == 200:
            self.token = resp.json()["access_token"]
        else:
            log.warn("Unable to login: Status %s", resp.status)
            log.warn("Message: %s", resp.data)

    def upload_measurements(self, id: int, measurements: dict):
        url = f"http://{self.host}:{self.port}/api/measurement/{id}"
        body = json.dumps(measurements)
        resp = self.http.request(
            "PUT",
            url=url,
            body=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
        )
        if resp.status != 200:
            log.warn("Unable to create measurement: Status: %s", resp.status)
            log.warn("Message: %s", resp.data)


class Job:
    def __init__(
        self,
        measurement_id: int,
        project_name: str,
        project_version: str,
        github_url: str,
        purl: str,
    ):
        self.measurement_id = measurement_id
        self.project_name = project_name
        self.project_version = project_version
        self.github_url = github_url
        self.purl = purl
