# oaTests/Core/wall_of_shame.py
import html

def generate_wall_of_shame(stats_list, ps):
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
        shame_lines.append(f"\n{title}")
        # INCREASED TO 50 ITEMS PER CATEGORY
        by_metric = sorted(stats_list, key=sort_key, reverse=True)[:50]
        
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
    shame_lines.append("\nCATEGORY 5: SUBSYSTEM BREAKDOWN (Worst 20 per Root Process)")
    all_roots = sorted(list(set(r for s in stats_list for r in s['roots'])))
    for root in all_roots:
        shame_lines.append(f"  [ ROOT SUBSYSTEM: {root} ]")
        root_stats = [s for s in stats_list if root in s['roots']]
        root_offenders = sorted(root_stats, key=lambda x: x['cumtime'], reverse=True)[:20]
        for i, s in enumerate(root_offenders, 1):
            raw_name = s['funcname']
            if raw_name.startswith("<") and raw_name.endswith(">"):
                 if "method" in raw_name and "'" in raw_name:
                     raw_name = raw_name.split("'")[1]
            safe_funcname = html.escape(raw_name)
            shame_lines.append(f"    {i:2}. {s['cumtime']:8.4f}s cum | {safe_funcname}")

    # 4. Add Framework Overhead
    shame_lines.append("\nCATEGORY 6: THE FRAMEWORK OVERHEAD (Top 20 Built-in Spammers)")
    builtins = [s for s in stats_list if s['filename'] == "~"]
    builtin_spammers = sorted(builtins, key=lambda x: x['ncalls'], reverse=True)[:20]
    for i, s in enumerate(builtin_spammers, 1):
        shame_lines.append(f"    {i:2}. {s['ncalls']:10} calls | {s['tottime']:8.4f}s self | {html.escape(s['funcname'])}")

    return "\n".join(shame_lines)
