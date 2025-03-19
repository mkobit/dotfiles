#!/bin/bash
# Script to install the Bazel-generated .vimrc files
set -euo pipefail

# Help function
print_help() {
  echo "Usage: $0 [OPTIONS]"
  echo ""
  echo "Install Bazel-generated .vimrc files"
  echo ""
  echo "Options:"
  echo "  -v, --variant VARIANT    Specify variant (default, work, personal)"
  echo "  -m, --mode MODE          Installation mode (symlink, source, print)"
  echo "  -f, --force              Force overwrite of existing .vimrc"
  echo "  -h, --help               Show this help message"
}

# Default values
VARIANT="default"
MODE="print"
FORCE=0

# Parse options
while [[ $# -gt 0 ]]; do
  case "$1" in
    -v|--variant)
      VARIANT="$2"
      shift 2
      ;;
    -m|--mode)
      MODE="$2"
      shift 2
      ;;
    -f|--force)
      FORCE=1
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      print_help
      exit 1
      ;;
  esac
done

# Map variant to target
case "${VARIANT}" in
  default)
    TARGET="//modules/vim:vimrc"
    ;;
  work)
    TARGET="//modules/vim:work_vimrc"
    ;;
  personal)
    TARGET="//modules/vim:personal_vimrc"
    ;;
  *)
    echo "Invalid variant: ${VARIANT}"
    print_help
    exit 1
    ;;
esac

# Build the target
echo "Building ${TARGET}..."
bazel build "${TARGET}"

# Get the bazel-bin directory
BAZEL_BIN=$(bazel info bazel-bin)

# Determine the generated file path
case "${VARIANT}" in
  default)
    VIMRC_PATH="${BAZEL_BIN}/modules/vim/vimrc.vimrc"
    ;;
  work)
    VIMRC_PATH="${BAZEL_BIN}/modules/vim/work_vimrc.vimrc"
    ;;
  personal)
    VIMRC_PATH="${BAZEL_BIN}/modules/vim/personal_vimrc.vimrc"
    ;;
esac

# Check if the file exists
if [[ ! -f "${VIMRC_PATH}" ]]; then
  echo "Error: Generated file not found at ${VIMRC_PATH}"
  exit 1
fi

echo "Generated file: ${VIMRC_PATH}"
echo "First 5 lines:"
head -n 5 "${VIMRC_PATH}" | sed 's/^/  /'

# Install based on mode
case "${MODE}" in
  symlink)
    # Check if .vimrc already exists
    if [[ -f "${HOME}/.vimrc" && ${FORCE} -eq 0 ]]; then
      echo "Warning: ~/.vimrc already exists."
      echo "Use -f or --force to overwrite."
      exit 1
    fi
    
    # Create symbolic link
    ln -sf "${VIMRC_PATH}" "${HOME}/.vimrc"
    echo "Created symbolic link: ~/.vimrc -> ${VIMRC_PATH}"
    ;;
    
  source)
    # Check if .vimrc already exists
    if [[ -f "${HOME}/.vimrc" ]]; then
      # Check if the source line already exists
      if grep -q "source ${VIMRC_PATH}" "${HOME}/.vimrc"; then
        echo "Source line already exists in ~/.vimrc"
      else
        # Add the source line
        echo "" >> "${HOME}/.vimrc"
        echo "\" === Begin Bazel generated configuration ===" >> "${HOME}/.vimrc"
        echo "source ${VIMRC_PATH}" >> "${HOME}/.vimrc"
        echo "\" === End Bazel generated configuration ===" >> "${HOME}/.vimrc"
        echo "Added source line to ~/.vimrc"
      fi
    else
      # Create a new .vimrc with the source line
      echo "\" === Begin Bazel generated configuration ===" > "${HOME}/.vimrc"
      echo "source ${VIMRC_PATH}" >> "${HOME}/.vimrc"
      echo "\" === End Bazel generated configuration ===" >> "${HOME}/.vimrc"
      echo "Created new ~/.vimrc with source line"
    fi
    ;;
    
  print)
    # Just print the path (default behavior)
    echo ""
    echo "To use this configuration:"
    echo ""
    echo "1. Create a symbolic link:"
    echo "   ln -sf ${VIMRC_PATH} ~/.vimrc"
    echo ""
    echo "2. Or source it in your existing .vimrc:"
    echo "   echo 'source ${VIMRC_PATH}' >> ~/.vimrc"
    ;;
    
  *)
    echo "Invalid mode: ${MODE}"
    print_help
    exit 1
    ;;
esac