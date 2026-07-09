#!/usr/bin/env bash
#
# check_changelog.sh
#
# Fails if a minor/major release (or any 2.0.0.devN pre-release) is being tagged without a
# matching entry in CHANGELOG.rst. Patch releases (only the last X.Y.Z component bumped, with
# no .devN suffix involved) are exempt -- CHANGELOG.rst intentionally doesn't get a heading for
# those, only for the following minor release.
#
# The "previous release" is found by walking this tag's own commit ancestry (`git describe`),
# not by a global version sort across all tags -- this project cuts patch releases from older
# maintenance branches even after newer tags exist elsewhere, so the highest-numbered tag
# overall is not reliably this release's actual predecessor.
#
# Usage:
#   ./check_changelog.sh v1.54.0

set -euo pipefail

TAG="$1"
VERSION="${TAG#v}"

PREV_TAG=$(git describe --tags --abbrev=0 "${TAG}^" 2>/dev/null || true)

if [ -z "$PREV_TAG" ]; then
    echo "No previous tag found in ${TAG}'s history, skipping changelog check."
    exit 0
fi
PREV_VERSION="${PREV_TAG#v}"

is_patch_bump() {
    local new="$1" prev="$2"
    # a .devN release always needs its own entry, on either side of the comparison
    if [[ "$new" == *.dev* || "$prev" == *.dev* ]]; then
        return 1
    fi
    local new_minor prev_minor
    new_minor=$(echo "$new" | cut -d. -f1-2)
    prev_minor=$(echo "$prev" | cut -d. -f1-2)
    [[ "$new_minor" == "$prev_minor" ]]
}

if is_patch_bump "$VERSION" "$PREV_VERSION"; then
    echo "Patch release ${VERSION} (previous: ${PREV_VERSION}) - changelog entry not required."
    exit 0
fi

ESCAPED_VERSION=$(echo "$VERSION" | sed 's/\./\\./g')
if grep -qE "^v${ESCAPED_VERSION}[[:space:]]" CHANGELOG.rst; then
    echo "Found CHANGELOG.rst entry for v${VERSION}."
else
    echo "::error::CHANGELOG.rst has no entry for v${VERSION} (previous release: v${PREV_VERSION}). Add one before tagging a release."
    exit 1
fi
