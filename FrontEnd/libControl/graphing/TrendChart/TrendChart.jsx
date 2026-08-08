/**
 * Header: TrendChart.jsx
 * Purpose: One reading, plotted against wall-clock time.
 * Description: Value-over-time strip chart for a `yak_listen` reading.
 *
 * Version: 26.08.08.1
 * Change Log:
 * - 2026-08-08: Initial version — DMM trend.
 */

// DynamicGraph plots a TRACE: an array of points the instrument hands over in
// one reply, already carrying its own x axis. A meter answers something else
// entirely — one number, now — and the x axis is the panel's own clock. Nothing
// here could draw that, so a DMM's history existed only in whoever was watching.
//
// SAMPLED ON A CADENCE, not on arrival. A reading payload is {value, unit} with
// no timestamp (contracts/src/control-value.ts calls ts metadata, and YAK does
// not stamp one yet), so two identical consecutive answers are byte-identical:
// the same 4.9997 V read twice is indistinguishable from one read once, and a
// chart drawn on payload changes would flatline through exactly the steady
// signal it is there to show. The clock is the honest x axis — this records
// what the panel knew at time t, and says so.
const TrendChart = ({ config, topic }) => {
    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const listen = config?.yak_listen_topic || topic;
    const windowSec = Number(config?.window_seconds) > 0 ? Number(config.window_seconds) : 120;
    const sampleMs = Number(config?.sample_ms) > 0 ? Number(config.sample_ms) : 1000;
    const height = Number(config?.layout?.height || config?.height || 280);
    const colors = config?.cosmetics?.colors || {};
    const line = colors.primary || '#39D353';
    const grid = colors.secondary || '#333333';
    const bg = colors.background || '#1a1a1a';

    const label = (() => {
        const l = config?.label;
        if (!l) return '';
        if (typeof l === 'string') return l;
        return l[lang] || l.En || '';
    })();

    // The unit travels with the value, so the axis is labelled by the
    // instrument rather than by the panel's assumption about it.
    const reading = React.useMemo(() => {
        const raw = listen ? messages[listen] : undefined;
        if (raw === undefined) return { value: undefined, unit: config?.units || '' };
        try {
            const p = JSON.parse(String(raw));
            if (p && typeof p === 'object' && p.value !== undefined) {
                return { value: Number(p.value), unit: p.unit || config?.units || '' };
            }
        } catch (e) { /* plain payload */ }
        return { value: Number(raw), unit: config?.units || '' };
    }, [listen ? messages[listen] : undefined, config?.units]);

    const [points, setPoints] = React.useState([]);
    const latest = React.useRef(reading);
    latest.current = reading;

    // A fresh value is drawn at once — a single ACQUIRE should not wait out the
    // cadence to appear — and the cadence then carries the line forward while
    // the value holds.
    const record = React.useCallback(() => {
        const v = latest.current.value;
        if (!Number.isFinite(v)) return;
        const now = Date.now();
        setPoints((prev) => {
            const next = prev.concat([{ t: now, v }]);
            const cutoff = now - windowSec * 1000;
            let i = 0;
            while (i < next.length && next[i].t < cutoff) i += 1;
            return i > 0 ? next.slice(i) : next;
        });
    }, [windowSec]);

    React.useEffect(() => { record(); }, [reading.value, record]);
    React.useEffect(() => {
        const id = setInterval(record, sampleMs);
        return () => clearInterval(id);
    }, [record, sampleMs]);

    // Measured rather than stretched: a viewBox scaled to the pane would squash
    // the axis text along with the plot.
    const boxRef = React.useRef(null);
    const [width, setWidth] = React.useState(600);
    React.useLayoutEffect(() => {
        const el = boxRef.current;
        if (!el || !window.ResizeObserver) return;
        const ro = new window.ResizeObserver(() => setWidth(el.clientWidth || 600));
        ro.observe(el);
        setWidth(el.clientWidth || 600);
        return () => ro.disconnect();
    }, []);

    const padL = 64, padR = 12, padT = 10, padB = 22;
    const plotW = Math.max(10, width - padL - padR);
    const plotH = Math.max(10, height - padT - padB);

    // Autoscale, with a floor on the span so a dead-steady reading draws a flat
    // line across the middle instead of a noise-amplified scribble.
    const values = points.map((p) => p.v);
    let lo = values.length ? Math.min(...values) : 0;
    let hi = values.length ? Math.max(...values) : 1;
    const span = hi - lo;
    const floor = Math.max(Math.abs(hi), Math.abs(lo)) * 0.01 || 1;
    if (span < floor) { const mid = (hi + lo) / 2; lo = mid - floor / 2; hi = mid + floor / 2; }
    else { lo -= span * 0.08; hi += span * 0.08; }

    const now = Date.now();
    const x = (t) => padL + plotW * (1 - (now - t) / (windowSec * 1000));
    const y = (v) => padT + plotH * (1 - (v - lo) / (hi - lo));

    const path = points.length
        ? points.map((p, i) => `${i ? 'L' : 'M'}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join(' ')
        : '';

    const tick = (v) => {
        const a = Math.abs(v);
        if (a !== 0 && (a < 0.001 || a >= 1e6)) return v.toExponential(2);
        return v.toFixed(a >= 100 ? 1 : a >= 1 ? 3 : 5);
    };
    const rows = [0, 0.25, 0.5, 0.75, 1].map((f) => lo + (hi - lo) * f);
    const cols = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(windowSec * (1 - f)));

    return (
        <div ref={boxRef} style={{ width: '100%', boxSizing: 'border-box' }}>
            {label && (
                <div style={{ color: '#999', fontSize: '10px', fontWeight: 'bold', padding: '1px 3px' }}>
                    {label.toUpperCase()}
                </div>
            )}
            <svg width={width} height={height} style={{ background: bg, borderRadius: '3px', display: 'block' }}>
                {rows.map((v, i) => (
                    <g key={`r${i}`}>
                        <line x1={padL} x2={padL + plotW} y1={y(v)} y2={y(v)} stroke={grid} strokeWidth="1" />
                        <text x={padL - 6} y={y(v) + 3} textAnchor="end" fill="#888" fontSize="9">{tick(v)}</text>
                    </g>
                ))}
                {cols.map((s, i) => {
                    const cx = padL + plotW * (1 - s / windowSec);
                    return (
                        <g key={`c${i}`}>
                            <line x1={cx} x2={cx} y1={padT} y2={padT + plotH} stroke={grid} strokeWidth="1" />
                            <text x={cx} y={height - 6} textAnchor="middle" fill="#888" fontSize="9">
                                {s === 0 ? 'now' : `-${s}s`}
                            </text>
                        </g>
                    );
                })}
                {path && <path d={path} fill="none" stroke={line} strokeWidth="2" />}
                {points.length > 0 && (
                    <circle cx={x(points[points.length - 1].t)} cy={y(points[points.length - 1].v)}
                            r="3" fill={line} />
                )}
                {reading.unit && (
                    <text x={padL + 4} y={padT + 11} fill="#888" fontSize="10">{reading.unit}</text>
                )}
                {!points.length && (
                    <text x={padL + plotW / 2} y={padT + plotH / 2} textAnchor="middle" fill="#666" fontSize="11">
                        waiting for a reading
                    </text>
                )}
            </svg>
        </div>
    );
};

window.TrendChart = TrendChart;
