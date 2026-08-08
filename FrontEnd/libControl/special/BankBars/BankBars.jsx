/**
 * Header: BankBars.jsx
 * Purpose: Every instrument's latest reading, side by side.
 * Description: One bar per device answering a named reading, with its value and unit.
 *
 * Version: 26.08.08.1
 * Change Log:
 * - 2026-08-08: Initial version — DMM bank.
 */

// A bank view asks a question no per-device panel can: how do the meters
// COMPARE. Eight tabs each showing one number cannot answer it, and neither can
// eight copies of a meter widget — the comparison is the point, so the bars
// have to share one scale.
//
// The devices are found on the BUS, not passed in. Readings are retained and
// their topics name the instrument that produced them, so a wildcard over
// `.../Device/DMM/+/+/Reading/Read_Next` is already the list of every DMM that
// has ever answered — including one that joined the bench after this page was
// built. Nothing to stamp, nothing to keep in step with discovery.
const BankBars = ({ config }) => {
    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const pattern = config?.match
        || 'OpenAir/System/Protocols/visa/Device/DMM/+/+/Reading/Read_Next';
    const names = config?.names || {};
    const colors = config?.cosmetics?.colors || {};
    const barColor = colors.primary || '#39D353';
    const negColor = colors.secondary || '#FF6B6B';
    const rowH = Number(config?.row_height) || 28;

    const label = (() => {
        const l = config?.label;
        if (!l) return '';
        if (typeof l === 'string') return l;
        return l[lang] || l.En || '';
    })();

    // MQTT wildcards, because that is the syntax everything else here already
    // uses: `+` is one level, `#` is the rest.
    const matches = React.useCallback((topic) => {
        const p = pattern.split('/');
        const t = topic.split('/');
        for (let i = 0; i < p.length; i += 1) {
            if (p[i] === '#') return true;
            if (i >= t.length) return false;
            if (p[i] !== '+' && p[i] !== t[i]) return false;
        }
        return p.length === t.length;
    }, [pattern]);

    // A QUANTITY THE INSTRUMENT DOES NOT REPORT.
    //
    // A 66101A answers volts and amps; watts is the two of them multiplied, and
    // nothing on the bus carries it. Rather than have the panel ask for a
    // reading that does not exist, `multiply_by` names a second pattern and the
    // row becomes the product.
    //
    // The partner topic is found by REBINDING: whatever each `+` matched in the
    // first pattern is substituted into the second in the same order, so both
    // readings are guaranteed to come from the same device. Pairing them by
    // position in two separately-sorted lists would silently multiply one
    // module's volts by another's amps the moment a device dropped off the bus.
    const rebind = React.useCallback((target, topic) => {
        if (!target) return '';
        const p = pattern.split('/');
        const t = topic.split('/');
        const binds = [];
        for (let i = 0; i < p.length && i < t.length; i += 1) {
            if (p[i] === '#') break;
            if (p[i] === '+') binds.push(t[i]);
        }
        let k = 0;
        return target.split('/').map((s) => (s === '+' ? binds[k++] : s)).join('/');
    }, [pattern]);

    const partnerPattern = config?.multiply_by || '';
    const partnerOf = React.useCallback(
        (topic) => rebind(partnerPattern, topic), [rebind, partnerPattern]);

    // `unit_from` names a reading whose VALUE is the unit's name; `unit_map`
    // translates the instrument's word into the symbol to print. An unmapped
    // word is shown as-is rather than dropped — a reading labelled DIOD is
    // still more use than one labelled nothing.
    const unitFromPattern = config?.unit_from || '';
    const unitFor = React.useCallback(
        (topic) => rebind(unitFromPattern, topic), [rebind, unitFromPattern]);
    const unitMap = React.useMemo(() => {
        const raw = config?.unit_map || {};
        const out = {};
        for (const k of Object.keys(raw)) out[k.toUpperCase()] = raw[k];
        return out;
    }, [JSON.stringify(config?.unit_map)]);

    const readingAt = React.useCallback((topic) => {
        const raw = messages[topic];
        if (raw === undefined) return { value: undefined, unit: '' };
        try {
            const parsed = JSON.parse(String(raw));
            if (parsed && typeof parsed === 'object' && parsed.value !== undefined) {
                return { value: Number(parsed.value), unit: parsed.unit || '' };
            }
        } catch (e) { /* plain payload */ }
        return { value: Number(raw), unit: '' };
    }, [messages]);

    const rows = React.useMemo(() => {
        const out = [];
        for (const topic of Object.keys(messages)) {
            if (!matches(topic)) continue;
            let { value, unit } = readingAt(topic);
            if (partnerPattern) {
                const other = readingAt(partnerOf(topic));
                // Both halves or nothing: half a product is not a smaller
                // number, it is a different quantity.
                value = (Number.isFinite(value) && Number.isFinite(other.value))
                    ? value * other.value : undefined;
                unit = config?.unit || 'W';
            }
            // A UNIT THE INSTRUMENT REPORTS AS A WORD.
            //
            // `:READ?` on a meter answers a bare number: volts, ohms and hertz
            // are indistinguishable, and no static unit can be declared for it
            // because the unit IS the selected function. So the row takes its
            // unit from the function read back beside it — same round trip,
            // same device, found by the same wildcard rebinding as the product
            // above. Eight meters on eight different functions each label
            // themselves correctly.
            if (unitFromPattern) {
                const word = String(readingAt(unitFor(topic)).value ?? '').trim();
                if (word && word !== 'undefined' && word !== 'NaN') {
                    const key = word.toUpperCase();
                    unit = unitMap[key] !== undefined ? unitMap[key] : word;
                }
            }
            if (config?.unit) unit = config.unit;
            // `.../Device/<type>/<model>/<dev>/Reading/<command>` — the model and
            // the device slot are the instrument's name until someone gives it a
            // friendlier one via `names`.
            const seg = topic.split('/');
            const at = seg.indexOf('Device');
            const model = at >= 0 ? seg[at + 2] : '';
            const dev = at >= 0 ? seg[at + 3] : '';
            const key = `${model}/${dev}`;
            out.push({
                topic,
                key,
                name: names[key] || names[topic] || `${model} · ${dev}`,
                value,
                unit,
                stale: !Number.isFinite(value),
            });
        }
        // RACK ORDER, and the same order in every graph.
        //
        // When the builder has supplied names they lead with the channel — CH1,
        // CH2, … — and that number is the rack's own numbering, so it sorts
        // ahead of anything derivable from the topic. Without names, fall back
        // to model then device NUMBER: a string sort puts Dev10 between Dev1 and
        // Dev2, which would leave the eighth module in the middle of the list
        // and the three graphs disagreeing about which row is which.
        const trailing = (s) => {
            const m = /(\d+)\s*$/.exec(s);
            return m ? parseInt(m[1], 10) : Number.MAX_SAFE_INTEGER;
        };
        const leading = (s) => {
            const m = /(\d+)/.exec(s);
            return m ? parseInt(m[1], 10) : null;
        };
        out.sort((a, b) => {
            const an = leading(a.name), bn = leading(b.name);
            if (an !== null && bn !== null && an !== bn) return an - bn;
            const am = a.key.replace(/\d+\s*$/, ''), bm = b.key.replace(/\d+\s*$/, '');
            return am === bm ? trailing(a.key) - trailing(b.key) : am.localeCompare(bm);
        });
        return out;
    }, [messages, matches, readingAt, partnerOf, partnerPattern, unitFor,
        unitFromPattern, unitMap, config?.unit, JSON.stringify(names)]);

    // One scale for all of them, or the bars are eight unrelated pictures.
    const peak = rows.reduce((m, r) => (Number.isFinite(r.value) ? Math.max(m, Math.abs(r.value)) : m), 0) || 1;

    const show = (v) => {
        if (!Number.isFinite(v)) return '—';
        const a = Math.abs(v);
        if (a !== 0 && (a < 0.001 || a >= 1e6)) return v.toExponential(4);
        return v.toFixed(a >= 100 ? 2 : a >= 1 ? 4 : 6);
    };

    return (
        <div style={{ width: '100%', boxSizing: 'border-box', padding: '4px 6px' }}>
            {label && (
                <div style={{ color: '#999', fontSize: '10px', fontWeight: 'bold', marginBottom: '4px' }}>
                    {label.toUpperCase()}
                </div>
            )}
            {!rows.length && (
                <div style={{ color: '#666', fontSize: '11px', padding: '10px 2px' }}>
                    No instrument has answered yet — press GET ALL VALUES.
                </div>
            )}
            {rows.map((r) => (
                <div key={r.topic} style={{ display: 'flex', alignItems: 'center', height: `${rowH}px`, gap: '8px' }}>
                    <div style={{ width: '150px', flexShrink: 0, color: '#ccc', fontSize: '11px',
                                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                         title={r.topic}>
                        {r.name}
                    </div>
                    <div style={{ flexGrow: 1, height: `${Math.max(8, rowH - 12)}px`, background: '#1a1a1a',
                                  border: '1px solid #333', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{
                            width: `${Math.min(100, (Math.abs(r.value) / peak) * 100 || 0)}%`,
                            height: '100%',
                            background: r.value < 0 ? negColor : barColor,
                            transition: 'width 0.2s',
                        }} />
                    </div>
                    <div style={{ width: '140px', flexShrink: 0, textAlign: 'right', color: '#fff',
                                  fontSize: '12px', fontFamily: 'Segoe UI, sans-serif' }}>
                        {show(r.value)} <span style={{ color: '#999' }}>{r.unit}</span>
                    </div>
                </div>
            ))}
        </div>
    );
};

window.BankBars = BankBars;
