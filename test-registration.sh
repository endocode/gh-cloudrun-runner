#!/usr/bin/env bash
set -eEuo pipefail

TOKEN=$(curl -s -X POST -H "authorization: token ${TOKEN}" "https://api.github.com/orgs/${ORGANIZATION}/actions/runners/registration-token" | jq -r .token)

cleanup() {
  ./config.sh remove --token "${TOKEN}"
}

./config.sh \
  --url "https://github.com/${ORGANIZATION}" \
  --token "${TOKEN}" \
  --name "${NAME}" \
  --unattended \
  --ephemeral \
  --work _work

./run.sh

cleanup
