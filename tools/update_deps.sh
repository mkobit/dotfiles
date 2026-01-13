#!/bin/bash
set -euo pipefail

# Function to update Python dependencies
update_python() {
    echo "Updating Python dependencies..."
    # Update requirements.lock.txt
    bazel run //:requirements.update
}

# Main execution
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 --python-only"
    exit 1
fi

case "$1" in
    --python-only)
        update_python
        ;;
    *)
        echo "Unknown argument: $1"
        exit 1
        ;;
esac
