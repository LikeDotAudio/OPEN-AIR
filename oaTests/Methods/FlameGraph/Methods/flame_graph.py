# oaTests/Methods/FlameGraph/flame_graph.py
#
# Performance visualization engine for SVG Flame Graph generation.
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
# Version 20260329.0025.1
#
# Description:
# This module transforms raw Python profile statistics (pstats) into an
# interactive, high-resolution SVG flame graph. It leverages the 'flameprof'
# library and applies custom post-processing to optimize the output for the
# OpenAir forensics dashboard.
#
# Architectural Role:
# - Visualization Engine: Renders complex call-stack data into visual assets.
# - Statistics Normalizer: Corrects common profiling artifacts (virtual roots).

import importlib.util
import io
import re
import sys

# --- Constants for Magic Numbers ---
DEFAULT_RECURSION_LIMIT = 50000
MIN_EXECUTION_TIME = 0.000001
DEFAULT_THRESHOLD = 0.001
FLAMEGRAPH_STANDARD_WIDTH = 1200 # Standard width for flame graphs
FLAMEGRAPH_WIDTH_MULTIPLIER = 5  # Multiplier for high-resolution graphs
# --- End Constants ---

# Check if flameprof is available without exceptions
_flameprof_spec = importlib.util.find_spec("flameprof")
if _flameprof_spec:
    import flameprof
else:
    flameprof = None

def generate_flamegraph_with_flameprof(ps, output_svg):
    """Renders the pstats data into an interactive SVG flame graph."""
    if not flameprof:
        print("? 'flameprof' library not found. Install it with: pip install flameprof")
        return False

    # ? PRECONDITION VALIDATION
    if not ps or not hasattr(ps, 'stats') or not ps.stats:
        print("?? No profile data collected.")
        return False

    ps.strip_dirs()
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(DEFAULT_RECURSION_LIMIT)

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
            new_callers[c_func] = (c_cc, c_nc, c_tt, max(c_ct, MIN_EXECUTION_TIME))

        if not new_callers or func in roots:
            new_callers[vroot] = (cc, nc, tt, max(ct, MIN_EXECUTION_TIME))
        stats[func] = (cc, nc, tt, ct, new_callers)

    stats[vroot] = (1, 1, 0, max(total_tottime, MIN_EXECUTION_TIME), {})

    out = io.StringIO()
    # Increased width to 6000 (5x standard) for better resolution
    flameprof.render(ps.stats, out, width=FLAMEGRAPH_STANDARD_WIDTH * FLAMEGRAPH_WIDTH_MULTIPLIER, threshold=DEFAULT_THRESHOLD)
    svg_content = out.getvalue()

    if not svg_content.strip():
        sys.setrecursionlimit(old_limit)
        return False

    # ? POST-PROCESS SVG: Inject ID and standard height, but KEEP WIDTH for resolution
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
