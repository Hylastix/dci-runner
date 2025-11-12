# File: entrypoint.sh
# Project: scripts
# Created Date: 4 Aug 2025
# Author: Clemens Albrecht
# -----
# Last Modified: 18 Sep 2025
# Modified By: Clemens Albrecht
# -----
# Copyright (c) 2025 Hylastix GmbH
# ------------------------------------------------------------------

#!/usr/bin/env bash

source /home/dci/.sdkman/bin/sdkman-init.sh
source /etc/dci/secrets.env

code_dir="/tmp/codeUnderTest"

# Setup variables
project_name="${PROJECT_NAME}"
project_version="${PROJECT_VERSION}"
github_url="${GITHUB_URL}"
purl="${PURL}"
sonar_host="${SONAR_HOST}"

# From environments file
github_token="${GITHUB_TOKEN}"
sonar_token="${SONAR_TOKEN}"
libraries_token="${LIBRARIES_TOKEN}"

# Clone code-under-test
git clone ${github_url} ${code_dir} >&2
cd "$code_dir" || exit

# find correct git tag
tag=$(git tag -l | grep ${project_version} | head -1)

# Checkout specified version
git checkout ${tag} >&2

# Run static analysis
SONAR_TOKEN="${sonar_token}" SONAR_PROJECT="${project_name}" SONAR_HOST="${sonar_host}" /usr/local/bin/run_sonar_python.sh >&2

# Collect all data and send to stdout
PROJECT_NAME="${project_name}" \
  PROJECT_VERSION="${project_version}" \
  GITHUB_URL="${github_url}" \
  GITHUB_TOKEN="${github_token}" \
  PURL="${purl}" \
  SONAR_TOKEN="${sonar_token}" \
  SONAR_HOST="${sonar_host}" \
  LIBRARIES_TOKEN="${libraries_token}" \
  SOURCE_DIR="${code_dir}" /usr/local/bin/collector.py
