#!/bin/bash
set -euo pipefail

# Function to update Bazel version
update_bazel() {
    echo "Checking for latest Bazel version..."
    # Get the latest release tag from GitHub, stripping any 'v' prefix if present (though bazel usually uses x.y.z)
    LATEST_VERSION=$(gh release view --repo bazelbuild/bazel --json tagName --jq .tagName | sed 's/^v//')
    CURRENT_VERSION=$(cat .bazelversion)

    if [ "$LATEST_VERSION" != "$CURRENT_VERSION" ]; then
        echo "Updating Bazel from $CURRENT_VERSION to $LATEST_VERSION"
        echo "$LATEST_VERSION" > .bazelversion
    else
        echo "Bazel is already at the latest version ($CURRENT_VERSION)"
    fi
}

# Function to update Python dependencies
update_python() {
    echo "Updating Python dependencies..."
    # Update requirements.lock.txt
    bazel run //:requirements.update

    # Update BUILD files via Gazelle
    bazel run //:gazelle_python_manifest.update
}

# Main execution
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 [--bazel-only] [--python-only]"
    exit 1
fi

case "$1" in
    --bazel-only)
        update_bazel
        ;;
    --python-only)
        update_python
        ;;
    *)
        echo "Unknown argument: $1"
        exit 1
        ;;
esac
