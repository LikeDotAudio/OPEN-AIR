/**
 * Header: CMDPEditor.jsx
 * Purpose: CMDPEditor component or utility.
 * Description: Handles logic and rendering for CMDPEditor component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// CMDPEditor - Grouping & Editing panel for the CMDP
// Author: Anthony Peter Kuzub / Claude (Collaborator)
// Version: 20260701.1500.0
//
// Description: A DOM companion element for the CMDP (Circular Motion Displacement
// Potentiometer). It edits the same channels[] / group_configs[] data the CMDP
// renders — group visibility / solo / mute / rename / colour, and per-channel
// rename / group reassignment / visibility / mute / level·depth·angle — and
// publishes the full { channels, group_configs } state via onChange. Point this
// element and a CMDP at the SAME MQTT path and edits live-update the display.

// Inline comment: Logic for CMDPEditor
const CMDPEditor = ({ config, value, onChange }) => {
    const accent = config?.color || '#f4902c';

    // Effective state: prefer the live shared value, fall back to the config node.
    const channels = (value && value.channels)
        || config?.channels || config?.nodeJson?.channels || [];
    const groups = (value && value.group_configs)
        || config?.group_configs || config?.nodeJson?.group_configs || [];

    // Every edit publishes the FULL state so the shared value always carries both
    // channels and groups (a CMDP drag preserves groups the same way).
    const commit = (nextChannels, nextGroups) => {
        if (onChange) onChange({ channels: nextChannels, group_configs: nextGroups });
    };

    const cloneCh = () => channels.map(c => ({ ...c }));
    const cloneGr = () => groups.map(g => ({ ...g }));

    // --- Group mutations ----------------------------------------------------
    const setGroup = (gi, patch) => { const g = cloneGr(); g[gi] = { ...g[gi], ...patch }; commit(cloneCh(), g); };
    const soloGroup = (gi) => { const g = cloneGr().map((grp, i) => ({ ...grp, visible: i === gi })); commit(cloneCh(), g); };
    const renameGroup = (gi, name) => {
        // Rename cascades to channels that referenced the old group name.
        const oldName = groups[gi]?.name;
        const g = cloneGr(); g[gi] = { ...g[gi], name };
        const c = cloneCh().map(ch => (ch.group === oldName ? { ...ch, group: name } : ch));
        commit(c, g);
    };
    const addGroup = () => {
        const palette = ['#FF4444', '#FFFF44', '#44FF44', '#44FFFF', '#4444FF', '#FF44FF', '#FF4488', '#888888'];
        const g = cloneGr();
        g.push({ name: `Group ${g.length + 1}`, color: palette[g.length % palette.length], visible: true, mute: false });
        commit(cloneCh(), g);
    };
    const removeGroup = (gi) => { const g = cloneGr(); g.splice(gi, 1); commit(cloneCh(), g); };

    // --- Channel mutations --------------------------------------------------
    const setChan = (ci, patch) => { const c = cloneCh(); c[ci] = { ...c[ci], ...patch }; commit(c, cloneGr()); };
    const addChannel = () => {
        const c = cloneCh();
        const maxId = c.reduce((m, ch) => Math.max(m, Number(ch.id) || 0), 0);
        c.push({ id: maxId + 1, name: `Ch ${maxId + 1}`, group: groups[0]?.name || '', angle: 0, level: 70, depth: 50, visible: true, mute: false });
        commit(c, cloneGr());
    };
    const removeChannel = (ci) => { const c = cloneCh(); c.splice(ci, 1); commit(c, cloneGr()); };

    // --- Styling ------------------------------------------------------------
    const S = {
        wrap: { background: 'rgba(28,28,30,0.94)', color: '#eee', font: '12px Arial', padding: '10px', borderRadius: '6px', border: `1px solid ${accent}`, boxShadow: '0 4px 18px rgba(0,0,0,0.6)', width: '100%', boxSizing: 'border-box', maxHeight: '100%', overflow: 'auto' },
        h: { color: accent, fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '1px', fontSize: '11px', margin: '4px 0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: `1px solid ${accent}`, paddingBottom: '3px' },
        row: { display: 'flex', alignItems: 'center', gap: '4px', padding: '3px 0', borderBottom: '1px solid #333' },
        name: { flex: '1 1 60px', minWidth: 0, background: '#333', color: '#eee', border: '1px solid #444', borderRadius: '3px', padding: '2px 4px', font: '12px Arial' },
        num: { width: '42px', background: '#333', color: '#eee', border: '1px solid #444', borderRadius: '3px', padding: '2px', font: '11px Arial', textAlign: 'center' },
        sel: { background: '#333', color: '#eee', border: '1px solid #444', borderRadius: '3px', padding: '2px', font: '11px Arial' },
        color: { width: '22px', height: '20px', padding: 0, border: '1px solid #444', background: 'none', borderRadius: '3px', cursor: 'pointer' },
        dot: (col) => ({ width: '12px', height: '12px', borderRadius: '50%', background: col, flex: '0 0 auto', boxShadow: '0 0 3px rgba(0,0,0,0.6)' }),
        btn: (on, col) => ({ cursor: 'pointer', userSelect: 'none', border: `1px solid ${on ? (col || '#aaa') : '#444'}`, background: on ? (col ? col : '#444') : '#2a2a2a', color: on ? '#fff' : '#777', borderRadius: '3px', padding: '2px 5px', fontSize: '11px', lineHeight: '14px' }),
        add: { cursor: 'pointer', border: `1px solid ${accent}`, color: accent, background: 'none', borderRadius: '3px', padding: '1px 8px', fontSize: '11px', fontWeight: 'bold' },
        x: { cursor: 'pointer', color: '#c55', border: '1px solid #533', background: '#2a2a2a', borderRadius: '3px', padding: '2px 5px', fontSize: '11px' },
    };

    const groupColorOf = (name) => (groups.find(g => g.name === name) || {}).color || accent;
    const num = (v, d) => { const n = parseFloat(v); return Number.isFinite(n) ? n : d; };

    return (
        <div style={S.wrap}>
            <div style={S.h}>
                <span>Groups</span>
                <button style={S.add} onClick={addGroup}>+ Group</button>
            </div>
            {groups.map((g, gi) => (
                <div key={`g-${gi}`} style={S.row}>
                    <input type="color" style={S.color} value={g.color || accent}
                        onChange={(e) => setGroup(gi, { color: e.target.value })} title="Group colour" />
                    <input style={S.name} value={g.name || ''}
                        onChange={(e) => renameGroup(gi, e.target.value)} />
                    <span style={S.btn(g.visible !== false, accent)} title="Visible"
                        onClick={() => setGroup(gi, { visible: g.visible === false })}>👁</span>
                    <span style={S.btn(false)} title="Solo this group"
                        onClick={() => soloGroup(gi)}>Solo</span>
                    <span style={S.btn(!!g.mute, '#a33')} title="Mute"
                        onClick={() => setGroup(gi, { mute: !g.mute })}>M</span>
                    <span style={S.x} title="Remove group" onClick={() => removeGroup(gi)}>✕</span>
                </div>
            ))}

            <div style={{ ...S.h, marginTop: '12px' }}>
                <span>Channels ({channels.length})</span>
                <button style={S.add} onClick={addChannel}>+ Channel</button>
            </div>
            {channels.map((ch, ci) => (
                <div key={`c-${ci}`} style={S.row}>
                    <span style={S.dot(groupColorOf(ch.group))} />
                    <input style={S.name} value={ch.name || ''}
                        onChange={(e) => setChan(ci, { name: e.target.value })} />
                    <select style={S.sel} value={ch.group || ''}
                        onChange={(e) => setChan(ci, { group: e.target.value })}>
                        {groups.map((g, gi) => <option key={gi} value={g.name}>{g.name}</option>)}
                    </select>
                    <input style={S.num} type="number" title="Level" value={num(ch.level, 0)}
                        onChange={(e) => setChan(ci, { level: num(e.target.value, 0) })} />
                    <input style={S.num} type="number" title="Depth" value={num(ch.depth, 0)}
                        onChange={(e) => setChan(ci, { depth: num(e.target.value, 0) })} />
                    <input style={S.num} type="number" title="Angle" value={num(ch.angle, 0)}
                        onChange={(e) => setChan(ci, { angle: num(e.target.value, 0) })} />
                    <span style={S.btn(ch.visible !== false, accent)} title="Visible"
                        onClick={() => setChan(ci, { visible: ch.visible === false })}>👁</span>
                    <span style={S.btn(!!ch.mute, '#a33')} title="Mute"
                        onClick={() => setChan(ci, { mute: !ch.mute })}>M</span>
                    <span style={S.x} title="Remove channel" onClick={() => removeChannel(ci)}>✕</span>
                </div>
            ))}
        </div>
    );
};

window.CMDPEditor = CMDPEditor;

export { CMDPEditor }
