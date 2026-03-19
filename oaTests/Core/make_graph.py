# oaTests/Core/make_graph.py
import io
import sys
import re
import importlib.util

# Check if flameprof is available without exceptions
_flameprof_spec = importlib.util.find_spec("flameprof")
if _flameprof_spec:
    import flameprof
else:
    flameprof = None

def generate_flamegraph_with_flameprof(ps, output_svg):
    """Renders the pstats data into an interactive SVG flame graph."""
    if not flameprof:
        print("❌ 'flameprof' library not found. Install it with: pip install flameprof")
        return False
    
    # ⚡ PRECONDITION VALIDATION
    if not ps or not hasattr(ps, 'stats') or not ps.stats:
        print("⚠️ No profile data collected.")
        return False

    ps.strip_dirs()
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(50000)

    stats = ps.stats
    total_tottime = 0
    for func, data in stats.items():
        cc, nc, tt, ct, callers = data
        tt = max(0, tt) if tt == tt else 0
        ct = max(tt, ct) if ct == ct else tt
        stats[func] = (cc, nc, tt, ct, callers)
        total_tottime += tt

    roots = [f for f, data in stats.items() if not data[4]]
    vroot = ("<virtual>", 0, "total_execution")
    
    for func in list(stats.keys()):
        if func == vroot: continue
        cc, nc, tt, ct, callers = stats[func]
        
        new_callers = {}
        for c_func, c_data in callers.items():
            c_cc, c_nc, c_tt, c_ct = c_data
            new_callers[c_func] = (c_cc, c_nc, c_tt, max(c_ct, 0.000001))
        
        if not new_callers or func in roots:
            new_callers[vroot] = (cc, nc, tt, max(ct, 0.000001))
        stats[func] = (cc, nc, tt, ct, new_callers)
    
    stats[vroot] = (1, 1, 0, max(total_tottime, 0.000001), {})

    out = io.StringIO()
    # Increased width to 6000 (5x standard) for better resolution
    flameprof.render(ps.stats, out, width=6000, threshold=0.001)
    svg_content = out.getvalue()
    
    if not svg_content.strip(): 
        sys.setrecursionlimit(old_limit)
        return False
    
    # ⚡ POST-PROCESS SVG: Inject ID and standard height, but KEEP WIDTH for resolution
    if '<svg' in svg_content:
        # Force fixed height for consistent UI, but allow width to stay at 6000px
        svg_content = re.sub(r'height="[^"]+"', 'height="600"', svg_content, count=1)
        # Inject ID and Preserve Aspect Ratio
        svg_content = svg_content.replace('<svg', '<svg id="flamegraph-svg" preserveAspectRatio="none"', 1)
    
    if '<?xml' in svg_content:
        svg_content = svg_content[svg_content.find('<svg'):]

    with open(output_svg, 'w') as f:
        f.write(svg_content)
    
    sys.setrecursionlimit(old_limit)
    return svg_content
