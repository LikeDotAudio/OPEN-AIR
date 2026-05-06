const parseSplitName = (name) => {
    const match = name.match(/^(left|right|top|bottom)_(\d+)$/i);
    if (match) return { direction: match[1].toLowerCase(), percent: parseInt(match[2], 10) };
    return null;
};

const WindowLayout = ({ node }) => {
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
                            <WindowLayout node={split} />
                        </div>
                    );
                })}
            </div>
        );
    }
    
    // If no splits, it's a Tab container!
    return <TabContainer node={node} />;
};

const TabContainer = ({ node }) => {
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

    const [activeTab, setActiveTab] = React.useState(dirs.length > 0 ? dirs[0].name : null);

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
                     <div key={f.name} style={{ flexGrow: 1, flexBasis: '0', minHeight: '300px', borderBottom: '1px solid #333' }}>
                        <window.LoaderOrchestrator layoutJson={f.content} />
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
                        onClick={() => setActiveTab(d.name)}
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
                {activeNode && <WindowLayout node={activeNode} />}
            </div>
        </div>
    );
};

const WindowManager = ({ directoryTree }) => {
    const [lang, setLang] = window.useMqttLang();
    
    if (!directoryTree || !directoryTree.children) return <div style={{color: '#fff'}}>Loading Tree...</div>;

    // The root usually contains "Window_1", "Window_2"
    const windows = directoryTree.children.filter(c => c.type === 'directory' && c.name.toLowerCase().includes('window'));
    
    const [activeWindow, setActiveWindow] = React.useState(windows.length > 0 ? windows[0].name : null);

    const activeWindowNode = windows.find(w => w.name === activeWindow) || directoryTree;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', backgroundColor: '#000', color: '#fff' }}>
            
            {/* Master Window Bar */}
            <div style={{ display: 'flex', backgroundColor: '#111', borderBottom: '1px solid #333', alignItems: 'center', padding: '0 10px', height: '35px', flexShrink: 0 }}>
                <span style={{ color: '#fff', fontWeight: 'bold', marginRight: '20px', letterSpacing: '1px', fontSize: '12px' }}>OPEN-AIR</span>
                {windows.map(w => (
                    <div 
                        key={w.name}
                        onClick={() => setActiveWindow(w.name)}
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

                <div style={{ fontSize: '10px', color: '#0f0', fontWeight: 'bold', letterSpacing: '1px' }}>MQTT ACTIVE</div>
            </div>

            {/* Window Content */}
            <div style={{ flexGrow: 1, overflow: 'hidden' }}>
                <WindowLayout node={activeWindowNode} />
            </div>
        </div>
    );
};

window.WindowManager = WindowManager;