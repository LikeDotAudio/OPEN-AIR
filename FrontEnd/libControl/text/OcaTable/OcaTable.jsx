/**
 * Header: OcaTable.jsx
 * Purpose: OcaTable component or utility.
 * Description: Handles logic and rendering for OcaTable component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for OcaTable
const OcaTable = ({ value, config }) => {
    const title = config?.description?.[window.useMqttLang()[0]] || config?.description?.En || "Data Table";
    const headers = config?.headers || [];
    
    // Data usually comes in as an object of objects or array of objects
    const [data, setData] = React.useState(config?.data || {});

    React.useEffect(() => {
        if (value) {
            try {
                const parsed = typeof value === 'string' ? JSON.parse(value) : value;
                setData(parsed);
            } catch(e) {
                console.error("Failed to parse table data:", e);
            }
        }
    }, [value]);

    const rows = Array.isArray(data) ? data : Object.values(data);

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
                        {rows.length > 0 ? rows.map((row, i) => (
                            <tr key={i} style={{ backgroundColor: i % 2 === 0 ? '#1a1a1a' : '#1e1e1e' }}>
                                {headers.map(h => (
                                    <td key={h} style={{ padding: '8px 10px', borderBottom: '1px solid #222' }}>
                                        {String(row[h] !== undefined ? row[h] : '')}
                                    </td>
                                ))}
                            </tr>
                        )) : (
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
                <span style={{ fontSize: '9px', color: '#444' }}>{rows.length} ROWS</span>
            </div>
        </div>
    );
};

window.OcaTable = OcaTable;