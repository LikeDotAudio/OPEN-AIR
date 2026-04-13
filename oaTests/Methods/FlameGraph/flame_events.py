# oaTests/Methods/FlameGraph/flame_events.py
#
# Statistical processing and event enrichment for profiling data.
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
# Version 20260329.0030.1
#
# Description:
# This module provides the logic for transforming raw Python profile
# statistics into a rich, structured dataset. It performs root attribution
# (identifying which subsystem triggered a call) and applies layer tagging
# (APP, LIB, CORE) to simplify forensic analysis.
#
# Architectural Role:
# - Data Normalizer: Converts pstats into a unified dictionary-based schema.
# - Subsystem Classifier: Maps call stacks back to logical architectural roots.

import os
import html
from collections import deque, defaultdict

def process_stats_for_ui(ps):
    """
    Transforms raw pstats into a rich list of dicts with root attribution 
    and layer tagging (APP/LIB/CORE).
    """
    stats = ps.stats
    vroot = ("<virtual>", 0, "total_execution")
    
    # ⚡ VIRTUAL ROOT INJECTION (Mirroring make_graph.py logic)
    # This ensures we can trace every function back to a top-level entry point.
    roots = [f for f, data in stats.items() if not data[4]]
    for func in list(stats.keys()):
        if func == vroot: continue
        cc, nc, tt, ct, callers = stats[func]
        if not callers or func in roots:
            # Inject link to virtual root
            new_callers = dict(callers)
            new_callers[vroot] = (cc, nc, tt, ct)
            stats[func] = (cc, nc, tt, ct, new_callers)

    # 1. Map hierarchy for root attribution
    roots_to_analyze = [f for f, data in stats.items() if vroot in data[4]]
    
    callees = defaultdict(list)
    for func, data in stats.items():
        for caller in data[4]:
            callees[caller].append(func)
            
    func_to_roots = defaultdict(set)
    root_naming_map = {
        'openair.py': 'MAIN', 'mqtt': 'MQTT', 'watchdog': 'WATCHDOG', 
        'gui': 'UI', 'worker': 'WORKER', 'visa': 'VISA', 
        'yak': 'YAK', 'manager': 'MANAGER', 'ptp': 'PTP'
    }

    MAX_LABEL_LENGTH = 10

    def _format_root_label(file_path):
        """Cleans and formats a file path into a standardized root label."""
        base = os.path.basename(file_path)
        clean = base.replace('.py', '').replace('gui_', '').replace('manager_', '')
        return clean.upper()[:MAX_LABEL_LENGTH]

    def get_root_label(f):
        desc = f"{f[0]} {f[2]}".lower()
        for pattern, label in root_naming_map.items():
            if pattern in desc: return label
        return _format_root_label(f[0])

    for root_func in roots_to_analyze:
        label = get_root_label(root_func)
        queue = deque([root_func])
        visited = {root_func}
        while queue:
            curr = queue.popleft()
            func_to_roots[curr].add(label)
            for child in callees[curr]:
                if child not in visited:
                    visited.add(child)
                    queue.append(child)

    # 2. Build final flattened performance stats
    performance_stats = []
    for func, (cc, nc, tt, ct, callers) in stats.items():
        if func == vroot: continue
        fname = func[2]
        
        if func[0] == "~":
            caller_names = [c[2] for c in callers if c[2] and c[2] != vroot[2]]
            if caller_names:
                fname = f"built-in: {fname} (via {', '.join(list(set(caller_names))[:2])})"
            else:
                fname = f"built-in: {fname}"
                
        performance_stats.append({
            'filename': func[0], 'lineno': func[1], 'funcname': fname or "<unknown>", 
            'ncalls': nc, 'tottime': tt, 'cumtime': ct, 
            'per_call': tt/nc if nc > 0 else 0,
            'roots': sorted(list(func_to_roots[func])),
            'raw_key': func
        })
        
    return performance_stats

def generate_table_rows(performance_stats):
    """Generates HTML table rows with data attributes for filtering/sorting."""
    rows = []
    performance_stats.sort(key=lambda x: x['cumtime'], reverse=True)
    max_cumtime = max(s['cumtime'] for s in performance_stats) if performance_stats else 1
    
    # ⚡ NO LIMIT: All events displayed
    for stat in performance_stats:
        contrib = (stat['cumtime'] / max_cumtime) * 100
        filename = stat['filename']
        layer = "LIB" if any(p in filename for p in ["site-packages", "lib/python"]) else "CORE" if (filename == "~" or "/usr/lib" in filename) else "APP"
        
        tags_html = "".join([f'<span class="tag">{r}</span>' for r in stat["roots"]])
        
        # Escape function name for HTML display
        safe_funcname = html.escape(stat["funcname"])
        
        row = f'<tr data-layer="{layer}" data-roots="{" ".join(stat["roots"])}">'
        row += f'<td><div style="margin-bottom:4px"><span class="tag tag-layer-{layer}">{layer}</span>{tags_html}</div>'
        row += f'<span style="color:#fff">{safe_funcname}</span><br><span style="color:#666;font-size:11px">{os.path.basename(filename)}:{stat["lineno"]}</span></td>'
        row += f'<td class="stat-value">{stat["ncalls"]}</td><td class="stat-value">{stat["tottime"]:.6f}s</td><td class="stat-value">{stat["cumtime"]:.6f}s</td><td class="stat-value">{stat["per_call"]:.6f}s</td>'
        row += f'<td><div style="width:{min(100, contrib):.1f}%;height:4px;background:#3498db;border-radius:2px"></div><span style="font-size:10px;color:#666">{contrib:.1f}%</span></td></tr>'
        rows.append(row)
        
    return "\n".join(rows)
