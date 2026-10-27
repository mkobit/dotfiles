# Shared logging utilities for chezmoi scripts

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
_chezmoi_log() {
    local timestamp
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)" || timestamp=unknown
    printf '%s %b[%s]%b %b\n' "$timestamp" "$1" "$2" "$NC" "$3" 2>/dev/null || true
}

log_info() {
    _chezmoi_log "$BLUE" INFO "$1"
}

log_success() {
    _chezmoi_log "$GREEN" SUCCESS "$1"
}

log_warn() {
    _chezmoi_log "$YELLOW" WARN "$1"
}

log_error() {
    _chezmoi_log "$RED" ERROR "$1"
}

# Utility functions
check_command() {
    command -v "$1" >/dev/null 2>&1
}

check_sudo_access() {
    if sudo -n true 2>/dev/null; then
        return 0
    fi
    if [ -t 0 ] && [ -t 1 ] && [ -z "${ANTIGRAVITY_AGENT:-}" ] && [ -z "${CI:-}" ] && [ "${DEBIAN_FRONTEND:-}" != "noninteractive" ]; then
        return 0
    fi
    return 1
}
