#!/bin/bash
# OPEN-AIR Master SNMP Bridge
FLAT_FILE="/home/anthony/Documents/OPEN-AIR/oaDataSNMP/openair_snmp_objects.txt"
LOG_FILE="/home/anthony/Documents/OPEN-AIR/oaDataSNMP/openair_snmp_set.log"
DEBUG_LOG="/home/anthony/Documents/OPEN-AIR/oaDataSNMP/bridge_debug.log"

# Log all requests for debugging
echo "[$(date)] REQ: $1 $2" >> $DEBUG_LOG

# Handle SET (-s)
if [ "$1" = "-s" ]; then
    echo "-s $2 $3 $4" >> $LOG_FILE
    exit 0
fi

awk -F':' -v cmd="$1" -v target="$2" '
    function norm(oid) {
        gsub(/^[."]+|[."]+$/, "", oid);
        split(oid, p, ".");
        out = "";
        for (i=1; i<=length(p); i++) {
            out = out sprintf("%010d.", p[i]);
        }
        return out;
    }
    BEGIN { 
        t = norm(target); 
        found = 0; 
    }
    {
        c = norm($1);
        if (cmd == "-g") {
            if (c == t) {
                # Print OID without leading dot
                print ($1 ~ /^\./ ? substr($1, 2) : $1);
                print "string";
                print substr($0, index($0, ":") + 1);
                found = 1;
                exit 0;
            }
        } else if (cmd == "-n") {
            if (c > t) {
                # Print OID without leading dot
                print ($1 ~ /^\./ ? substr($1, 2) : $1);
                print "string";
                print substr($0, index($0, ":") + 1);
                found = 1;
                exit 0;
            }
        }
    }
    END { if (!found) exit 1; }
    ' "$FLAT_FILE"

if [ $? -ne 0 ]; then
    echo "[$(date)] NOT FOUND: $2" >> $DEBUG_LOG
fi
