/**
 * Header: ScanActivity.jsx
 * Purpose: Live discovery-activity feed for the Discovered tab.
 * Description: Renders the narration every discovery agent publishes to the bus
 *              (VISA scan log + the discovered-GUI watcher's device diffs) so a
 *              running scan is visible ON THE PAGE, not only in the container's
 *              stdout and the browser console.
 *
 * Version: 26.07.26.1
 * Change Log:
 * - 2026-07-26: Initial component.
 */

// Feed data comes from window.useDiscoveryActivity() (comMQTT/MqttProvider.jsx),
// which keeps the lines in a plain store OUTSIDE React context — a scan emits
// bursts of lines, and routing them through context would re-render every widget
// on the page for each one.
const OA_ACTIVITY_LEVELS = {
    ok:    { color: '#2ea043', icon: '✅' },
    warn:  { color: '#d29922', icon: '⚠️' },
    error: { color: '#f85149', icon: '❌' },
    info:  { color: '#58a6ff', icon: '🔎' },
};

window.ScanActivity = ({ config, node }) => {
    config = config || node || {};
    const activityHook = window.useDiscoveryActivity;
    // Standalone/editor preview (no MqttProvider): render the empty shell rather
    // than crashing the panel.
    const { lines, scanning, clear } = activityHook
        ? activityHook()
        : { lines: [], scanning: false, clear: () => {} };

    const title = config?.description?.En || config?.title || 'Discovery Activity';
    const scrollRef = React.useRef(null);
    const stickRef = React.useRef(true);   // follow the tail unless scrolled up

    // "Nothing has happened for a while" is itself information — an idle bench
    // looks identical to a broken feed without it. Ticks once a second so the
    // age readout moves even when no lines arrive.
    const [, tick] = React.useReducer(x => x + 1, 0);
    React.useEffect(() => {
        const t = setInterval(tick, 1000);
        return () => clearInterval(t);
    }, []);

    // Depends on the array IDENTITY, not its length: the store caps the buffer,
    // so once it is full the length stops changing while lines keep arriving.
    React.useEffect(() => {
        const el = scrollRef.current;
        if (el && stickRef.current) el.scrollTop = el.scrollHeight;
    }, [lines, scanning]);

    const onScroll = () => {
        const el = scrollRef.current;
        if (!el) return;
        // 24px slack: "close enough to the bottom" still counts as following.
        stickRef.current = (el.scrollHeight - el.scrollTop - el.clientHeight) < 24;
    };

    const last = lines.length ? lines[lines.length - 1] : null;
    const ageSec = last ? Math.max(0, Math.round(Date.now() / 1000 - last.ts)) : null;
    const ageText = ageSec === null ? '—'
        : ageSec < 2 ? 'just now'
        : ageSec < 90 ? `${ageSec}s ago`
        : `${Math.round(ageSec / 60)}m ago`;

    const fmtTime = (ts) => {
        try { return new Date(ts * 1000).toLocaleTimeString(); }
        catch (e) { return ''; }
    };

    return (
        <div style={{
            display: 'flex', flexDirection: 'column', width: '100%',
            height: '100%', minHeight: '160px',
            backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#1e1e1e') : '#1e1e1e'),
            border: '1px solid #333', borderRadius: '4px', overflow: 'hidden',
        }}>
            {/* Header — the liveness indicator. A pulsing dot while a VISA scan
                is in flight; steady grey when the agents are just watching. */}
            <div style={{
                backgroundColor: '#2b2b2b', padding: '8px 14px', borderBottom: '1px solid #111',
                color: '#fff', fontSize: '12px', fontWeight: 'bold',
                display: 'flex', alignItems: 'center', gap: '10px',
            }}>
                <span style={{
                    width: '10px', height: '10px', borderRadius: '50%', flexShrink: 0,
                    backgroundColor: scanning ? '#d29922' : '#2ea043',
                    boxShadow: scanning ? '0 0 8px #d29922' : '0 0 6px rgba(46,160,67,0.6)',
                    animation: scanning ? 'oa-scan-pulse 1s ease-in-out infinite' : 'none',
                }} />
                <span>{title.toUpperCase()}</span>
                <span style={{ color: scanning ? '#d29922' : '#7a7a7a', fontWeight: 'normal' }}>
                    {scanning ? 'SCANNING…' : 'watching'}
                </span>
                <div style={{ flexGrow: 1 }} />
                <span style={{ fontSize: '10px', color: '#888', fontWeight: 'normal' }}>
                    last: {ageText}
                </span>
                <button onClick={clear} style={{
                    backgroundColor: '#333', color: '#bbb', border: '1px solid #444',
                    padding: '2px 8px', fontSize: '10px', borderRadius: '2px', cursor: 'pointer',
                }}>CLEAR</button>
            </div>

            <style>{`@keyframes oa-scan-pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.25 } }`}</style>

            <div ref={scrollRef} onScroll={onScroll} style={{
                flexGrow: 1, overflow: 'auto', padding: '6px 0',
                fontFamily: 'monospace', fontSize: '11px',
            }}>
                {lines.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: '#555' }}>
                        No activity yet — press RESCAN DEVICES, or wait for the
                        network agents to report a change.
                    </div>
                ) : lines.map((line, i) => {
                    const meta = OA_ACTIVITY_LEVELS[line.level] || OA_ACTIVITY_LEVELS.info;
                    return (
                        <div key={`${line.ts}-${i}`} style={{
                            display: 'flex', gap: '8px', padding: '2px 14px',
                            backgroundColor: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                        }}>
                            <span style={{ color: '#555', flexShrink: 0 }}>{fmtTime(line.ts)}</span>
                            <span style={{ flexShrink: 0 }}>{meta.icon}</span>
                            {line.source && (
                                <span style={{ color: '#666', flexShrink: 0 }}>[{line.source}]</span>
                            )}
                            <span style={{ color: meta.color, wordBreak: 'break-word' }}>{line.message}</span>
                        </div>
                    );
                })}
            </div>

            <div style={{
                backgroundColor: '#111', padding: '5px 14px', borderTop: '1px solid #333',
                display: 'flex', gap: '10px', alignItems: 'center',
            }}>
                <span style={{ fontSize: '9px', color: '#444' }}>{lines.length} LINE(S)</span>
                <div style={{ flexGrow: 1 }} />
                <span style={{ fontSize: '9px', color: '#444' }}>
                    OpenAir/System/Discovery/Activity + visa/Scan/Log
                </span>
            </div>
        </div>
    );
};

// Register with WYSIWYG Editor
if (!window.OA_COMPONENTS) window.OA_COMPONENTS = {};
window.OA_COMPONENTS['_GuiScanActivity'] = window.ScanActivity;
