# Connect to Ollama running on the Windows host via WSL mirrored networking
if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
    export OLLAMA_HOST="http://localhost:11434"
fi
