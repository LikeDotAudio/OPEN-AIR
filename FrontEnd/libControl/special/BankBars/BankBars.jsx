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

    const rows = React.useMemo(() => {
        const out = [];
        for (const topic of Object.keys(messages)) {
            if (!matches(topic)) continue;
            let value, unit = '';
            try {
                const parsed = JSON.parse(String(messages[topic]));
                if (parsed && typeof parsed === 'object' && parsed.value !== undefined) {
                    value = Number(parsed.value);
                    unit = parsed.unit || '';
                } else {
                    value = Number(messages[topic]);
                }
            } catch (e) {
                value = Number(messages[topic]);
            }
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
        out.sort((a, b) => a.key.localeCompare(b.key));
        return out;
    }, [messages, matches, JSON.stringify(names)]);

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
