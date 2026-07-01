const parseSplitName = (name) => {
    const match = name.match(/^(left|right|top|bottom)_(\d+)$/i);
    if (match) return { direction: match[1].toLowerCase(), percent: parseInt(match[2], 10) };
    return null;
};

const WindowLayout = ({ node, path = '' }) => {
    if (!node || !node.children) return null;

    // Check if children are splits
    const splits = node.children.filter(c => parseSplitName(c.name));
    if (splits.length > 0) {
        const isRow = splits.some(s => {
            const parsed = parseSplitName(s.name);
            return parsed && (parsed.direction === 'left' || parsed.direction === 'right');
        });
        
        // Sort to ensure left/top comes before right/bottom
        const sortedSplits = [...splits].sort((a, b) => {
            const pA = parseSplitName(a.name);
            const pB = parseSplitName(b.name);
            if (!pA || !pB) return 0;
            if (pA.direction === 'left' || pA.direction === 'top') return -1;
            if (pA.direction === 'right' || pA.direction === 'bottom') return 1;
            return 0;
        });

        return (
            <div style={{ display: 'flex', flexDirection: isRow ? 'row' : 'column', width: '100%', height: '100%' }}>
                {sortedSplits.map(split => {
                    const parsed = parseSplitName(split.name);
                    return (
                        <div key={split.name} style={{ 
                            flexBasis: `${parsed.percent}%`, 
                            flexGrow: parsed.percent, 
                            flexShrink: 1, 
                            overflow: 'hidden', 
                            borderRight: isRow ? '1px solid #333' : 'none', 
                            borderBottom: !isRow ? '1px solid #333' : 'none'
                        }}>
                            <WindowLayout node={split} path={`${path}/${split.name}`} />
                        </div>
                    );
                })}
            </div>
        );
    }

    // If no splits, it's a Tab container!
    return <TabContainer node={node} path={path} />;
};

const TabContainer = ({ node, path = '' }) => {
    let dirs = node.children.filter(c => c.type === 'directory');
    dirs = [...dirs].sort((a, b) => {
        const matchA = a.name.match(/^(\d+)_/);
        const matchB = b.name.match(/^(\d+)_/);
        const numA = matchA ? parseInt(matchA[1], 10) : Infinity;
        const numB = matchB ? parseInt(matchB[1], 10) : Infinity;
        if (numA !== numB) return numA - numB;
        return a.name.localeCompare(b.name);
    });
    
    let files = node.children.filter(c => c.type === 'file' && c.name.endsWith('.json'));
    files = [...files].sort((a, b) => {
        const matchA = a.name.match(/^(\d+)_/);
        const matchB = b.name.match(/^(\d+)_/);
        const numA = matchA ? parseInt(matchA[1], 10) : Infinity;
        const numB = matchB ? parseInt(matchB[1], 10) : Infinity;
        if (numA !== numB) return numA - numB;
        return a.name.localeCompare(b.name);
    });

    // Restore this pane's active tab from the URL hash (keyed by its node path),
    // so a refresh returns to the same tab in every pane.
    const [activeTab, setActiveTab] = React.useState(() => {
        const saved = window.OaNav && window.OaNav.get(path);
        return (saved && dirs.find(d => d.name === saved)) ? saved
            : (dirs.length > 0 ? dirs[0].name : null);
    });
    const selectTab = (name) => { setActiveTab(name); window.OaNav && window.OaNav.set(path, name); };

    // If new dirs loaded, reset active tab if current is invalid
    React.useEffect(() => {
        if (dirs.length > 0 && !dirs.find(d => d.name === activeTab)) {
            setActiveTab(dirs[0].name);
        }
    }, [node, dirs, activeTab]);

    if (dirs.length === 0 && files.length > 0) {
        return (
            <div style={{ 
                width: '100%', 
                height: '100%', 
                overflow: 'auto', 
                backgroundColor: '#1a1a1a', 
                display: 'flex', 
                flexDirection: 'column' 
            }}>
                 {files.map(f => (
                     <div key={f.name}
                        onContextMenu={(e) => { e.preventDefault(); window.launchWysiwygEditor && window.launchWysiwygEditor({ filePath: f.path, content: f.content }); }}
                        title="Right-click: Open WYSIWYG editor"
                        style={{ flexGrow: 1, flexBasis: '0', minHeight: '300px', borderBottom: '1px solid #333' }}>
                        <window.LoaderOrchestrator layoutJson={f.content} filePath={f.path} />
                     </div>
                 ))}
            </div>
        );
    }

    if (dirs.length === 0) {
        return <div style={{color:'#888', padding: '10px', height: '100%', backgroundColor: '#1a1a1a'}}></div>;
    }

    const activeNode = dirs.find(d => d.name === activeTab);

    // Clean up names like "0_Spectrum" -> "Spectrum"
    const cleanName = (name) => name.replace(/^\d+_/, '').replace(/_/g, ' ');

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
            <div style={{ display: 'flex', backgroundColor: '#0a0a0a', overflowX: 'auto', flexShrink: 0, borderBottom: '1px solid #222' }}>
                {dirs.map(d => (
                    <div
                        key={d.name}
                        onClick={() => selectTab(d.name)}
                        style={{
                            padding: '8px 16px',
                            cursor: 'pointer',
                            backgroundColor: activeTab === d.name ? '#1e1e1e' : 'transparent',
                            color: activeTab === d.name ? '#f4902c' : '#aaa', // Open-Air Orange highlight
                            borderBottom: activeTab === d.name ? '2px solid #f4902c' : '2px solid transparent',
                            fontWeight: activeTab === d.name ? 'bold' : 'normal',
                            whiteSpace: 'nowrap',
                            fontSize: '14px',
                            fontFamily: 'Segoe UI, sans-serif',
                            transition: 'all 0.1s'
                        }}
                    >
                        {cleanName(d.name)}
                    </div>
                ))}
            </div>
            <div style={{ flexGrow: 1, overflow: 'hidden' }}>
                {activeNode && <WindowLayout node={activeNode} path={`${path}/${activeNode.name}`} />}
            </div>
        </div>
    );
};

