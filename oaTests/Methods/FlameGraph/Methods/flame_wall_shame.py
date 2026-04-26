# oaTests/Methods/FlameGraph/flame_wall_shame.py
#
# Metrics-focused performance report for rapid bottleneck identification.
#
# Author: Anthony Peter Kuzub
# Blog: www.Like.audio (Contributor to this project)
#
# Professional services for customizing and tailoring this software to your specific
# application can be negotiated. There is no charge to use, modify, or fork this software.
#
# Build Log: https://like.audio/category/software/spectrum-scanner/
# Source Code: https://github.com/APKaudio/
# Feature Requests can be emailed to i @ like . audio
#
# Version 20260329.0045.1
#
# Description:
# The 'Wall of Shame' provides a concise, high-density view of the top
# performance offenders. It is optimized for rapid scanning by lead
# developers to identify immediate hotspots in the code that require
# micro-optimization or refactoring.
#
# Architectural Role:
# - Performance Auditor: Highlights the heaviest functions by raw metrics.
# - Rapid Triage Tool: Identifies high-frequency and high-latency offenders.

import html

# --- Architectural Limits ---
MAX_OFFENDERS_PER_CATEGORY = 50
MAX_SUBSYSTEM_BREAKDOWN_ITEMS = 20

def generate_wall_of_shame(performance_stats, ps):
    """
    Generates a concise, metrics-focused performance report.
    Focuses on raw numbers for quick identification of top offenders.
    """
    # 1. Define Categories
    categories = [
        ("CATEGORY 1: BLOCKING / HEAVY PATHS (Cumulative Time)", lambda x: x['cumtime']),
        ("CATEGORY 2: CPU INTENSIVE LOOPS (Self Time)", lambda x: x['tottime']),
        ("CATEGORY 3: UPDATE SPAM / REDUNDANCY (Call Frequency)", lambda x: x['ncalls']),
        ("CATEGORY 4: LATENCY / PAYLOAD WEIGHT (Slowest Single Calls)", lambda x: x['per_call'])
    ]

    # 2. Build lines
    shame_lines = ["--- PERFORMANCE WALL OF SHAME (TOP OFFENDERS) ---", ""]

    for title, sort_key in categories:
        shame_lines.append(f"\n>>> {title}")
        # USE CONSTANT
        by_metric = sorted(performance_stats, key=sort_key, reverse=True)[:MAX_OFFENDERS_PER_CATEGORY]

        for i, s in enumerate(by_metric, 1):
            # Sanitize Function Name for HTML Display (remove <method ...>)
            raw_name = s['funcname']
            if raw_name.startswith("<") and raw_name.endswith(">"):
                 if "method" in raw_name and "'" in raw_name:
                     raw_name = raw_name.split("'")[1]

            safe_funcname = html.escape(raw_name)

            if "Frequency" in title:
                val_str = f"{s['ncalls']:10} calls | {s['tottime']:8.4f}s self"
            elif "Latency" in title:
                val_str = f"{s['per_call']:10.6f}s/call"
            elif "CPU" in title:
                val_str = f"{s['tottime']:10.4f}s | {s['ncalls']:8} calls"
            else: # Cumulative
                val_str = f"{s['cumtime']:10.4f}s | {s['ncalls']:8} calls"

            shame_lines.append(f" {i:2}. {val_str} | {safe_funcname}")

    # 3. Add Subsystem Breakdown
    shame_lines.append(f"\n>>> CATEGORY 5: SUBSYSTEM BREAKDOWN (Worst {MAX_SUBSYSTEM_BREAKDOWN_ITEMS} per Root Process)")
    all_roots = sorted(list(set(r for s in performance_stats for r in s['roots'])))
    for root in all_roots:
        shame_lines.append(f"  [ ROOT SUBSYSTEM: {root} ]")
        root_stats = [s for s in performance_stats if root in s['roots']]
        root_offenders = sorted(root_stats, key=lambda x: x['cumtime'], reverse=True)[:MAX_SUBSYSTEM_BREAKDOWN_ITEMS]
        for i, s in enumerate(root_offenders, 1):
            raw_name = s['funcname']
            if raw_name.startswith("<") and raw_name.endswith(">"):
                 if "method" in raw_name and "'" in raw_name:
                     raw_name = raw_name.split("'")[1]
            safe_funcname = html.escape(raw_name)
            shame_lines.append(f"    {i:2}. {s['cumtime']:8.4f}s cum | {safe_funcname}")

    # 4. Add Framework Overhead
    shame_lines.append(f"\n>>> CATEGORY 6: THE FRAMEWORK OVERHEAD (Top {MAX_SUBSYSTEM_BREAKDOWN_ITEMS} Built-in Spammers)")
    builtins = [s for s in performance_stats if s['filename'] == "~"]
    builtin_spammers = sorted(builtins, key=lambda x: x['ncalls'], reverse=True)[:MAX_SUBSYSTEM_BREAKDOWN_ITEMS]
    for i, s in enumerate(builtin_spammers, 1):
        shame_lines.append(f"    {i:2}. {s['ncalls']:10} calls | {s['tottime']:8.4f}s self | {html.escape(s['funcname'])}")

    return "\n".join(shame_lines)
