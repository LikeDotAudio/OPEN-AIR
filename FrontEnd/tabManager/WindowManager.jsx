/**
 * Header: WindowManager.jsx
 * Purpose: WindowManager component or utility.
 * Description: Handles logic and rendering for WindowManager component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// Inline comment: Logic for parseSplitName
const parseSplitName = (name) => {
    const match = name.match(/^(left|right|top|bottom)_(\d+)$/i);
    if (match) return { direction: match[1].toLowerCase(), percent: parseInt(match[2], 10) };
    return null;
};

// Inline comment: Logic for MqttLazyPublisher
const MqttLazyPublisher = ({ directoryTree }) => {
    const publish = window.useMqttPublish ? window.useMqttPublish() : null;
    const { connected } = window.useMqttStatus ? window.useMqttStatus() : { connected: false };

    React.useEffect(() => {
        if (!connected || !directoryTree || !publish) return;

        // Gather all topics and configs from the entire directoryTree
        const queue = [];
        const crawl = (node) => {
            if (node.type === 'file' && node.content) {
                Object.values(node.content).forEach(comp => {
                    if (comp && comp.behavior && comp.behavior.topic) {
                        const topic = comp.behavior.topic;
                        const defaultValue = comp.behavior.default_value;
                        const config = comp;
                        queue.push({ topic, defaultValue, config });
                    }
                });
            } else if (node.children) {
                node.children.forEach(crawl);
            }
        };
        crawl(directoryTree);

        let currentIndex = 0;
        let idleCallbackId = null;

        const processQueue = (deadline) => {
            while (currentIndex < queue.length && (deadline.timeRemaining() > 2 || deadline.didTimeout)) {
                const item = queue[currentIndex];
                publish(`${item.topic}/config`, JSON.stringify(item.config));
                if (window.OA_MQTT_LAST && window.OA_MQTT_LAST[item.topic] === undefined) {
                    publish(item.topic, JSON.stringify({ value: item.defaultValue, full_id: window.OA_SESSION_FULL_ID || 'WEB_IDLE' }));
                }
                currentIndex++;
            }
            if (currentIndex < queue.length) {
                if (window.requestIdleCallback) {
                    idleCallbackId = window.requestIdleCallback(processQueue, { timeout: 1000 });
                } else {
                    idleCallbackId = setTimeout(() => processQueue({ timeRemaining: () => 10, didTimeout: false }), 100);
                }
            }
        };

        if (window.requestIdleCallback) {
            idleCallbackId = window.requestIdleCallback(processQueue, { timeout: 2000 });
        } else {
            idleCallbackId = setTimeout(() => processQueue({ timeRemaining: () => 10, didTimeout: false }), 1000);
        }

        return () => {
            if (window.cancelIdleCallback && idleCallbackId) window.cancelIdleCallback(idleCallbackId);
            else clearTimeout(idleCallbackId);
        };
    }, [connected, directoryTree, publish]);

    return null;
};

// Inline comment: Logic for ResizableSplit
const ResizableSplit = ({ splits, isRow, path }) => {
    const splitA = splits[0];
    const splitB = splits[1];
    const parsedA = parseSplitName(splitA.name);

    const [percentA, setPercentA] = React.useState(parsedA ? parsedA.percent : 50);
    const [savedPercent, setSavedPercent] = React.useState(parsedA ? parsedA.percent : 50);
    const containerRef = React.useRef(null);
    const isDragging = React.useRef(false);

    const onMouseDown = (e) => {
        isDragging.current = true;
        document.body.style.cursor = isRow ? 'col-resize' : 'row-resize';
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        e.preventDefault();
    };

    const onMouseMove = (e) => {
        if (!isDragging.current || !containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        
        let newPercent = 0;
        if (isRow) {
            const x = e.clientX - rect.left;
            newPercent = (x / rect.width) * 100;
        } else {
            const y = e.clientY - rect.top;
            newPercent = (y / rect.height) * 100;
        }
        
        newPercent = Math.max(0, Math.min(100, newPercent));
        setPercentA(newPercent);
        if (newPercent > 5 && newPercent < 95) {
            setSavedPercent(newPercent);
        }
    };

    const onMouseUp = () => {
        isDragging.current = false;
        document.body.style.cursor = '';
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    };

    const toggleLeft = () => {
        if (percentA === 0) {
            setPercentA(savedPercent);
        } else {
            if (percentA > 5 && percentA < 95) setSavedPercent(percentA);
            setPercentA(0);
        }
    };

    const toggleRight = () => {
        if (percentA === 100) {
            setPercentA(savedPercent);
        } else {
            if (percentA > 5 && percentA < 95) setSavedPercent(percentA);
            setPercentA(100);
        }
    };
    
    const restoreCenter = () => {
        setPercentA(50);
        setSavedPercent(50);
    };

    const lastNonCenter = React.useRef(0);
    const cycleSplit = () => {
        if (percentA > 5 && percentA < 95) {
            const nextTarget = lastNonCenter.current === 0 ? 100 : 0;
            setPercentA(nextTarget);
            lastNonCenter.current = nextTarget;
        } else {
            if (percentA === 0) lastNonCenter.current = 0;
            if (percentA === 100) lastNonCenter.current = 100;
            setPercentA(50);
            setSavedPercent(50);
        }
    };

    React.useEffect(() => {
        if (!path.includes('/')) {
            window.dispatchEvent(new CustomEvent('oa-split-state', { detail: { path, percent: percentA } }));
        }
    }, [percentA, path]);

    React.useEffect(() => {
        const handleGlobalToggle = (e) => {
            // Only respond if this is the top-level split for the window
            if (!path.includes('/')) {
                if (e.detail === 'left') toggleLeft();
                if (e.detail === 'right') toggleRight();
                if (e.detail === 'center') restoreCenter();
                if (e.detail === 'cycle') cycleSplit();
            }
        };
        window.addEventListener('oa-global-split-toggle', handleGlobalToggle);
        return () => window.removeEventListener('oa-global-split-toggle', handleGlobalToggle);
    }, [percentA, savedPercent, path]);

    return (
        <div ref={containerRef} style={{ display: 'flex', flexDirection: isRow ? 'row' : 'column', width: '100%', height: '100%' }}>
            <div style={{ flexBasis: `${percentA}%`, flexGrow: 0, flexShrink: 0, overflow: 'hidden', minWidth: 0, minHeight: 0, display: percentA === 0 ? 'none' : 'block' }}>
                <WindowLayout node={splitA} path={`${path}/${splitA.name}`} />
            </div>
            
            <div 
                style={{
                    display: 'flex',
                    flexDirection: isRow ? 'column' : 'row',
                    alignItems: 'center',
                    justifyContent: 'center',
                    [isRow ? 'width' : 'height']: '8px',
                    backgroundColor: '#1a1a1a',
                    zIndex: 10,
                    position: 'relative',
                    transition: 'background-color 0.2s',
                    userSelect: 'none',
                    borderLeft: isRow ? '1px solid #333' : 'none',
                    borderRight: isRow ? '1px solid #333' : 'none',
                    borderTop: !isRow ? '1px solid #333' : 'none',
                    borderBottom: !isRow ? '1px solid #333' : 'none',
                }}
                onMouseEnter={e => e.currentTarget.style.backgroundColor = '#2a2a2a'}
                onMouseLeave={e => e.currentTarget.style.backgroundColor = '#1a1a1a'}
            >
                <div 
                    onMouseDown={onMouseDown}
                    style={{
                        position: 'absolute',
                        top: 0, left: 0, right: 0, bottom: 0,
                        cursor: isRow ? 'col-resize' : 'row-resize',
                    }}
                />
            </div>

            <div style={{ flexGrow: 1, flexShrink: 1, overflow: 'hidden', minWidth: 0, minHeight: 0, display: percentA === 100 ? 'none' : 'block' }}>
                <WindowLayout node={splitB} path={`${path}/${splitB.name}`} />
            </div>
        </div>
    );
};

// Inline comment: Logic for WindowLayout
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

        if (sortedSplits.length === 2) {
            return <ResizableSplit splits={sortedSplits} isRow={isRow} path={path} />;
        }

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

// Inline comment: Logic for TabContainer
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
                {dirs.map(d => {
                    const fullPath = path ? `${path}/${d.name}` : d.name;
                    const tabUrl = window.OaNav && window.OaNav.buildIsolatedUrl ? window.OaNav.buildIsolatedUrl(fullPath) : '#';
                    return (
                    <a
                        key={d.name}
                        href={tabUrl}
                        onClick={(e) => {
                            if (e.ctrlKey || e.metaKey || e.button === 1) return;
                            e.preventDefault();
                            selectTab(d.name);
                        }}
                        style={{
                            display: 'block',
                            textDecoration: 'none',
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
                    </a>
                    );
                })}
            </div>
            <div style={{ flexGrow: 1, overflow: 'hidden' }}>
                {activeNode && <WindowLayout node={activeNode} path={`${path}/${activeNode.name}`} />}
            </div>
        </div>
    );
};

// Inline comment: Logic for HeaderControlButton
const HeaderControlButton = ({ label, color, onClick }) => {
    return (
        <button
            onClick={onClick}
            style={{
                backgroundColor: '#111',
                color: color,
                border: `1px solid ${color}`,
                boxShadow: `0 0 8px ${color}`,
                borderRadius: '4px',
                padding: '4px 16px',
                margin: '0 5px',
                cursor: 'pointer',
                fontFamily: 'Segoe UI, sans-serif',
                fontWeight: 'bold',
                fontSize: '11px',
                textTransform: 'uppercase',
                transition: 'all 0.1s'
            }}
        >
            {label}
        </button>
    );
};

// Inline comment: Logic for HeaderControls
const HeaderControls = () => {
    if (!window.useMqttState) return null;
    
    const [isRunning, setIsRunning] = window.useMqttState('System/Control/Start', false);

    return (
        <div style={{ display: 'flex', marginLeft: 'auto', marginRight: '10px', alignItems: 'center' }}>
            <HeaderControlButton 
                label={isRunning ? "Stop" : "Start"} 
                color={isRunning ? "#ff0000" : "#00ff00"} 
                onClick={() => setIsRunning(!isRunning)} 
            />
        </div>
    );
};

// Inline comment: Logic for WindowManager
const WindowManager = ({ directoryTree }) => {
    const [lang, setLang] = window.useMqttLang();
    const { connected: mqttConnected, fullId: mqttFullId } = (window.useMqttStatus ? window.useMqttStatus() : { connected: false, fullId: '' });

    const [splitStates, setSplitStates] = React.useState({});
    React.useEffect(() => {
        const handler = (e) => setSplitStates(prev => ({ ...prev, [e.detail.path]: e.detail.percent }));
        window.addEventListener('oa-split-state', handler);
        return () => window.removeEventListener('oa-split-state', handler);
    }, []);

    // WYSIWYG editor open-state. Panels dispatch 'oa-open-wysiwyg' (see Entry.jsx)
    // on right-click; we render the editor overlay inside this tree so it shares
    // the MqttProvider context and the live renderer.
    const [editor, setEditor] = React.useState(null);
    React.useEffect(() => {
        const onOpen = (e) => setEditor(e.detail || null);
        window.addEventListener('oa-open-wysiwyg', onOpen);
        
        // Auto-open editor if specified in URL
        const urlParams = new URLSearchParams(window.location.search);
        const editorPath = urlParams.get('editor');
        if (editorPath) {
            if (editorPath === 'true') {
                setEditor({ filePath: null, content: {} });
            } else {
                // Find file in directoryTree
                const findFile = (node, path) => {
                    if (node.type === 'file' && node.path === path) return node;
                    if (node.children) {
                        for (let child of node.children) {
                            const found = findFile(child, path);
                            if (found) return found;
                        }
                    }
                    return null;
                };
                const fileNode = findFile(directoryTree, editorPath);
                if (fileNode) {
                    setEditor({ filePath: fileNode.path, content: fileNode.content });
                }
            }
        }
        
        return () => window.removeEventListener('oa-open-wysiwyg', onOpen);
    }, [directoryTree]);

    if (!directoryTree || !directoryTree.children) return <div style={{color: '#fff'}}>Loading Tree...</div>;

    // The root contains the top-level GUI folders
    const windows = directoryTree.children.filter(c => c.type === 'directory');

    // Restore the active window from the URL hash (so refresh returns here).
    const [activeWindow, setActiveWindow] = React.useState(() => {
        const saved = window.OaNav && window.OaNav.get('__win');
        return (saved && windows.find(w => w.name === saved)) ? saved
            : (windows.length > 0 ? windows[0].name : null);
    });
    const selectWindow = (name) => { setActiveWindow(name); window.OaNav && window.OaNav.set('__win', name); };

    const activeWindowNode = windows.find(w => w.name === activeWindow) || directoryTree;

    const urlParams = new URLSearchParams(window.location.search);
    const isolatePath = urlParams.get('isolate');

    let isolatedNode = null;
    if (isolatePath && directoryTree) {
        let curr = directoryTree;
        const parts = isolatePath.split('/').filter(Boolean);
        for (let p of parts) {
            curr = curr.children?.find(c => c.name === p);
            if (!curr) break;
        }
        isolatedNode = curr;
    }

    if (isolatedNode) {
        return (
            <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', backgroundColor: '#000', color: '#fff' }}>
                <div style={{ flexGrow: 1, overflow: 'hidden' }}>
                    <WindowLayout node={isolatedNode} path={isolatePath} />
                </div>
                {editor && window.WysiwygEditor && (
                    <window.WysiwygEditor
                        filePath={editor.filePath}
                        content={editor.content}
                        onClose={() => setEditor(null)}
                    />
                )}
            </div>
        );
    }

    const [showSettings, setShowSettings] = React.useState(false);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', backgroundColor: '#000', color: '#fff' }}>
            
            {/* Master Window Bar */}
            <div style={{ display: 'flex', backgroundColor: '#111', borderBottom: '1px solid #333', alignItems: 'center', padding: '0 10px', height: '35px', flexShrink: 0 }}>
                <div style={{ position: 'relative', marginRight: '20px' }}>
                    <span 
                        onClick={() => setShowSettings(!showSettings)}
                        style={{ 
                            color: mqttConnected ? '#0f0' : '#f55', 
                            fontWeight: 'bold', 
                            letterSpacing: '1px', 
                            fontSize: '12px',
                            cursor: 'pointer',
                            userSelect: 'none'
                        }}
                        title={mqttConnected ? "MQTT ONLINE - Click for Settings" : "MQTT OFFLINE - Click for Settings"}
                    >
                        OPEN-AIR
                    </span>
                    {showSettings && (
                        <div style={{
                            position: 'absolute',
                            top: '100%',
                            left: '0',
                            marginTop: '10px',
                            backgroundColor: '#111',
                            border: '1px solid #333',
                            borderRadius: '4px',
                            padding: '10px',
                            zIndex: 100,
                            boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '12px',
                            minWidth: '200px'
                        }}>
                             <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                 <span style={{ fontSize: '10px', color: '#666', fontWeight: 'bold' }}>LANG:</span>
                                 <select 
                                     value={lang} 
                                     onChange={(e) => setLang(e.target.value)}
                                     style={{
                                         backgroundColor: '#000', color: '#0f0', border: '1px solid #333',
                                         fontSize: '10px', padding: '2px 5px', borderRadius: '3px',
                                         outline: 'none', cursor: 'pointer', fontFamily: 'monospace', fontWeight: 'bold'
                                     }}
                                 >
                                     <option value="En">ENGLISH</option>
                                     <option value="Fr">FRANÇAIS</option>
                                     <option value="De">DEUTSCH</option>
                                     <option value="Es">ESPAÑOL</option>
                                 </select>
                             </div>
                             
                             <div 
                                 title={`Browser session full_id: ${mqttFullId || 'unavailable'}\nClick to copy`}
                                 onClick={() => {
                                     if (mqttFullId && navigator.clipboard) {
                                         navigator.clipboard.writeText(mqttFullId).catch(() => {});
                                     }
                                 }}
                                 style={{ fontSize: '10px', color: '#888', fontFamily: 'monospace', cursor: 'pointer', userSelect: 'none' }}
                             >
                                 ID: {mqttFullId ? mqttFullId.split(':')[0] + ':' + (mqttFullId.split(':')[1] || '') : '—'}
                             </div>

                             <div 
                                 onClick={() => {
                                     const current = new URLSearchParams(window.location.search).get('mqtt') || window.location.hostname || 'localhost';
                                     const override = window.prompt("Enter MQTT Broker IP or Hostname to connect to:", current);
                                     if (override && override.trim() !== "" && override !== current) {
                                         const url = new URL(window.location.href);
                                         url.searchParams.set('mqtt', override.trim());
                                         window.location.href = url.toString();
                                     }
                                 }}
                                 title="Click to configure MQTT Server IP"
                                 style={{
                                     fontSize: '10px', color: mqttConnected ? '#0f0' : '#f55', fontWeight: 'bold',
                                     letterSpacing: '1px', cursor: 'pointer', padding: '4px 5px',
                                     borderRadius: '3px', border: '1px solid #333', backgroundColor: '#000',
                                     textAlign: 'center'
                                 }}
                             >
                                 {mqttConnected ? 'MQTT ACTIVE' : 'MQTT OFFLINE'}
                             </div>
                             
                             <button
                                 onClick={() => {
                                     if ('serviceWorker' in navigator) {
                                         navigator.serviceWorker.getRegistrations().then(function(registrations) {
                                             for(let registration of registrations) {
                                                 registration.unregister();
                                             }
                                             window.location.reload(true);
                                         });
                                     } else {
                                         window.location.reload(true);
                                     }
                                 }}
                                 style={{
                                     fontSize: '10px', color: '#fff', fontWeight: 'bold',
                                     letterSpacing: '1px', cursor: 'pointer', padding: '6px 5px',
                                     borderRadius: '3px', border: '1px solid #555', backgroundColor: '#d33',
                                     textAlign: 'center', marginTop: '2px'
                                 }}
                             >
                                 FLUSH CACHE & RELOAD
                             </button>
                        </div>
                    )}
                </div>
                {windows.map(w => {
                    const winUrl = window.OaNav && window.OaNav.buildIsolatedUrl ? window.OaNav.buildIsolatedUrl(w.name) : '#';
                    return (
                    <a
                        key={w.name}
                        href={winUrl}
                        onClick={(e) => {
                            if (e.ctrlKey || e.metaKey || e.button === 1) return;
                            e.preventDefault();
                            if (activeWindow === w.name) {
                                window.dispatchEvent(new CustomEvent('oa-global-split-toggle', { detail: 'cycle' }));
                            } else {
                                selectWindow(w.name);
                            }
                        }}
                        style={{
                            padding: '0 20px',
                            height: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            cursor: 'pointer',
                            textDecoration: 'none',
                            color: activeWindow === w.name ? '#fff' : '#666',
                            borderBottom: activeWindow === w.name ? '2px solid #fff' : '2px solid transparent',
                            textTransform: 'uppercase',
                            fontSize: '11px',
                            fontWeight: 'bold',
                            backgroundColor: activeWindow === w.name ? '#222' : 'transparent'
                        }}
                        title={activeWindow === w.name ? "Click to cycle split layout" : ""}
                    >
                        {(() => {
                            let label = w.name.replace(/^\\d+[_-]?/, '').replace(/_/g, ' ');
                            if (activeWindow === w.name) {
                                const p = splitStates[w.name];
                                const leftArrow = p === 0 ? '' : '◀\u00A0\u00A0';
                                const rightArrow = p === 100 ? '' : '\u00A0\u00A0▶';
                                label = `${leftArrow}${label}${rightArrow}`;
                            }
                            return label;
                        })()}
                    </a>
                    );
                })}
                
                <HeaderControls />

                <div style={{ flexGrow: 1 }} />
            </div>

            {/* Window Content */}
            <div style={{ flexGrow: 1, overflow: 'hidden' }}>
                <WindowLayout node={activeWindowNode} path={activeWindow || ''} />
            </div>

            {/* Background Lazy Publisher */}
            <MqttLazyPublisher directoryTree={directoryTree} />

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