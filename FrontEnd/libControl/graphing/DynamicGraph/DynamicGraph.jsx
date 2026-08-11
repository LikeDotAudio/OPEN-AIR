/**
 * Header: DynamicGraph.jsx
 * Purpose: DynamicGraph component or utility.
 * Description: Handles logic and rendering for DynamicGraph component or utility.
 *
 * Version: 26.08.08.2
 * Change Log:
 * - 2026-08-08: Pop-out handed to OaPopout.Host — the graph is MOVED into the
 *   overlay/window, so it keeps updating and the tab stops drawing a second copy.
 * - 2026-08-08: Resize on the ELEMENT, not just the window, now that a graph can
 *   be sized by a percentage height.
 * - 2026-07-05: Initial annotation and documentation added.
 * - 2026-08-08: Plot YAK trace readings (`traces` + `x_axis`), not just authored
 *               `datasets`. An instrument sends amplitudes ALONE — the frequency
 *               axis arrives as the start/stop of the same reply — so the widget
 *               builds X from the span rather than expecting [x,y] pairs.
 * - 2026-08-08: Time-domain axis. A scope reports the first sample's time and the
 *               interval between samples, never a stop, so `x_axis.increment` is
 *               an alternative to `x_axis.stop`; and its samples arrive inside an
 *               IEEE-488.2 block header, which is stripped before parsing.
 */

// A blanked trace still answers :TRACe<n>:DATA?, with the instrument's
// "no data" sentinel in every bin (-547.6 dBm on the N9340B). Plotting it is
// worse than useless: one flat line 480 dB below the signal collapses the Y
// axis and every real trace becomes a straight line at the top of the chart.
// Anything below this floor is not a measurement — no spectrum analyser has
// 300 dB of range — so a trace made entirely of them is dropped, not drawn.
const BLANK_FLOOR_DBM = -300;

// A scope answers :WAVeform:DATA? with an IEEE-488.2 definite-length block:
// `#8000012001-0.04,-0.04,…` — a hash, one digit giving the width of the length
// field, then that many digits of length, then the data. Left in place it does
// not merely add a stray character: it FUSES with the first sample, so
// parseFloat returns NaN and point zero of every captured trace goes missing.
const stripBlockHeader = (text) => {
    const s = String(text).trim();
    const m = /^#(\d)/.exec(s);
    return m ? s.slice(2 + Number(m[1])) : s;
};

