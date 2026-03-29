# oaTests/Methods/FlameGraph/flame_wall_pity.py
#
# Categorical performance report focusing on architectural empathy.
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
# Version 20260329.0040.1
#
# Description:
# The 'Wall of Pity' is a detailed forensic report designed to provide
# deep context on performance bottlenecks. Unlike the concise Wall of Shame,
# it provides descriptive narratives for each category of offender, helping
# developers understand *why* a specific architectural pattern is heavy.
#
# Architectural Role:
# - Forensic Narrator: Translates raw metrics into architectural insights.
# - Bottleneck Identifier: Groups offenders by Cumulative Time, Self-Time, 
#   and Call Frequency.

import os
import html

def generate_wall_of_pity(stats_list, ps):
    """
    Generates a highly detailed, descriptive performance report.
    Designed to provide a 'blind coder' with full context on architectural bottlenecks.
    The 'Wall of Pitty' provides deep empathy for the processor's struggles.
    """
    stats = ps.stats
    vroot = ("<virtual>", 0, "total_execution")
    
    # 1. Pre-process rich caller and subsystem attribution
    func_metadata = {}
    for func, (cc, nc, tt, ct, callers) in stats.items():
        if func == vroot: continue
        
        # Sort callers by who triggered this function the most
        sorted_callers = sorted(callers.items(), key=lambda x: x[1][1], reverse=True)
        top_callers = []
        for c_func, c_stats in sorted_callers[:3]:
            # Format caller name
            c_name = c_func[2]
            # Handle class methods or odd pstats names
            if c_name.startswith("<") and c_name.endswith(">"):
                # Clean up <method 'name' ...>
                if "method" in c_name and "'" in c_name:
                    c_name = c_name.split("'")[1]
            
            c_file = os.path.basename(c_func[0])
            if c_func[0] == "~": 
                c_label = f"built-in:{c_name}"
            else:
                c_label = f"{c_name} (in {c_file}:{c_func[1]})"
                
            # Calculate what percentage of total calls this caller is responsible for
            pct = (c_stats[1] / nc * 100) if nc > 0 else 0
            top_callers.append(f"{c_label} [{pct:.1f}%]")
        
        # Escape the full path to avoid any weird chars
        safe_path = html.escape(f"{func[0]}:{func[1]}")
        
        func_metadata[func] = {
            "caller_report": " | TRIGGERED BY: " + ", ".join(top_callers) if top_callers else " | TRIGGERED BY: <entry point>",
            "full_path": safe_path
        }

    # 2. Define Descriptive Categories
    categories = [
        {
            "id": "BLOCKING_PATHS",
            "title": "CATEGORY 1: THE BLOCKERS (Cumulative Time Bottlenecks)",
            "description": "These paths represent the heaviest execution branches. Even if the function itself is fast, its children are keeping the CPU occupied for significant durations. Fixing these usually requires architectural changes to how data flows through the system.",
            "sort_key": lambda x: x['cumtime'],
            "metric_label": "Total Time Held",
            "metric_format": lambda x: f"{x['cumtime']:.4f}s"
        },
        {
            "id": "CPU_INTENSIVE",
            "title": "CATEGORY 2: THE GRINDERS (Self-Time / Hotspots)",
            "description": "These functions are CPU 'hotspots'. The time is spent inside the function body itself, not waiting for others. This is the 'Wall of Shame' for inefficient loops, heavy regex, or unoptimized logic. Focus here for micro-optimizations.",
            "sort_key": lambda x: x['tottime'],
            "metric_label": "Internal Grind",
            "metric_format": lambda x: f"{x['tottime']:.4f}s"
        },
        {
            "id": "UPDATE_SPAM",
            "title": "CATEGORY 3: THE SPAMMERS (High Frequency / Death by 1000 Cuts)",
            "description": "Redundant logic and 'update spam'. These functions are called thousands of times. Even a 1ms execution becomes a disaster when triggered in a tight loop or every UI frame. Ask yourself: 'Do I really need to call this that often?'",
            "sort_key": lambda x: x['ncalls'],
            "metric_label": "Call Volume",
            "metric_format": lambda x: f"{x['ncalls']} calls"
        },
        {
            "id": "LATENCY_WEIGHT",
            "title": "CATEGORY 4: THE SLUGGARDS (Slowest Single Execution)",
            "description": "These functions represent latency spikes. A single call here is heavy enough to cause a visible stutter or a network timeout. This is often indicative of blocking I/O, heavy file reads, or synchronous network requests that should be async.",
            "sort_key": lambda x: x['per_call'],
            "metric_label": "Worst Latency",
            "metric_format": lambda x: f"{x['per_call']:.6f}s/call"
        }
    ]

    # 3. Build the descriptive report
    report = [
        "===================================================================================",
        "                   OPEN-AIR PERFORMANCE WALL OF PITTY (INTELLIGENCE REPORT)        ",
        "===================================================================================",
        "This report identifies the most significant architectural and logic-level offenders",
        "discovered during the profiling session. Use the details below to trace exactly",
        "who is responsible for the performance degradation.",
        ""
    ]
    
    for cat in categories:
        report.append(f"\n>>> {cat['title']}")
        report.append("-" * len(cat['title']))
        report.append(f"CONTEXT: {cat['description']}")
        report.append("")
        
        # 50 items
        by_metric = sorted(stats_list, key=cat['sort_key'], reverse=True)[:50]
        
        for i, s in enumerate(by_metric, 1):
            # Safe Fallback for Metadata
            raw_key = s.get('raw_key')
            if raw_key and raw_key in func_metadata:
                meta = func_metadata[raw_key]
            else:
                meta = {
                    "full_path": html.escape(f"{s.get('filename', 'unknown')}:{s.get('lineno', '?')}"),
                    "caller_report": " | TRIGGERED BY: (Unknown Caller Context)"
                }
            
            subsystems = f" [Subsystems: {', '.join(s['roots'])}]" if s['roots'] else ""
            
            # Sanitize Function Name for HTML Display
            raw_name = s['funcname']
            if raw_name.startswith("<") and raw_name.endswith(">"):
                 if "method" in raw_name and "'" in raw_name:
                     raw_name = raw_name.split("'")[1]
            
            safe_funcname = html.escape(raw_name)
            safe_caller_report = html.escape(meta['caller_report'])
            
            line_1 = f" {i:2}. {cat['metric_label']}: {cat['metric_format'](s)} | FUNCTION: {safe_funcname}{subsystems}"
            line_2 = f"     LOCATION: {meta['full_path']}"
            line_3 = f"     DETAIL  : {safe_caller_report}"
            
            report.append(line_1)
            report.append(line_2)
            report.append(line_3)
            report.append("")

    # --- CATEGORY 5: SUBSYSTEM BREAKDOWN ---
    report.append("\n>>> CATEGORY 5: SUBSYSTEM BREAKDOWN (Worst 20 per Root Process)")
    report.append("-" * 65)
    report.append("CONTEXT: Performance offenders grouped by their origin process or root subsystem. This identifies which 'partition' of the app is causing the most cumulative lag.")
    report.append("")

    # Extract unique roots
    all_roots = sorted(list(set(r for s in stats_list for r in s['roots'])))
    for root in all_roots:
        report.append(f"  [ ROOT SUBSYSTEM: {root} ]")
        root_stats = [s for s in stats_list if root in s['roots']]
        root_offenders = sorted(root_stats, key=lambda x: x['cumtime'], reverse=True)[:20]
        
        for i, s in enumerate(root_offenders, 1):
            raw_name = s['funcname']
            if raw_name.startswith("<") and raw_name.endswith(">"):
                 if "method" in raw_name and "'" in raw_name:
                     raw_name = raw_name.split("'")[1]
            safe_funcname = html.escape(raw_name)
            report.append(f"    {i:2}. {s['cumtime']:8.4f}s cum | {s['tottime']:8.4f}s self | {safe_funcname}")
        report.append("")

    # --- CATEGORY 6: THE FRAMEWORK OVERHEAD (Built-ins) ---
    report.append("\n>>> CATEGORY 6: THE FRAMEWORK OVERHEAD (Top 20 Built-in Spammers)")
    report.append("-" * 65)
    report.append("CONTEXT: These are internal Python built-ins or methods triggered by the app. High volume here often indicates overhead from libraries, debuggers, or inefficient use of language features (e.g., constant isinstance checks or lock contention).")
    report.append("")

    builtins = [s for s in stats_list if s['filename'] == "~"]
    builtin_spammers = sorted(builtins, key=lambda x: x['ncalls'], reverse=True)[:20]
    for i, s in enumerate(builtin_spammers, 1):
        report.append(f"    {i:2}. {s['ncalls']:10} calls | {s['tottime']:8.4f}s self | {html.escape(s['funcname'])}")

    report.append("\n===================================================================================")
    report.append("END OF PITTY REPORT - OPTIMIZE ACCORDINGLY")
    report.append("===================================================================================")

    return "\n".join(report)
