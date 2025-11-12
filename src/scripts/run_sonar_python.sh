# File: run_sonar_python.sh
# Project: scripts
# Created Date: 25 Sep 2025
# Author: Clemens Albrecht
# -----
# Last Modified: 25 Sep 2025
# Modified By: Clemens Albrecht
# -----
# Copyright (c) 2025 Hylastix GmbH
# ------------------------------------------------------------------

token="${SONAR_TOKEN}"
project_name="${SONAR_PROJECT}"
host="${SONAR_HOST}"

pysonar --sonar-project-key=${project_name} --sonar-host-url=${host} --token=${token} --sonar-project-name=${project_name}
