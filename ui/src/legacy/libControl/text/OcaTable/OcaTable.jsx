/**
 * Header: OcaTable.jsx
 * Purpose: OcaTable component or utility.
 * Description: Handles logic and rendering for OcaTable component or utility.
 * 
 * Version: 26.08.07.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 * - 2026-08-07: Age out the cold-start snapshot's liveness tint. A snapshot's
 *               `_row_state` was true when it was written and is asserted about
 *               now; past `config.snapshot_at + SNAPSHOT_TRUSTED_S` the rows are
 *               drawn `unknown` instead of green.
 */

// Inline comment: Logic for OcaTable
// Accepts its setup as `config` (FieldComponent path) OR `node` (WidgetFactory
// registry path — which passes node, not config; without this fallback every
// registry-dispatched table rendered empty, e.g. Sample.json's
// "Discovered Devices" example).
const OcaTable = ({ value, config, node }) => {
    config = config || node;
    const title = config?.description?.[window.useMqttLang()[0]] || config?.description?.En || "Data Table";
    const headers = config?.headers || [];
    
    // Data usually comes in as an object of objects or array of objects
    const [data, setData] = React.useState(config?.data || {});

    // Live rows over MQTT.
    //
    // A table baked into a panel file is a snapshot: it only changes when
    // something regenerates the file AND the browser is hard-refreshed. For
    // discovery tables that is the wrong shape — devices appear, vanish and
    // change state continuously, and a stale table that looks authoritative is
    // worse than an empty one.
    //
    // Subscribing here (rather than in WidgetFactory) makes it work on BOTH
    // render paths: tables declared as blocks go through the factory, which
    // does no MQTT at all, while fields come via FieldComponent, which already
    // passes `value`. An explicit `value` prop still wins, so the field path is
    // unchanged.
    //
    // `config.data` remains the cold-start snapshot: the table is populated the
    // instant the panel loads, then replaced by live rows when the first
    // retained message lands.
    // Read-only on purpose: no `nodeJson` third argument. Passing one makes
    // useMqttState publish the node as `<topic>/config` AND — when the retained
    // rows have not arrived yet — publish its own null default to `<topic>`,
    // which retained-overwrites the row payload the agents just produced. A
    // table subscribes; it never owns the topic.
    const useMqttStateHook = window.useMqttState || React.useState;
    const [liveValue] = useMqttStateHook(config?.topic, null);

    // Whether anything has replaced the cold-start snapshot yet. Only the
    // snapshot can go stale — live rows are, by definition, current.
    const [live, setLive] = React.useState(false);

    React.useEffect(() => {
        const incoming = (value !== undefined && value !== null) ? value : liveValue;
        if (incoming === undefined || incoming === null || incoming === '') return;
        try {
            const parsed = typeof incoming === 'string' ? JSON.parse(incoming) : incoming;
            setData(parsed);
            setLive(true);
        } catch(e) {
            console.error("Failed to parse table data:", e);
        }
    }, [value, liveValue]);

    const rows = Array.isArray(data) ? data : Object.values(data);

    // How long a snapshot's liveness verdict is worth anything, in seconds.
    //
    // The same window the backend classifies rows against — ONLINE_WINDOW_SECONDS
    // in BackEnd/Core/orchestrator/src/discovered.rs. A row is called `online`
    // there because it was heard from inside this window; a snapshot older than
    // the window is therefore quoting a judgement its own source would no longer
    // make.
    const SNAPSHOT_TRUSTED_S = 15 * 60;

    // Re-render once the snapshot crosses the line, so a panel left open does
    // not sit there green. Only while it still matters: no live rows have
    // arrived, and it has not aged out yet. Once either is settled the interval
    // is dropped and never runs again.
    const [, tick] = React.useReducer(n => n + 1, 0);
    const takenAt = Number(config?.snapshot_at) || 0;
    const snapshotAge = takenAt ? (Date.now() / 1000) - takenAt : Infinity;
    // No stamp at all is treated as stale rather than fresh. Panels written
    // before the stamp existed are exactly the ones most likely to be old, and
    // a table that under-claims can be corrected by a scan — one that
    // over-claims sends someone to the rack.
    const staleSnapshot = !live && snapshotAge > SNAPSHOT_TRUSTED_S;
    React.useEffect(() => {
        if (live || staleSnapshot) return;
        const id = setInterval(tick, 30000);
        return () => clearInterval(id);
    }, [live, staleSnapshot]);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#1e1e1e') : '#1e1e1e'), border: '1px solid #333', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ backgroundColor: '#2b2b2b', padding: '10px 15px', borderBottom: '1px solid #111', color: '#fff', fontSize: '12px', fontWeight: 'bold' }}>
                {title.toUpperCase()}
            </div>
            
            <div style={{ flexGrow: 1, overflow: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '11px', color: '#ccc', fontFamily: 'monospace' }}>
                    <thead style={{ backgroundColor: '#111', position: 'sticky', top: 0, zIndex: 1 }}>
                        <tr>
                            {headers.map(h => (
                                <th key={h} style={{ padding: '10px', textAlign: 'left', borderBottom: '1px solid #333', textTransform: 'capitalize' }}>
                                    {h.replace(/_/g, ' ')}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {rows.length > 0 ? rows.map((row, i) => {
                            // Optional liveness tint. A row may carry `_row_state`
                            // ('online' | 'offline' | 'unknown'); the key is hidden
                            // from `headers` so it never renders as a column.
                            // Tables without it keep the plain zebra striping.
                            //
                            // A stale snapshot's verdict is downgraded to
                            // `unknown` rather than shown or dropped. Green would
                            // be a claim about a bench nobody has looked at since
                            // the file was written; red would be just as much of
                            // a claim in the other direction; and no tint at all
                            // would hide that these rows are historical.
                            // Conditioned on the row HAVING a verdict: a table
                            // that never carried liveness (any hand-authored
                            // one) has no stamp either, and must keep its zebra
                            // striping rather than turn amber.
                            const state = (staleSnapshot && row._row_state) ? 'unknown' : row._row_state;
                            const aged = state !== row._row_state;
                            const zebra = i % 2 === 0 ? '#1a1a1a' : '#1e1e1e';
                            const TINT = {
                                online:  { bg: 'rgba(46,160,67,0.14)',  bar: '#2ea043' },
                                offline: { bg: 'rgba(248,81,73,0.13)',  bar: '#f85149' },
                                unknown: { bg: 'rgba(210,153,34,0.12)', bar: '#d29922' },
                            }[state];
                            return (
                            <tr key={i} title={!state ? undefined
                                    : aged ? `status: unknown — ${takenAt ? `snapshot is ${Math.floor(snapshotAge / 60)} min old` : 'undated snapshot'}, no live rows`
                                    : `status: ${state}`}
                                style={{ backgroundColor: TINT ? TINT.bg : zebra,
                                         boxShadow: TINT ? `inset 3px 0 0 ${TINT.bar}` : undefined }}>
                                {headers.map(h => (
                                    <td key={h} style={{ padding: '8px 10px', borderBottom: '1px solid #222' }}>
                                        {String(row[h] !== undefined ? row[h] : '')}
                                    </td>
                                ))}
                            </tr>
                            );
                        }) : (
                            <tr>
                                <td colSpan={headers.length} style={{ padding: '20px', textAlign: 'center', color: '#555' }}>
                                    No data available in table.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Footer / Toolbar */}
            <div style={{ backgroundColor: '#111', padding: '5px 15px', display: 'flex', gap: '10px', borderTop: '1px solid #333' }}>
                {config?.Add_Row && <button style={{ backgroundColor: '#333', color: '#fff', border: 'none', padding: '3px 8px', fontSize: '10px', borderRadius: '2px', cursor: 'pointer' }}>+ ADD</button>}
                {config?.Delete_Row && <button style={{ backgroundColor: '#333', color: '#fff', border: 'none', padding: '3px 8px', fontSize: '10px', borderRadius: '2px', cursor: 'pointer' }}>- DEL</button>}
                <div style={{ flexGrow: 1 }} />
                {/* Said out loud, not just tinted. The tint answers "is this row
                    alive"; this answers "should I believe this table at all",
                    which is the question a page served with no backend behind it
                    silently got wrong for twelve days. Only shown where liveness
                    was claimed — a hand-authored table has nothing to go stale. */}
                {staleSnapshot && rows.some(r => r && r._row_state) && (
                    <span style={{ fontSize: '9px', color: '#d29922' }}
                          title="No live rows have arrived on this table's topic.">
                        SNAPSHOT{takenAt ? ` · ${Math.floor(snapshotAge / 3600)}h OLD` : ' · UNDATED'} · NOT LIVE
                    </span>
                )}
                <span style={{ fontSize: '9px', color: '#444' }}>{rows.length} ROWS</span>
            </div>
        </div>
    );
};

window.OcaTable = OcaTable;