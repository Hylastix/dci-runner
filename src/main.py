"""
File: main.py
Project: dci-runner
Created Date: 4 Aug 2025
Author: Clemens Albrecht
-----
Last Modified: 18 Sep 2025
Modified By: Clemens Albrecht
-----
Copyright (c) 2025 Hylastix GmbH
------------------------------------------------------------------
"""

import os
import json
import urllib3
import structlog

from client import Client
from podman import PodmanClient
from client.client import Job
from container_manager import ContainerManager
from podman.errors import ContainerError
from multiprocessing import Process
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedError

log: structlog.stdlib.BoundLogger = structlog.get_logger()


class Config:
    def __init__(
        self,
        username,
        password,
        host,
        port,
        image_version,
        network_name,
        sonar_host,
        sonar_port,
    ) -> None:
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.image_version = image_version
        self.network_name = network_name
        self.sonar_host = sonar_host
        self.sonar_port = sonar_port


class JobProcess(Process):
    def __init__(self, config: Config, job: Job) -> None:
        super().__init__()
        self.config = config
        self.job = job

    def run(self):
        process_job(self.config, self.job)


def process_job(config: Config, job: Job):
    http = urllib3.PoolManager()
    client = Client(http, config.host, config.port)
    client.login(config.username, config.password)

    with PodmanClient() as podman_client:
        container_manager = ContainerManager(podman_client)
        image = container_manager.fetch_image(config.image_version)
        try:
            output: str = container_manager.run_container(
                image,
                job,
                config.network_name,
                f"http://{config.sonar_host}:{config.sonar_port}",
            )  # type: ignore
            measurements = json.loads(output)
        except ContainerError as error:
            measurements = {
                "vulnDensity": -1.0,
                "secDensity": -1.0,
                "bugDensity": -1.0,
                "smellDensity": -1.0,
                "commentDensity": -1.0,
                "hasLicense": -1.0,
                "usesCI": -1.0,
                "codeCoverage": -1.0,
                "busFactor": -1.0,
                "releaseFrequency": -1.0,
                "managesDeps": -1.0,
                "popularity": -1.0,
            }

        client.upload_measurements(job.measurement_id, measurements)


def main():
    username: str = os.getenv("DCI_USER", default="")
    password: str = os.getenv("PASSWORD", default="")
    host: str = os.getenv("HOST", default="")
    port: str = os.getenv("PORT", default="")
    image_version: str = os.getenv("IMAGE_VERSION", "")
    network_name: str = os.getenv("NETWORK_NAME", "dci")
    sonar_host: str = os.getenv("SONAR_HOST", "sonarqube")
    sonar_port: str = os.getenv("SONAR_PORT", "9000")

    if username == "" or password == "" or host == "":
        print("Username, password and host have to be provided")
        exit(1)

    config = Config(
        username,
        password,
        host,
        port,
        image_version,
        network_name,
        sonar_host,
        sonar_port,
    )

    http = urllib3.PoolManager()
    client = Client(http, config.host, config.port)
    client.login(config.username, config.password)

    socket = connect(
        uri=f"ws://{config.host}:{config.port}/jobs",
        additional_headers={"Authorization": f"Bearer {client.token}"},
    )

    while True:
        log.info("Waiting for job...")
        try:
            msg = socket.recv(timeout=30)
            try:
                job_dict = json.loads(msg)
                job = Job(
                    job_dict["measurement_id"],
                    job_dict["project_name"],
                    job_dict["project_version"],
                    job_dict["github_url"],
                    job_dict["purl"],
                )
                log.info("Starting job: %s", job.project_name)
                p = JobProcess(config, job)
                p.start()
            except json.JSONDecodeError as e:
                log.error("Couldn't decode message: %s", e)
        except TimeoutError:
            socket.pong()
        except ConnectionClosedError:
            socket = connect(
                uri=f"ws://{config.host}:{config.port}/jobs",
                additional_headers={"Authorization": f"Bearer {client.token}"},
            )


if __name__ == "__main__":
    main()
