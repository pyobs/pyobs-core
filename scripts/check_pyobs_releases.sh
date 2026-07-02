#!/usr/bin/env bash
#
# check_pyobs_releases.sh
#
# Lists the latest GitHub release for every public repo in the pyobs org,
# including pre-releases (e.g. 2.0.0.dev1), which `gh release list` shows
# but the GitHub web UI hides by default behind "Stable version available".
#
# Requires: gh (GitHub CLI), authenticated (`gh auth login`)
#
# Usage:
#   ./check_pyobs_releases.sh                  # all public repos in pyobs org
#   ./check_pyobs_releases.sh pyobs-core pyobs-gui   # only specific repos

set -euo pipefail

ORG="pyobs"

# Optional column width for repo name (for alignment)
NAME_WIDTH=24

print_header() {
    printf "%-${NAME_WIDTH}s %-20s %-12s %s\n" "REPO" "LATEST RELEASE" "TYPE" "PUBLISHED"
    printf "%-${NAME_WIDTH}s %-20s %-12s %s\n" "----" "--------------" "----" "---------"
}

check_repo() {
    local repo="$1"

    # Get the most recent release (including pre-releases), sorted by date
    local result
    result=$(gh release list --repo "$ORG/$repo" --limit 1 --json tagName,isPrerelease,publishedAt \
        --jq '.[0] | "\(.tagName)\t\(.isPrerelease)\t\(.publishedAt)"' 2>/dev/null) || true

    if [ -z "$result" ]; then
        printf "%-${NAME_WIDTH}s %-20s %-12s %s\n" "$repo" "(no releases)" "-" "-"
        return
    fi

    local tag prerelease published type
    IFS=$'\t' read -r tag prerelease published <<< "$result"

    if [[ "$tag" == *"dev"* || "$tag" == *"alpha"* || "$tag" == *"beta"* || "$tag" == *"rc"* || "$prerelease" = "true" ]]; then
        type="pre-release"
    else
        type="stable"
    fi

    # Trim time from published date, keep just the date
    published="${published%%T*}"

    printf "%-${NAME_WIDTH}s %-20s %-12s %s\n" "$repo" "$tag" "$type" "$published"
}

main() {
    if ! command -v gh &> /dev/null; then
        echo "Error: gh (GitHub CLI) is not installed. See https://cli.github.com/" >&2
        exit 1
    fi

    if ! gh auth status &> /dev/null; then
        echo "Error: not authenticated with gh. Run 'gh auth login' first." >&2
        exit 1
    fi

    print_header

    if [ "$#" -gt 0 ]; then
        # Repos passed explicitly on command line
        for repo in "$@"; do
            check_repo "$repo"
        done
    else
        # Fetch all public, non-archived repos in the org
        repos=$(gh repo list "$ORG" --limit 200 --no-archived --source \
            --json name,isPrivate --jq '.[] | select(.isPrivate == false) | .name' | sort)

        if [ -z "$repos" ]; then
            echo "No public repos found in org '$ORG' (or insufficient permissions)." >&2
            exit 1
        fi

        while IFS= read -r repo; do
            check_repo "$repo"
        done <<< "$repos"
    fi
}

main "$@"