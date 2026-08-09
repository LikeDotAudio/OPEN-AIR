/**
 * Header: CrossMatrix.jsx
 * Purpose: A crosspoint matrix card — buses down the side, sources across the top.
 * Description: One widget per card. Cells are library buttons; a row change sends OPEN then CLOSE.
 *
 * Version: 26.08.08.2
 * Change Log:
 * - 2026-08-08: Replaces MatrixRow — the bus names are column titles, not cell text.
 * - 2026-08-08: Pivoted — buses are now the screen rows, source names the column
 *   titles, and the cells suppress ButtonToggle's caption.
 */

// EACH AXIS GETS NAMED ONCE.
//
// Eight rows of four buttons each reading "SCOPE IN 2 (022)" says the same four
// words thirty-two times and still leaves the source name squeezed into the
// margin. A matrix has two axes and each one gets named once: the buses down
// the side, the sources across the top, and the cell carries only the
// crosspoint it closes.
//
// The buses go on the left because there are few of them and their names are
// short, while the source names are long enough to want a column of their own.
//
// That is also why this is ONE widget per card rather than eight row widgets —
// a header has to line up with the grid beneath it, and two independent
// components cannot promise that.
//
// A press still sends the whole SOURCE ROW, which is the part that keeps the
// relays honest on a matrix:
//
//     OPEN  every crosspoint in that row now off
//     CLOSE every crosspoint in that row now on
//
// Open first — break-before-make, so a dropped source is disconnected before
// the next arrives. Stating the row whole makes it idempotent: whatever the
// relays were doing beforehand, afterwards they match what is lit.
const CrossMatrix = ({ value, onChange, config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const [lit, setLit] = useMqtt
        ? window.useMqttState(topic, value !== undefined ? value : '', nodeJson)
        : [value, onChange, 'En'];
    const trigger = window.useMqttTrigger ? window.useMqttTrigger() : null;
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const text = (l, fallback) => {
        if (!l) return fallback;
        if (typeof l === 'string') return l;
        return l[lang] || l.En || fallback;
    };

    const slot = Number(config?.slot) || 0;
    const buses = Array.isArray(config?.buses) ? config.buses : [];      // rows on screen
    const sources = Array.isArray(config?.sources) ? config.sources : []; // columns on screen

    // channel = slot*100 + row*10 + column, straight off the module schematic.
    const channelAt = (sourceIdx, busIdx) =>
        `${slot * 100 + (busIdx + 1) * 10 + (sourceIdx + 1)}`.padStart(3, '0');

    const closed = React.useMemo(() => {
        const s = new Set(String(lit == null ? '' : lit)
            .split(',').map((x) => x.trim()).filter(Boolean));
        return s;
    }, [lit]);

    const siblingTopic = (leaf) => {
        const parts = String(topic || '').split('/');
        if (parts.length < 2 || !leaf) return '';
        parts[parts.length - 1] = leaf;
        return parts.join('/');
    };
    const openTopic = siblingTopic(config?.opens || 'Open_Cmd');
    const closeTopic = siblingTopic(config?.closes || 'Close_Cmd');

    const press = (sourceIdx, busIdx) => {
        const me = channelAt(sourceIdx, busIdx);
        const rowAll = buses.map((_, b) => channelAt(sourceIdx, b));
        const next = new Set(closed);
        if (next.has(me)) next.delete(me); else next.add(me);

        const on = rowAll.filter((c) => next.has(c));
        const off = rowAll.filter((c) => !next.has(c));

        // Keep every other row's state; only this source's row was touched.
        const all = [];
        sources.forEach((_, s) => buses.forEach((__, b) => {
            const c = channelAt(s, b);
            if (next.has(c)) all.push(c);
        }));
        setLit(all.join(','));

        if (!trigger) return;
        if (off.length && openTopic) trigger(openTopic, off.join(','));
        if (on.length && closeTopic) trigger(closeTopic, on.join(','));
    };

    const style = config?.style || {};
    const cell = config?.cell || {};
    const cellW = cell.width || 150;
    const cellH = cell.height || 34;
    const nameW = cell.name_width || 190;

    // Each cell is the library's own toggle, so a crosspoint looks like every
    // other button on the bench rather than a div someone drew here.
    const Button = window.ButtonToggle;

    return (
        <div style={{ width: '100%', boxSizing: 'border-box', padding: '4px 6px', overflowX: 'auto' }}>
            {/* Source titles */}
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', marginBottom: '4px' }}>
                <div style={{ width: `${nameW}px`, flexShrink: 0, color: '#666', fontSize: '10px' }}>
                    {text(config?.corner, 'BUS \\ SOURCE')}
                </div>
                {sources.map((s, i) => (
                    <div key={i} style={{
                        width: `${cellW}px`, flexShrink: 0, textAlign: 'center',
                        color: '#ccc', fontSize: '11px', fontWeight: 'bold',
                        borderBottom: '1px solid #444', paddingBottom: '2px',
                    }} title={text(s.label, '')}>
                        {text(s.label, s.name || `SOURCE ${i + 1}`)}
                        <div style={{ color: '#666', fontWeight: 'normal', fontSize: '9px' }}>
                            Ø{i + 1}
                        </div>
                    </div>
                ))}
            </div>

            {buses.map((b, bi) => (
                <div key={bi} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '3px' }}>
                    <div style={{
                        width: `${nameW}px`, flexShrink: 0, color: '#ccc', fontSize: '11px',
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }} title={text(b.label, '')}>
                        {text(b.label, b.name || `BUS ${bi + 1}`)}
                        <span style={{ color: '#666' }}>{'  '}row {(bi + 1) * 10}</span>
                    </div>
                    {sources.map((s, si) => {
                        const ch = channelAt(si, bi);
                        const on = closed.has(ch);
                        const cfg = {
                            type: '_GuiButtonToggle',
                            label_active: ch,
                            label_inactive: ch,
                            // The crosspoint number is already printed on the face;
                            // without this the shared toggle prints its own fallback
                            // caption, "Toggle", over every cell in the grid.
                            show_label: false,
                            layout: { width: cellW, height: cellH },
                            style,
                            latching: true,
                        };
                        return (
                            <div key={si} style={{ flexShrink: 0 }}
                                 title={`${text(s.label, '')} → ${text(b.label, '')}  (close ${ch})`}>
                                {Button
                                    ? <Button value={on} onChange={() => press(si, bi)} config={cfg} nodeJson={cfg} />
                                    : <button onClick={() => press(si, bi)}>{ch}</button>}
                            </div>
                        );
                    })}
                </div>
            ))}
        </div>
    );
};

window.CrossMatrix = CrossMatrix;