const WindowManager = ({ directoryTree }) => {
    const [lang, setLang] = window.useMqttLang();
    const { connected: mqttConnected, fullId: mqttFullId } = (window.useMqttStatus ? window.useMqttStatus() : { connected: false, fullId: '' });

    // WYSIWYG editor open-state. Panels dispatch 'oa-open-wysiwyg' (see Entry.jsx)
    // on right-click; we render the editor overlay inside this tree so it shares
    // the MqttProvider context and the live renderer.
    const [editor, setEditor] = React.useState(null);
    React.useEffect(() => {
        const onOpen = (e) => setEditor(e.detail || null);
        window.addEventListener('oa-open-wysiwyg', onOpen);
        return () => window.removeEventListener('oa-open-wysiwyg', onOpen);
    }, []);

    if (!directoryTree || !directoryTree.children) return <div style={{color: '#fff'}}>Loading Tree...</div>;

    // The root usually contains "Window_1", "Window_2"
    const windows = directoryTree.children.filter(c => c.type === 'directory' && c.name.toLowerCase().includes('window'));

    // Restore the active window from the URL hash (so refresh returns here).
    const [activeWindow, setActiveWindow] = React.useState(() => {
        const saved = window.OaNav && window.OaNav.get('__win');
        return (saved && windows.find(w => w.name === saved)) ? saved
            : (windows.length > 0 ? windows[0].name : null);
    });
    const selectWindow = (name) => { setActiveWindow(name); window.OaNav && window.OaNav.set('__win', name); };

    const activeWindowNode = windows.find(w => w.name === activeWindow) || directoryTree;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', backgroundColor: '#000', color: '#fff' }}>
            
            {/* Master Window Bar */}
            <div style={{ display: 'flex', backgroundColor: '#111', borderBottom: '1px solid #333', alignItems: 'center', padding: '0 10px', height: '35px', flexShrink: 0 }}>
                <span style={{ color: '#fff', fontWeight: 'bold', marginRight: '20px', letterSpacing: '1px', fontSize: '12px' }}>OPEN-AIR</span>
                {windows.map(w => (
                    <div
                        key={w.name}
                        onClick={() => selectWindow(w.name)}
                        style={{
                            padding: '0 20px',
                            height: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            cursor: 'pointer',
                            color: activeWindow === w.name ? '#fff' : '#666',
                            borderBottom: activeWindow === w.name ? '2px solid #fff' : '2px solid transparent',
                            textTransform: 'uppercase',
                            fontSize: '11px',
                            fontWeight: 'bold',
                            backgroundColor: activeWindow === w.name ? '#222' : 'transparent'
                        }}
                    >
                        {w.name.replace(/_/g, ' ')}
                    </div>
                ))}
                
                <div style={{ flexGrow: 1 }} />

                {/* Language Selector */}
                <div style={{ marginRight: '20px', display: 'flex', alignItems: 'center' }}>
                    <span style={{ fontSize: '10px', color: '#666', marginRight: '8px', fontWeight: 'bold' }}>LANG:</span>
                    <select 
                        value={lang} 
                        onChange={(e) => setLang(e.target.value)}
                        style={{
                            backgroundColor: '#000',
                            color: '#0f0',
                            border: '1px solid #333',
                            fontSize: '10px',
                            padding: '2px 5px',
                            borderRadius: '3px',
                            outline: 'none',
                            cursor: 'pointer',
                            fontFamily: 'monospace',
                            fontWeight: 'bold'
                        }}
                    >
                        <option value="En">ENGLISH</option>
                        <option value="Fr">FRANÇAIS</option>
                        <option value="De">DEUTSCH</option>
                        <option value="Es">ESPAÑOL</option>
                    </select>
                </div>

                {/* Session identity + live MQTT connection state */}
                <div
                    title={`Browser session full_id: ${mqttFullId || 'unavailable'}\nClick to copy`}
                    onClick={() => {
                        if (mqttFullId && navigator.clipboard) {
                            navigator.clipboard.writeText(mqttFullId).catch(() => {});
                        }
                    }}
                    style={{
                        fontSize: '10px',
                        color: '#888',
                        fontFamily: 'monospace',
                        marginRight: '12px',
                        cursor: 'pointer',
                        userSelect: 'none',
                    }}
                >
                    ID: {mqttFullId ? mqttFullId.split(':')[0] + ':' + (mqttFullId.split(':')[1] || '') : '—'}
                </div>
                <div 
                    onClick={() => {
                        const current = new URLSearchParams(window.location.search).get('mqtt') || '44.44.44.152';
                        const override = window.prompt("Enter MQTT Broker IP or Hostname to connect to:", current);
                        if (override && override.trim() !== "" && override !== current) {
                            const url = new URL(window.location.href);
                            url.searchParams.set('mqtt', override.trim());
                            window.location.href = url.toString();
                        }
                    }}
                    title="Click to configure MQTT Server IP"
                    style={{
                        fontSize: '10px',
                        color: mqttConnected ? '#0f0' : '#f55',
                        fontWeight: 'bold',
                        letterSpacing: '1px',
                        cursor: 'pointer',
                        padding: '2px 5px',
                        borderRadius: '3px',
                        border: '1px solid #333',
                        backgroundColor: '#000'
                    }}
                >
                    {mqttConnected ? 'MQTT ACTIVE' : 'MQTT OFFLINE'}
                </div>
            </div>

            {/* Window Content */}
            <div style={{ flexGrow: 1, overflow: 'hidden' }}>
                <WindowLayout node={activeWindowNode} path={activeWindow || ''} />
            </div>

            {/* WYSIWYG editor overlay */}
            {editor && window.WysiwygEditor && (
                <window.WysiwygEditor
                    filePath={editor.filePath}
                    content={editor.content}
                    onClose={() => setEditor(null)}
                />
            )}
        </div>
    );
};

window.WindowManager = WindowManager;