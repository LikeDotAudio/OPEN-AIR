/**
 * Header: TrendChart.jsx
 * Purpose: One reading, plotted against wall-clock time.
 * Description: Value-over-time strip chart for a `yak_listen` reading.
 *
 * Version: 26.08.08.2
 * Change Log:
 * - 2026-08-08: Fill the window when popped out (OaPopout), and measure off the
 *   window event as well as the box — the observer is deaf across documents.
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

    // EIGHT SUPPLIES ARE ONE QUESTION, NOT EIGHT.
    //
    // A trend per module is eight charts with eight y-axes, and comparing them
    // means comparing pictures. Overlaid on one axis the comparison is the
    // reading: which rail sagged, which tracked, which never came up. `match`
    // is a topic pattern — the same wildcard discovery BankBars uses — so the
    // series are whatever the bench has, not a list kept in step by hand.
    const matchPattern = config?.match || '';
    const names = config?.names || {};
    const seriesTopics = React.useMemo(() => {
        if (!matchPattern) return listen ? [listen] : [];
        const p = matchPattern.split('/');
        const hit = [];
        for (const t of Object.keys(messages)) {
            const parts = t.split('/');
            let ok = p.length === parts.length;
            for (let i = 0; ok && i < p.length; i += 1) {
                if (p[i] === '#') { ok = true; break; }
                if (p[i] !== '+' && p[i] !== parts[i]) ok = false;
            }
            if (ok) hit.push(t);
        }
        hit.sort();
        return hit;
    }, [matchPattern, listen, Object.keys(messages).join('|')]);

    const nameOf = (t) => {
        const seg = t.split('/');
        const at = seg.indexOf('Device');
        const key = at >= 0 ? `${seg[at + 2]}/${seg[at + 3]}` : t;
        return names[key] || names[t] || key;
    };

    // The unit travels with the value, so the axis is labelled by the
    // instrument rather than by the panel's assumption about it.
    const readingAt = (t) => {
        const raw = t ? messages[t] : undefined;
        if (raw === undefined) return { value: undefined, unit: config?.units || '' };
        try {
            const p = JSON.parse(String(raw));
            if (p && typeof p === 'object' && p.value !== undefined) {
                return { value: Number(p.value), unit: p.unit || config?.units || '' };
            }
        } catch (e) { /* plain payload */ }
        return { value: Number(raw), unit: config?.units || '' };
    };
    const reading = readingAt(seriesTopics[0]);

    // points: { topic -> [{t, v}] }
    const [points, setPoints] = React.useState({});
    const latest = React.useRef({});
    latest.current = {};
    seriesTopics.forEach((t) => { latest.current[t] = readingAt(t); });

    // A fresh value is drawn at once — a single ACQUIRE should not wait out the
    // cadence to appear — and the cadence then carries the line forward while
    // the value holds.
    const record = React.useCallback(() => {
        const now = Date.now();
        const cutoff = now - windowSec * 1000;
        setPoints((prev) => {
            const next = {};
            let touched = false;
            for (const t of Object.keys(latest.current)) {
                const v = latest.current[t].value;
                const had = prev[t] || [];
                if (!Number.isFinite(v)) { next[t] = had; continue; }
                touched = true;
                const grown = had.concat([{ t: now, v }]);
                let i = 0;
                while (i < grown.length && grown[i].t < cutoff) i += 1;
                next[t] = i > 0 ? grown.slice(i) : grown;
            }
            return touched ? next : prev;
        });
    }, [windowSec]);

    React.useEffect(() => { record(); },
        [seriesTopics.map((t) => String(messages[t] || '')).join('|'), record]);
    React.useEffect(() => {
        const id = setInterval(record, sampleMs);
        return () => clearInterval(id);
    }, [record, sampleMs]);

    // Measured rather than stretched: a viewBox scaled to the pane would squash
    // the axis text along with the plot.
    //
    // Two measurements, because there are two ways this chart can be sized. In a
    // panel it is `height` tall — the author's number — and only the width is
    // discovered. Popped out (OaPopout marks the holder), the window IS the size:
    // a 280px strip floating in a 800px window is not what was asked for. The
    // window event carries the second case: a ResizeObserver made in THIS
    // document does not fire for an element that now lives in another one.
    const boxRef = React.useRef(null);
    const [box, setBox] = React.useState({ w: 600, h: 0 });
    React.useLayoutEffect(() => {
        const el = boxRef.current;
        if (!el) return;
        const measure = () => {
            const host = el.parentElement;
            const detached = !!(host && host.getAttribute && host.getAttribute('data-oa-detached') === '1');
            setBox({
                w: el.clientWidth || 600,
                h: detached ? Math.max(0, (host.clientHeight || 0) - (label ? 16 : 0)) : 0,
            });
        };
        const ro = window.ResizeObserver ? new window.ResizeObserver(measure) : null;
        if (ro) ro.observe(el);
        window.addEventListener('resize', measure);
        measure();
        return () => { if (ro) ro.disconnect(); window.removeEventListener('resize', measure); };
    }, [label]);
    const width = box.w;
    const drawH = box.h > 120 ? box.h : height;

    const padL = 64, padR = 12, padT = 10, padB = 22;
    const plotW = Math.max(10, width - padL - padR);
    const plotH = Math.max(10, drawH - padT - padB);

    // Autoscale across EVERY series, so overlaid rails share one axis — the
    // whole reason to overlay them is that the comparison is the reading.
    const values = seriesTopics.flatMap((t) => (points[t] || []).map((p) => p.v));
    let lo = values.length ? Math.min(...values) : 0;
    let hi = values.length ? Math.max(...values) : 1;
    const span = hi - lo;
    const floor = Math.max(Math.abs(hi), Math.abs(lo)) * 0.01 || 1;
    if (span < floor) { const mid = (hi + lo) / 2; lo = mid - floor / 2; hi = mid + floor / 2; }
    else { lo -= span * 0.08; hi += span * 0.08; }

    const now = Date.now();
    const x = (t) => padL + plotW * (1 - (now - t) / (windowSec * 1000));
    const y = (v) => padT + plotH * (1 - (v - lo) / (hi - lo));

    // A palette rather than one colour: eight rails on one axis are only
    // readable if each line keeps its identity, and the legend names them.
    const PALETTE = config?.palette || ['#33A1FD', '#39D353', '#FF902C', '#FF6B6B',
                                        '#B06CFF', '#00D4C8', '#FFD400', '#FF61C7'];
    const series = seriesTopics.map((t, i) => {
        const pts = points[t] || [];
        return {
            topic: t,
            name: matchPattern ? nameOf(t) : label,
            colour: matchPattern ? PALETTE[i % PALETTE.length] : line,
            pts,
            path: pts.length
                ? pts.map((p, j) => `${j ? 'L' : 'M'}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join(' ')
                : '',
        };
    });
    const anyPoints = series.some((s) => s.pts.length > 0);

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
            <svg width={width} height={drawH} style={{ background: bg, borderRadius: '3px', display: 'block' }}>
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
                            <text x={cx} y={drawH - 6} textAnchor="middle" fill="#888" fontSize="9">
                                {s === 0 ? 'now' : `-${s}s`}
                            </text>
                        </g>
                    );
                })}
                {series.map((s, i) => (s.path
                    ? <path key={`p${i}`} d={s.path} fill="none" stroke={s.colour} strokeWidth="2" />
                    : null))}
                {series.map((s, i) => (s.pts.length
                    ? <circle key={`d${i}`} cx={x(s.pts[s.pts.length - 1].t)}
                              cy={y(s.pts[s.pts.length - 1].v)} r="3" fill={s.colour} />
                    : null))}
                {reading.unit && (
                    <text x={padL + 4} y={padT + 11} fill="#888" fontSize="10">{reading.unit}</text>
                )}
                {matchPattern && series.map((s, i) => (
                    <g key={`l${i}`} transform={`translate(${padL + 40 + (i % 4) * 150}, ${padT + 10 + Math.floor(i / 4) * 13})`}>
                        <rect width="10" height="3" y="-3" fill={s.colour} />
                        <text x="14" y="0" fill="#aaa" fontSize="9">{s.name}</text>
                    </g>
                ))}
                {!anyPoints && (
                    <text x={padL + plotW / 2} y={padT + plotH / 2} textAnchor="middle" fill="#666" fontSize="11">
                        waiting for a reading
                    </text>
                )}
            </svg>
        </div>
    );
};

window.TrendChart = TrendChart;
