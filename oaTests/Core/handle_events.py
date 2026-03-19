# oaTests/Core/handle_events.py
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
        'OpenAir.py': 'MAIN', 'mqtt': 'MQTT', 'watchdog': 'WATCHDOG', 
        'gui': 'UI', 'worker': 'WORKER', 'visa': 'VISA', 
        'yak': 'YAK', 'manager': 'MANAGER', 'ptp': 'PTP'
    }

    def get_root_label(f):
        desc = f"{f[0]} {f[2]}".lower()
        for pattern, label in root_naming_map.items():
            if pattern in desc: return label
        return os.path.basename(f[0]).replace('.py', '').replace('gui_', '').replace('manager_', '').upper()[:10]

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

    # 2. Build final flattened stats list
    stats_list = []
    for func, (cc, nc, tt, ct, callers) in stats.items():
        if func == vroot: continue
        fname = func[2]
        
        if func[0] == "~":
            caller_names = [c[2] for c in callers if c[2] and c[2] != vroot[2]]
            if caller_names:
                fname = f"built-in: {fname} (via {', '.join(list(set(caller_names))[:2])})"
            else:
                fname = f"built-in: {fname}"
                
        stats_list.append({
            'filename': func[0], 'lineno': func[1], 'funcname': fname or "<unknown>", 
            'ncalls': nc, 'tottime': tt, 'cumtime': ct, 
            'per_call': tt/nc if nc > 0 else 0,
            'roots': sorted(list(func_to_roots[func])),
            'raw_key': func
        })
        
    return stats_list

def generate_table_rows(stats_list):
    """Generates HTML table rows with data attributes for filtering/sorting."""
    rows = []
    stats_list.sort(key=lambda x: x['cumtime'], reverse=True)
    max_cumtime = max(s['cumtime'] for s in stats_list) if stats_list else 1
    
    # ⚡ NO LIMIT: All events displayed
    for stat in stats_list:
        contrib = (stat['cumtime'] / max_cumtime) * 100
        filename = stat['filename']
        layer = "LIB" if any(p in filename for p in ["site-packages", "lib/python"]) else "CORE" if (filename == "~" or "/usr/lib" in filename) else "APP"
        
        tags_html = "".join([f'<span class="tag">{r}</span>' for r in stat["roots"]])
        
        # Escape function name for HTML display
        safe_funcname = html.escape(stat["funcname"])
        
        row = f'<tr data-layer="{layer}" data-roots="{" ".join(stat["roots"])}">'
        row += f'<td><div style="margin-bottom:4px"><span class="tag tag-layer-{layer}">{layer}</span>{tags_html}</div>'
        row += f'<span style="color:#fff">{safe_funcname}</span><br><span style="color:#666;font-size:11px">{os.path.basename(filename)}:{stat["lineno"]}</span></td>'
        row += f'<td class="stat-val">{stat["ncalls"]}</td><td class="stat-val">{stat["tottime"]:.6f}s</td><td class="stat-val">{stat["cumtime"]:.6f}s</td><td class="stat-val">{stat["per_call"]:.6f}s</td>'
        row += f'<td><div style="width:{min(100, contrib):.1f}%;height:4px;background:#3498db;border-radius:2px"></div><span style="font-size:10px;color:#666">{contrib:.1f}%</span></td></tr>'
        rows.append(row)
        
    return "\n".join(rows)