// Inline comment: Logic for DynamicGraph
const DynamicGraph = ({ value: mqttData, config }) => {
    const chartRef = React.useRef(null);
    const chartInstance = React.useRef(null);
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();
    // Read the bus directly. A trace needs SIX topics at once (four sets of
    // samples plus the span's start and stop), and `useMqttState` hands a widget
    // exactly one — and only after coercing it with Number(), which discards a
    // 461-value CSV outright. Display-only, so nothing is published from here.
    const messages = (window.useMqttMessages ? window.useMqttMessages() : {}) || {};

    const title = config?.label?.[lang] || config?.label?.En || config?.title || "Dynamic Graph";
    
    // Geometry
    const heightVal = config?.geometry?.height || config?.layout?.height || 400;
    const height = typeof heightVal === 'number' ? `${heightVal}px` : heightVal;
    
    const widthVal = config?.geometry?.width || config?.layout?.width || '100%';
    const width = typeof widthVal === 'number' ? `${widthVal}px` : widthVal;

    // Axes
    const xAxisCfg = config?.axis?.x || {};
    const yAxisCfg = config?.axis?.y || {};
    const showGrid = config?.axis?.show_grid !== false;

    // Data Processing
    const parseCsv = (csvString) => {
        if (!csvString) return [];
        const lines = csvString.split('\n');
        const data = [];
        for (let i = 1; i < lines.length; i++) { 
            const trimmedLine = lines[i].trim();
            if (!trimmedLine) continue; 
            const values = trimmedLine.split(',');
            if (values.length >= 2) {
                const x = parseFloat(values[0]);
                const y = parseFloat(values[1]);
                if (!isNaN(x) && !isNaN(y)) data.push([x, y]);
            }
        }
        return data;
    };

    // ── YAK trace mode ──────────────────────────────────────────────────────
    //
    // `config.traces` is a list of series, each naming the reading it takes its
    // samples from; `config.x_axis` names the two readings carrying the span.
    // The orchestrator stamps a `yak_listen_topic` beside every `yak_listen` it
    // finds at ANY depth (instruments.rs, bind_readout), so these nested specs
    // arrive already bound to this device.
    //
    // A spec may list several sources: the same physical trace is published
    // under a different reading name depending on which capture fetched it
    // (trace_data_all/samples_2 vs trace_data_234/samples_2), and the graph must
    // draw whichever ran last rather than only ever the one it was authored on.
    const traceSpecs = React.useMemo(() => {
        const raw = Array.isArray(config?.traces) ? config.traces : [];
        if (raw.length) return raw;
        // A single top-level `yak_listen` is the one-trace shorthand.
        if (config?.yak_listen_topic) {
            return [{ id: 'trace', label: config.label, yak_listen_topic: config.yak_listen_topic }];
        }
        return [];
    }, [JSON.stringify(config?.traces), config?.yak_listen_topic]);

    const sourceTopicsOf = (spec) => {
        const out = [];
        if (spec.yak_listen_topic) out.push(spec.yak_listen_topic);
        (Array.isArray(spec.sources) ? spec.sources : []).forEach(s => {
            if (s && s.yak_listen_topic) out.push(s.yak_listen_topic);
        });
        return out;
    };

    // Read a ControlValue off the bus: {"value": "...", "unit": "Hz"}.
    const readingOf = (topic) => {
        const raw = topic ? messages[topic] : undefined;
        if (raw === undefined) return undefined;
        try {
            const p = JSON.parse(String(raw));
            if (p && typeof p === 'object' && p.value !== undefined) return p;
        } catch (e) { /* not JSON — fall through to the bare payload */ }
        return { value: String(raw) };
    };

    const xUnits = config?.x_axis?.units || config?.axis?.x?.units || 'Hz';

    // Which capture answered LAST wins.
    //
    // Retained readings carry no timestamp, so freshness cannot be read off the
    // payload — it has to be observed. Every render notes the payload behind each
    // source topic; the one that CHANGED since the previous render is what the
    // instrument just answered, and it becomes that slot's source until another
    // does. Without this, GET TRACES 2,3,4 would leave the chart showing whatever
    // GET ALL TRACES had last left on the other topic — including its span, which
    // is the more dangerous half: a trace drawn against a span it was not
    // measured on is wrong everywhere, not merely stale.
    const activeSource = React.useRef({});   // slot id -> topic
    const lastSeen = React.useRef({});       // topic -> payload

    // A WIDGET INSTANCE IS REUSED WHEN THE PANEL SWITCHES DEVICE.
    //
    // Same component, same position in the tree, different topics — the hazard
    // useMqttState already guards with `previousTopic`. Here the memory being
    // carried across was `activeSource`, and the staleness rule below only
    // re-picks when the remembered topic has NO payload. A topic belonging to
    // another oscilloscope has one, so the remembered source survived the
    // switch: three scopes, two of them never asked for a trace in this
    // session, all drawing the first one's waveform with nothing on screen
    // saying whose it was.
    //
    // Fingerprinting the SOURCES rather than the values: which topics this
    // graph is pointed at changes only when the panel is rebound to another
    // instrument, which is exactly when the memory of the last one is worthless.
    const sourceFingerprint = JSON.stringify([
        traceSpecs.map(sourceTopicsOf),
        sourceTopicsOf(config?.x_axis?.start || {}),
        sourceTopicsOf(config?.x_axis?.stop || {}),
        sourceTopicsOf(config?.x_axis?.increment || {}),
    ]);
    const prevFingerprint = React.useRef(sourceFingerprint);
    const rebound = React.useRef(false);
    if (prevFingerprint.current !== sourceFingerprint) {
        prevFingerprint.current = sourceFingerprint;
        activeSource.current = {};
        lastSeen.current = {};
        rebound.current = true;   // consumed where traceSeriesRef is held
    }

    const pickSource = (id, topics) => {
        topics.forEach(t => {
            const now = messages[t];
            if (now !== undefined && lastSeen.current[t] !== now) {
                lastSeen.current[t] = now;
                activeSource.current[id] = t;
            }
        });
        // Nothing has moved yet (first paint off retained state): take the first
        // source that actually has a payload.
        if (!activeSource.current[id] || messages[activeSource.current[id]] === undefined) {
            activeSource.current[id] = topics.find(t => messages[t] !== undefined) || topics[0];
        }
        return activeSource.current[id];
    };

    const slotIdOf = (spec, i) => spec.id || `trace_${i + 1}`;
    const traceTopics = traceSpecs.map((spec, i) => pickSource(slotIdOf(spec, i), sourceTopicsOf(spec)));
    // The instrument's own answer to "is this trace showing anything".
    const modeTopics = traceSpecs.map(spec => spec.mode?.yak_listen_topic);
    const startTopic = pickSource('__x_start', sourceTopicsOf(config?.x_axis?.start || {}));
    const stopTopic = pickSource('__x_stop', sourceTopicsOf(config?.x_axis?.stop || {}));
    const stepTopic = pickSource('__x_step', sourceTopicsOf(config?.x_axis?.increment || {}));

    // Signature of the raw payloads this graph depends on. The messages object
    // gets a new identity on EVERY MQTT message on the page — a marker readout
    // ticking must not re-parse 4 x 461 samples.
    const traceDataKey = traceTopics
        .concat(modeTopics, [startTopic, stopTopic, stepTopic])
        .map(t => (t ? `${t}=${String(messages[t] || '').length}:${String(messages[t] || '').slice(-24)}` : ''))
        .join('|');

    // The span, in display units. Hoisted out of the series build because the
    // axis TYPE depends on it: a log axis cannot render a sweep that starts at
    // 0 Hz, and that is the default full-span state of every analyser here.
    //
    // TWO SHAPES OF AXIS, because two kinds of instrument describe one.
    //
    // An analyser answers with the ENDS of its sweep — start and stop — and the
    // step falls out of however many bins came back. A scope has no stop to
    // report: it answers with the time of the first sample and the interval
    // between samples, and where the trace ENDS depends on how many points the
    // capture returned. Given `x_axis.increment` this takes the second form and
    // the far end is computed per trace, from that trace's own length.
    const span = React.useMemo(() => {
        const conv = window.OaUnits ? window.OaUnits.convert : (v) => v;
        const startR = readingOf(startTopic);
        const start = Number(startR?.value);
        if (!Number.isFinite(start)) return null;
        const x0 = conv(start, startR.unit || 'Hz', xUnits);

        const stopR = readingOf(stopTopic);
        const stop = Number(stopR?.value);
        if (Number.isFinite(stop)) {
            return { x0, x1: conv(stop, stopR.unit || 'Hz', xUnits) };
        }
        const stepR = readingOf(stepTopic);
        const step = Number(stepR?.value);
        if (!Number.isFinite(step)) return null;
        return { x0, step: conv(step, stepR.unit || 'Hz', xUnits) };
    }, [traceDataKey, xUnits]);

    // `log` is honoured only where a log axis means anything.
    //
    // Two ways it does not. A span starting at 0 Hz — the default full sweep on
    // every analyser here — has no logarithm, and echarts renders the whole axis
    // blank rather than saying so, which reads as a failed capture. And a span
    // narrower than a decade has no power of ten INSIDE it: 1673–2140 MHz gets
    // zero major gridlines and one minor one at 2000, so the frequency axis
    // draws essentially no vertical lines while a linear axis of the same span
    // draws its usual evenly spaced set.
    //
    // Log therefore applies from one decade up, where the decades are what you
    // want to read against, and a narrow capture falls back to linear. Set
    // `x_axis.log_min_ratio` to override the threshold (1 forces log always).
    const wantsLog = String(config?.x_axis?.scale || xAxisCfg.scale || '').toLowerCase() === 'log';
    const logMinRatio = Number(config?.x_axis?.log_min_ratio) || 10;
    const xIsLog = wantsLog && !!span && span.x0 > 0 && span.x1 > 0
        && (span.x1 / span.x0) >= logMinRatio;

    // What mode each trace is in, in the panel's own words.
    //
    // A trace is not just a colour — MAX HOLD and LIVE REALTIME are different
    // measurements, and three overlaid curves are unreadable without saying
    // which is which. The graph already reads the mode to decide whether a
    // trace is blanked, so naming it costs nothing more on the wire.
    //
    // `mode.labels` is keyed by the long SCPI form and carries the SAME wording
    // as the trace-mode dropdown (both are stamped from Spectrum.json), so the
    // legend and that tab can never describe the same state differently.
    const modeLabels = React.useMemo(() => {
        const out = {};
        traceSpecs.forEach((spec, i) => {
            const reading = readingOf(modeTopics[i]);
            if (!reading) return;
            const m = String(reading.value).trim().toUpperCase();
            if (!m) return;
            const labels = spec.mode?.labels || {};
            // SCPI answers in the short form, so match the long key by prefix —
            // the same rule OcaDropdown uses. Unknown modes show the raw reply
            // rather than nothing: an unlabelled state is still information.
            const key = Object.keys(labels).find(k => k.toUpperCase() === m)
                || Object.keys(labels).find(k => k.toUpperCase().startsWith(m));
            out[slotIdOf(spec, i)] = key ? labels[key] : m;
        });
        return out;
    }, [traceDataKey, JSON.stringify(traceSpecs)]);

    const traceSeries = React.useMemo(() => {
        if (!traceSpecs.length || !span) return null;
        const { x0 } = span;

        const built = [];
        traceSpecs.forEach((spec, i) => {
            const id = slotIdOf(spec, i);

            // BLANK is the instrument saying "this trace shows nothing".
            //
            // A blanked trace still ANSWERS :TRACe<n>:DATA? — with whatever it
            // last held, or with the sentinel — so the samples alone cannot tell
            // you whether the operator wanted to see it. The trace mode can, and
            // it is the same fact the traces tab shows, so the graph and that
            // dropdown can never disagree. Checked before the samples are even
            // parsed: a blanked trace costs nothing.
            const mode = readingOf(modeTopics[i]);
            if (mode !== undefined) {
                // SCPI answers in the short form, so BLANK comes back as BLAN.
                const m = String(mode.value).trim().toUpperCase();
                if (m && 'BLANK'.startsWith(m)) return;
            }

            const reading = readingOf(traceTopics[i]);
            if (!reading) return;

            const ys = stripBlockHeader(reading.value).split(',');
            if (ys.length < 2) return;

            // The span is the axis: sample k sits at start + k*step. The
            // instrument never sends X, and it must not be invented from a
            // separate :FREQ:STAR? — that read can land after the span has moved.
            const step = span.step !== undefined
                ? span.step
                : (span.x1 - x0) / (ys.length - 1);
            const points = [];
            let real = 0;
            for (let k = 0; k < ys.length; k++) {
                const y = parseFloat(ys[k]);
                if (!Number.isFinite(y)) continue;
                if (y > BLANK_FLOOR_DBM) real++;
                points.push([x0 + k * step, y]);
            }
            if (!real) return;   // whole trace is the blank sentinel — not drawn

            built.push({
                id,
                name: spec.label?.[lang] || spec.label?.En || id,
                type: 'line',
                showSymbol: false,
                symbol: 'none',
                animation: false,
                sampling: 'lttb',
                lineStyle: { color: spec.color || undefined, width: spec.width || 1.5 },
                itemStyle: { color: spec.color || undefined },
                data: points,
            });
        });
        return built;
    }, [traceDataKey, JSON.stringify(traceSpecs), lang, xUnits, span]);

    // Last non-null build, so a structural re-apply can restate the traces
    // instead of clearing them.
    //
    // Dropped when the graph is rebound to another instrument: "keep showing
    // the last thing that built" is right across a re-render and wrong across a
    // device switch, where the last thing that built belongs to a different
    // oscilloscope. A scope that has not been asked for a trace shows none.
    const traceSeriesRef = React.useRef(null);
    if (rebound.current) {
        traceSeriesRef.current = null;
        rebound.current = false;
    }
    if (traceSeries) traceSeriesRef.current = traceSeries;

    // The mode is shown by a legend FORMATTER, not by renaming the series.
    //
    // echarts keys legend show/hide on the series name, so folding the mode into
    // the name would reset every manual hide the moment a trace changed mode —
    // the one thing you would be watching the legend for.
    const legendSuffix = React.useMemo(() => {
        const out = {};
        traceSpecs.forEach((spec, i) => {
            const id = slotIdOf(spec, i);
            const name = spec.label?.[lang] || spec.label?.En || id;
            if (modeLabels[id]) out[name] = modeLabels[id];
        });
        return out;
    }, [modeLabels, JSON.stringify(traceSpecs), lang]);
    const legendSuffixRef = React.useRef({});
    legendSuffixRef.current = legendSuffix;
    const legendFormatter = React.useCallback(
        (name) => {
            const mode = legendSuffixRef.current[name];
            return mode ? `${name}  ·  ${mode}` : name;
        },
        [],
    );

    // THE SPAN IS THE AXIS. There is no data outside it and no meaning either —
    // the instrument measured 461 points between these two frequencies and
    // nothing else. Left unbounded, echarts picks its own round numbers, which
    // is why zooming out ran the axis down towards 0 MHz through empty space,
    // and why a log axis showed a bare 100 → 1,000 decade with the capture
    // crammed against the right edge. An authored min/max still wins.
    //
    // In step mode there is no reported far end — it is wherever the samples ran
    // out — so it comes off the trace that was actually built.
    const stepEnd = React.useMemo(() => {
        if (!span || span.step === undefined) return undefined;
        let end;
        (traceSeriesRef.current || []).forEach(s => {
            const last = s.data[s.data.length - 1];
            if (last && (end === undefined || last[0] > end)) end = last[0];
        });
        return end;
    }, [traceSeries, span]);

    // Stable signature of everything that affects chart STRUCTURE. Options are
    // re-applied only when this string changes — NOT on every render. `config` gets
    // a fresh identity each render and unrelated MQTT updates re-render every widget,
    // so without this the chart was torn down + redrawn on any GUI change.
    const cfgKey = JSON.stringify({
        datasets: config?.datasets, axis: config?.axis, title, nav: !!config?.Navigation,
        x_axis: config?.x_axis, units: config?.units, traceMode: !!traceSpecs.length, xIsLog,
        span,      // the axis bounds are the span, so a new capture re-applies them
        stepEnd,   // …and in step mode, half of them come from the samples
        // Being pointed at a different instrument IS a structural change. The
        // live-trace effect below returns early when there is nothing to draw,
        // which is exactly the state a freshly-selected scope is in — so
        // without this the chart would keep the previous one's curve until
        // someone captured on the new one.
        sourceFingerprint,
    });

    const xMin = xAxisCfg.min ?? config?.x_axis?.min ?? (traceSpecs.length && span ? span.x0 : undefined);
    const xMax = xAxisCfg.max ?? config?.x_axis?.max
        ?? (traceSpecs.length && span ? (span.x1 ?? stepEnd) : undefined);

    // `x_axis.si_labels` — the prefix on the TICK rather than in the axis name.
    //
    // A scope's window spans nine orders of magnitude across one knob: twelve
    // divisions of 1 ns at the fast end of the timebase, of 10 s at the slow.
    // No single fixed unit is readable at both — milliseconds render a
    // nanosecond capture as 0.000012 — so the tick carries the prefix and the
    // same axis reads 12 ns and 1.5 ms without being re-authored.
    const siBase = config?.x_axis?.units || '';
    const siLabel = React.useCallback((v) => {
        const n = Number(v);
        if (!Number.isFinite(n)) return String(v);
        if (n === 0) return `0 ${siBase}`;
        const STEPS = [[1e9, 'G'], [1e6, 'M'], [1e3, 'k'], [1, ''],
                       [1e-3, 'm'], [1e-6, 'µ'], [1e-9, 'n'], [1e-12, 'p']];
        const a = Math.abs(n);
        const [scale, prefix] = STEPS.find(([s]) => a >= s) || STEPS[STEPS.length - 1];
        return `${Number((n / scale).toFixed(3))} ${prefix}${siBase}`;
    }, [siBase]);

    // A trace graph is titled by the block that contains it; a plain graph is
    // not, so it keeps its own heading.
    const showTitle = config?.show_title === true
        || (!traceSpecs.length && config?.show_title !== false);

    // Axis names. In trace mode the units come off the widget (`units`: dBm,
    // `x_axis.units`: MHz) rather than an authored `axis` block, so the operator
    // is never left reading an unlabelled number.
    const xName = xAxisCfg.label?.[lang] || xAxisCfg.label?.En
        || config?.x_axis?.label?.[lang] || config?.x_axis?.label?.En
        || (traceSpecs.length ? `Frequency (${xUnits})` : "");
    const yName = yAxisCfg.label?.[lang] || yAxisCfg.label?.En
        || (traceSpecs.length && config?.units ? config.units : "");

    React.useEffect(() => {
        if (!chartRef.current || typeof echarts === 'undefined') return;

        // Init ONCE; reuse the instance afterwards (no dispose/redraw churn).
        if (!chartInstance.current) {
            chartInstance.current = echarts.init(chartRef.current, 'dark');
        }

        const initialSeries = (config?.datasets || []).map(ds => {
            const seriesName = ds.id || ds.label?.[lang] || ds.label?.En || 'Series';
            return {
                id: ds.id,
                name: seriesName,
                type: 'line',
                smooth: ds.style?.smooth === true || (ds.style?.smoothing > 0),
                showSymbol: ds.style?.showSymbol !== false,
                data: ds.initial_csv_data ? parseCsv(ds.initial_csv_data) : [],
                lineStyle: {
                    color: ds.style?.line_color || '#0f0',
                    width: ds.style?.line_width || 2
                },
                itemStyle: { color: ds.style?.line_color || '#0f0' }
            };
        });

        const option = {
            backgroundColor: 'transparent',
            // No title in trace mode. The block above the widget already says
            // what this is, so a second heading spends ~30px of chart height
            // repeating it — on a spectrum trace that is dynamic range you can
            // see. `show_title: true` puts it back.
            title: showTitle ? {
                text: title,
                left: 'center',
                textStyle: { color: '#ccc', fontSize: 14 }
            } : { show: false },
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } }
            },
            // Four overlaid traces are unreadable without saying which is which
            // — and WHAT each one is: MAX HOLD and LIVE REALTIME are different
            // measurements, not two colours of the same thing.
            legend: traceSpecs.length ? {
                top: showTitle ? 22 : 2, textStyle: { color: '#aaa', fontSize: 11 }, itemHeight: 8,
                formatter: legendFormatter,
            } : undefined,
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                top: traceSpecs.length ? (showTitle ? 60 : 30) : undefined,
                containLabel: true,
                show: showGrid,
                borderColor: '#333'
            },
            xAxis: {
                type: (xIsLog || (!traceSpecs.length && xAxisCfg.scale === 'log')) ? 'log' : 'value',
                name: xName,
                nameLocation: 'middle',
                nameGap: 25,
                // A span is not anchored at zero either. Without `scale`, echarts
                // pads a value axis down to 0, so a 1673–2140 MHz capture drew
                // itself squeezed into the right fifth of a 0–2500 MHz axis.
                scale: traceSpecs.length > 0,
                splitLine: { show: showGrid, lineStyle: { color: '#444' } },
                // A log axis puts its major lines on the decades. A capture is
                // usually a slice of ONE decade — 1673 to 2140 MHz has no power
                // of ten inside it — so the major lines land outside the chart
                // and the frequency axis draws no vertical lines at all. The
                // minor subdivisions are the ones you actually read against.
                minorTick: { show: xIsLog },
                minorSplitLine: { show: xIsLog && showGrid, lineStyle: { color: '#2b2b2b' } },
                axisLine: { lineStyle: { color: xAxisCfg.color || '#555' } },
                axisLabel: config?.x_axis?.si_labels ? { formatter: siLabel } : undefined,
                min: xMin,
                max: xMax
            },
            yAxis: {
                type: yAxisCfg.scale === 'log' ? 'log' : 'value',
                name: yName,
                nameLocation: 'middle',
                nameGap: 40,
                // dBm is not anchored at zero — echarts' default `scale: false`
                // pads the axis down to it, squashing a -60 dBm noise floor into
                // the top sliver of the chart.
                scale: traceSpecs.length > 0,
                splitLine: { show: showGrid, lineStyle: { color: '#444' } },
                axisLine: { lineStyle: { color: yAxisCfg.color || '#555' } },
                min: yAxisCfg.min,
                max: yAxisCfg.max
            },
            dataZoom: config?.Navigation ? [
                { type: 'inside', start: 0, end: 100 },
                { type: 'slider', bottom: 10, height: 20, borderColor: '#333', handleStyle: { color: '#555' } }
            ] : [],
            // A structural re-apply must not blank the live traces: cfgKey can
            // change (a language switch, a resize-driven layout edit) long after
            // the last capture, and the data effect below will not re-run because
            // the samples themselves did not change.
            series: traceSpecs.length ? (traceSeriesRef.current || []) : initialSeries
        };

        chartInstance.current.setOption(option, { replaceMerge: 'series' });
    }, [cfgKey, lang]);

    // Live traces -> chart. `replaceMerge` because the series COUNT varies: a
    // trace that gets blanked on the instrument drops out of the list, and
    // echarts' default merge-by-index would leave its last samples on screen
    // forever.
    React.useEffect(() => {
        if (!traceSeries || !chartInstance.current) return;
        // The legend rides along: its formatter reads the CURRENT mode, so a
        // trace switching to MAX HOLD must redraw the label, not just the curve.
        chartInstance.current.setOption(
            { series: traceSeries, legend: { formatter: legendFormatter } },
            { replaceMerge: 'series' },
        );
    }, [traceSeries]);

    // Resize listener + dispose — mount/unmount only.
    //
    // The window event is not enough now that a graph may be sized by `height:
    // "100%"` instead of a fixed pixel count: its box changes whenever anything
    // ABOVE it does — a second tab row appearing, a block folding open — and the
    // window never resized, so echarts kept drawing at the old height inside a
    // box that had already moved. Watch the element, not the window.
    React.useEffect(() => {
        const resizeHandler = () => chartInstance.current && chartInstance.current.resize();
        window.addEventListener('resize', resizeHandler);
        const ro = (window.ResizeObserver && chartRef.current)
            ? new window.ResizeObserver(resizeHandler) : null;
        if (ro) ro.observe(chartRef.current);
        return () => {
            window.removeEventListener('resize', resizeHandler);
            if (ro) ro.disconnect();
            if (chartInstance.current) { chartInstance.current.dispose(); chartInstance.current = null; }
        };
    }, []);

    // Handle incoming real-time data from MQTT
    React.useEffect(() => {
        // Trace mode owns the series. The legacy path merges by series id from a
        // `{id: [[x,y]…]}` payload, and a widget whose own control topic happens
        // to carry an object would silently overwrite the captured waveforms.
        if (traceSpecs.length) return;
        if (mqttData && chartInstance.current) {
            let parsedMqttData = mqttData;
            if (typeof mqttData === 'string') {
                try {
                    parsedMqttData = JSON.parse(mqttData);
                } catch (e) { return; }
            }

            const updates = [];
            Object.entries(parsedMqttData).forEach(([datasetId, points]) => {
                if (Array.isArray(points)) {
                    // Try to find series by ID first, then fallback to name matching
                    updates.push({
                        id: datasetId,
                        data: points
                    });
                }
            });
            
            if (updates.length > 0) {
                chartInstance.current.setOption({ series: updates });
            }
        }
    }, [mqttData, traceSpecs.length]);

    // The pop-out lives in OaPopout.Host (wrapped on by FieldComponent), which
    // MOVES this element rather than re-plotting a copy of it: one chart
    // instance, so a new capture reaches the detached window by simply arriving.
    // The private version that used to live here wrote a snapshot of `option`
    // into a fresh document, which never updated again, and left the tab drawing
    // its own — live — copy beside it.
    return (
        <div style={{ width: width, height: height || '100%', flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', position: 'relative' }}>
            <div
                ref={chartRef}
                style={{ flexGrow: 1, width: '100%', minHeight: '100px', border: '1px solid #333', borderRadius: '4px', backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#111') : '#111') }}
            />
        </div>
    );
};
// Skip re-render when neither the live data nor the config CONTENT changed — this
// stops unrelated GUI changes (which re-render every widget via the MQTT context)
// from cascading into the graph.
window.DynamicGraph = React.memo(DynamicGraph, (prev, next) =>
    prev.value === next.value &&
    JSON.stringify(prev.config) === JSON.stringify(next.config)
);