#!/bin/bash
# Dedicated pass-persist bridge script for SNMP.
# Updated to use refactored relative path.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FLAT_FILE="$SCRIPT_DIR/../../../oaDataLogs/SNMP/openair_snmp_objects.txt"

if [ "$1" == "-g" ]; then
    grep "$2" "$FLAT_FILE" | head -n 1 | awk '{print $1 "\n" $2 "\n" $3}'
elif [ "$1" == "-n" ]; then
    grep -A 1 "$2" "$FLAT_FILE" | tail -n 1 | awk '{print $1 "\n" $2 "\n" $3}'
fi
