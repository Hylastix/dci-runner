# File: run_sonar_java.sh
# Project: scripts
# Created Date: 4 Aug 2025
# Author: Clemens Albrecht
# -----
# Last Modified: 18 Sep 2025
# Modified By: Clemens Albrecht
# -----
# Copyright (c) 2025 Hylastix GmbH
# ------------------------------------------------------------------

#!/bin/bash

source /home/dci/.sdkman/bin/sdkman-init.sh

token="${SONAR_TOKEN}"
project_name="${SONAR_PROJECT}"
host="${SONAR_HOST}"

get_project_type() {
  if [[ -f "pom.xml" ]]; then
    echo "maven"
    return 0
  elif [[ -f "build.gradle.kts" ]] || [[ -f "settings.gradle.kts" ]]; then
    echo "gradle-kotlin"
    return 0
  elif [[ -f "build.gradle" ]] || [[ -f "settings.gradle" ]]; then
    echo "gradle-groovy"
    return 0
  else
    echo "none"
    return 1
  fi
}

add_sonarqube_to_gradle() {
  local build_file="build.gradle"

  if grep -q "org.sonarqube" "$build_file"; then
    echo "SonarQube plugin already present in $build_file"
    return 0
  fi

  if grep -q "^plugins\s*{" "$build_file"; then
    sed -i '/^plugins\s*{/a\
  id "org.sonarqube" version "6.2.0.5505"
' "$build_file"
  else
    cat <<'EOF' >temp_build.gradle
plugins {
  id "org.sonarqube" version "6.2.0.5505"
}

EOF
    cat "$build_file" >>temp_build.gradle
    mv temp_build.gradle "$build_file"
  fi

  cat <<EOF >>"$build_file"

sonar {
  properties {
    property "sonar.projectKey", "${project_name}"
    property "sonar.host.url", "${host}"
  }
}
EOF

  echo "SonarQube configuration added to $build_file"
}

add_sonarqube_to_gradle_kotlin() {
  local build_file="build.gradle.kts"

  if grep -q "org.sonarqube" "$build_file"; then
    echo "SonarQube plugin already present in $build_file"
    return 0
  fi

  if grep -q "^plugins\s*{" "$build_file"; then
    sed -i '/^plugins\s*{/a\
    id("org.sonarqube") version "6.2.0.5505"
' "$build_file"
  else
    cat <<'EOF' >temp_build.gradle.kts
plugins {
    id("org.sonarqube") version "6.2.0.5505"
}

EOF
    cat "$build_file" >>temp_build.gradle.kts
    mv temp_build.gradle.kts "$build_file"
  fi

  cat <<EOF >>"$build_file"

sonar {
  properties {
    property("sonar.projectKey", "${project_name}")
    property("sonar.host.url", "${host}")
  }
}
EOF

  echo "SonarQube configuration added to $build_file"
}

run_gradle() {
  if [[ -f "gradlew" ]]; then
    exe="./gradlew"
  else
    sdk install gradle
    exe="gradle"
  fi
  ${exe} clean && ${exe} build testClasses -x test && ${exe} sonar -Dsonar.token="${token}"
}

run_maven() {
  if [[ -f "mvnw" ]]; then
    exe="./mvnw"
  else
    sdk install maven
    exe="mvn"
  fi
  ${exe} clean && ${exe} install -DskipTests &&
    ${exe} org.sonarsource.scanner.maven:sonar-maven-plugin:sonar -Dsonar.token="${token}" \
      -Dsonar.host.url="${host}" -Dsonar.projectKey="${project_name}"
}

run_analysis() {
  local project_type
  project_type=$(get_project_type)

  case "$project_type" in
  "gradle-groovy")
    add_sonarqube_to_gradle
    run_gradle
    ;;
  "gradle-kotlin")
    add_sonarqube_to_gradle_kotlin
    run_gradle
    ;;
  "maven")
    run_maven
    ;;
  *)
    echo "Setup only supported for Maven and Gradle projects currently"
    echo "Detected project type: $project_type"
    return 1
    ;;
  esac
}

run_analysis
