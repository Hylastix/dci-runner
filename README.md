# DCI-RUNNER

This is the job runner for DCI. It receives jobs via websocket from the platform and executes them.

## Requirements

- podman and podman-compose have to be installed
- podman user socket has to be enabled

## Configuration

- Add file called .runner.env to root directory with necessary information to configure the runner:

```toml
DCI_USER=runner
PASSWORD=<password>
HOST=platform
PORT=9080
IMAGE_VERSION=0.2
NETWORK_NAME=dci
SONAR_HOST=sonarqube
SONAR_PORT=9000
```

- Add file called .secrets.env to root directory with necessary information to run the collector inside the container:

```bash
export GITHUB_TOKEN=""
export SONAR_TOKEN=""
export LIBRARIES_TOKEN=""
```

## How to run

1. Create the dci container network if it doesn't already exist:

```bash
podman network create --ignore dci
```

2. Start sonarqube once, and login with default credentials (should be admin/admin):

```bash
podman-compose up -d sonarqube
```

3. Retrieve an API user token from the user settings and add it to .secrets.env
4. Build and start the runner:

```bash
podman-compose build
podman-compose up -d runner
```
