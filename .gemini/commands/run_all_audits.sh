#!/bin/bash

# Directory containing the audit TOML files
AUDIT_DIR="/home/anthony/Documents/OPEN-AIR/.gemini/commands"
GEMINI_CMD="gemini audit"

echo "Starting all audits..."

# Loop through all TOML files in the directory, excluding AuditAll.toml
find "$AUDIT_DIR" -maxdepth 1 -name "*.toml" ! -name "AuditAll.toml" -print0 | while IFS= read -r -d $'\0' file; do
    echo "--- Running audit: $file ---"
    if $GEMINI_CMD --file "$file"; then
        echo "✅ Audit '$file' completed successfully."
    else
        echo "❌ Audit '$file' failed. See above for details."
        # Optionally, you could exit here if one failure should stop all:
        # exit 1 
    fi
    echo "" # Add a blank line for readability between audits
done

echo "All audits finished."
