#!/usr/bin/env bash
# Make the ALE images this checkout pins available locally.
#
# Versions come from packages/ale-run/src/ale/run/releases.json. A published release is
# immutable, so a version the registry already has is pulled rather than rebuilt: a local
# rebuild of the same version would be a different image under the same name. Only a
# version not yet published is built here, for testing before CI publishes it.
#
#   images/build.sh                      every pinned image
#   images/build.sh vm-ubuntu24-base     selected images, by repository name
set -euo pipefail

cd "$(dirname "$0")/.."   # repository root

runtime="${ALE_CONTAINER_RUNTIME:-docker}"
command -v "$runtime" >/dev/null 2>&1 || {
    echo "ERROR: $runtime not found — see 'just doctor'" >&2
    exit 1
}

releases=$(python3 packages/ale-run/src/ale/run/releases.py "$@")
while read -r repository version recorded dockerfile context inputs; do
    name="ghcr.io/agentslastexam/${repository}"
    read -r -a input_paths <<<"$inputs"
    content=$(git ls-files -s -- "${input_paths[@]}" | sha256sum | cut -c1-12)
    if [[ "$content" != "$recorded" ]]; then
        echo "ERROR: ${repository} sources changed since ${version} (${recorded} -> ${content});" \
            "give it a new version in releases.json" >&2
        exit 1
    fi
    if "$runtime" buildx imagetools inspect "${name}:${version}" >/dev/null 2>&1; then
        echo ">> pulling published ${name}:${version}"
        "$runtime" pull "${name}:${version}"
        continue
    fi
    echo ">> building unpublished ${name}:${version} (${content})"
    "$runtime" build \
        --file "$dockerfile" \
        --tag "${name}:${version}" \
        --tag "${name}:${content}" \
        --label "ale.content_hash=${content}" \
        --label "ale.image_version=${version}" \
        "$context"
done <<<"$releases"
