"""
File: container_manager.py
Project: container_manager
Created Date: 4 Aug 2025
Author: Clemens Albrecht
-----
Last Modified: 18 Sep 2025
Modified By: Clemens Albrecht
-----
Copyright (c) 2025 Hylastix GmbH
------------------------------------------------------------------
"""

from collections.abc import Callable
from typing import Any, Iterable, Mapping
from podman.client import PodmanClient
from podman.domain.containers_manager import ContainersManager
from podman.domain.images import Image
from podman.domain.images_manager import ImagesManager
from client.client import Job


class ContainerManager:
    def __init__(self, client: PodmanClient):
        self.client: PodmanClient = client

    def fetch_image(self, image_version: str) -> Image:
        image_manager: ImagesManager = self.client.images

        if image_manager.exists(f"localhost/dci-container:{image_version}"):
            return image_manager.get(f"localhost/dci-container:{image_version}")
        else:
            build_args = {
                "path": ".",
                "dockerfile": "Dockerfile",
                "tag": f"dci-container:{image_version}",
            }
            (image, _) = image_manager.build(**build_args)
            return image

    def run_container(self, image: Image, job: Job, network: str, sonarqube_host: str):
        container_manager: ContainersManager = self.client.containers
        container_config = {
            "image": image.tags[0],
            "command": "",
            "remove": True,
            "stdout": True,
            "stderr": False,
            "environment": {
                "PROJECT_NAME": job.project_name,
                "PROJECT_VERSION": job.project_version,
                "GITHUB_URL": job.github_url,
                "PURL": job.purl,
                "SONAR_HOST": sonarqube_host,
            },
            "network_mode": "bridge",
            "networks": {network: {"aliases": [network]}},
        }
        return container_manager.run(**container_config)
