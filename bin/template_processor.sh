#!/bin/bash
# Helper script for processing template files
# This script replaces template variables with actual values

TEMPLATE_FILE="$1"
OUTPUT_FILE="$2"
VARS_FILE="$3"

# Check if parameters are provided
if [ -z "$TEMPLATE_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo "Usage: $0 <template_file> <output_file> [vars_file]"
    exit 1
fi

# Create a temporary file
TMP_FILE=$(mktemp)

# Copy template to temp file
cp "$TEMPLATE_FILE" "$TMP_FILE"

# If vars file is provided, use it to replace variables
if [ -n "$VARS_FILE" ] && [ -f "$VARS_FILE" ]; then
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        [[ "$key" =~ ^[[:space:]]*$ || "$key" =~ ^[[:space:]]*# ]] && continue
        
        # Trim whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)
        
        # Replace template variables
        sed -i.bak "s|{{$key}}|$value|g" "$TMP_FILE"
    done < "$VARS_FILE"
fi

# Process any environment variables
for var in $(env); do
    key=$(echo "$var" | cut -d= -f1)
    value=$(echo "$var" | cut -d= -f2-)
    
    # Replace template variables that match environment variables prefixed with DOTFILE_
    if [[ "$key" == DOTFILE_* ]]; then
        real_key=${key#DOTFILE_}
        sed -i.bak "s|{{$real_key}}|$value|g" "$TMP_FILE"
    fi
done

# Move temporary file to output
mkdir -p "$(dirname "$OUTPUT_FILE")"
mv "$TMP_FILE" "$OUTPUT_FILE"

echo "Processed template: $TEMPLATE_FILE -> $OUTPUT_FILE"
exit 0