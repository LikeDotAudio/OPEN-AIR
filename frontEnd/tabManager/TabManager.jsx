const TabManager = ({ directoryTree }) => {
    // Current path is a list of node names forming the path to the currently viewed element
    const [path, setPath] = React.useState([]);

    if (!directoryTree) return <div style={{color: '#fff'}}>Loading Tree...</div>;

    // Traverse the tree to find current level contents
    let currentNode = directoryTree;
    for (let p of path) {
        const found = currentNode.children?.find(c => c.name === p);
        if (found) {
            currentNode = found;
        }
    }

    // Determine what to display inside the current node
    const directories = currentNode.children?.filter(c => c.type === 'directory') || [];
    const files = currentNode.children?.filter(c => c.type === 'file' && c.name.endsWith('.json')) || [];

    // If this node has a JSON file layout in it, maybe render it
    // Usually directories contain folders which act as tabs
    const layoutFilesToRender = path.length > 0 && files.length > 0 ? files : [];

    const handleTabClick = (dirName) => {
        setPath([...path, dirName]);
    };

    const handleBreadcrumbClick = (index) => {
        setPath(path.slice(0, index + 1));
    };

    const goHome = () => setPath([]);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', backgroundColor: '#000', color: '#fff', fontFamily: 'sans-serif' }}>
            
            {/* Top Navigation Bar */}
            <div style={{ display: 'flex', alignItems: 'center', padding: '10px 20px', backgroundColor: '#222', borderBottom: '1px solid #444' }}>
                <span onClick={goHome} style={{ cursor: 'pointer', fontWeight: 'bold', color: '#00bcd4', marginRight: '10px' }}>
                    Gui_Frames Home
                </span>
                {path.map((p, i) => (
                    <span key={i} style={{ display: 'flex', alignItems: 'center' }}>
                        <span style={{ margin: '0 10px', color: '#666' }}>/</span>
                        <span 
                            onClick={() => handleBreadcrumbClick(i)} 
                            style={{ cursor: 'pointer', color: i === path.length - 1 ? '#fff' : '#00bcd4' }}
                        >
                            {p}
                        </span>
                    </span>
                ))}
            </div>

            {/* Tab Bar (Sub-directories acting as tabs) */}
            {directories.length > 0 && (
                <div style={{ display: 'flex', backgroundColor: '#111', borderBottom: '1px solid #333', overflowX: 'auto', flexShrink: 0 }}>
                    {directories.map(dir => (
                        <div 
                            key={dir.name}
                            onClick={() => handleTabClick(dir.name)}
                            style={{
                                padding: '12px 24px',
                                cursor: 'pointer',
                                borderRight: '1px solid #333',
                                whiteSpace: 'nowrap',
                                backgroundColor: '#1e1e1e'
                            }}
                            onMouseEnter={e => e.currentTarget.style.backgroundColor = '#333'}
                            onMouseLeave={e => e.currentTarget.style.backgroundColor = '#1e1e1e'}
                        >
                            {dir.name}
                        </div>
                    ))}
                </div>
            )}

            {/* Main Content Area */}
            <div style={{ flexGrow: 1, overflow: 'hidden', display: 'flex', backgroundColor: '#1a1a1a' }}>
                {layoutFilesToRender.length > 0 ? (
                    <div style={{ width: '100%', height: '100%', overflow: 'auto' }}>
                        {layoutFilesToRender.map(file => (
                            <div key={file.name} style={{ width: '100%', height: '100%' }}>
                                {window.LoaderOrchestrator ? (
                                    <window.LoaderOrchestrator layoutJson={file.content} filePath={file.path} />
                                ) : (
                                    <pre style={{padding: '20px'}}>{JSON.stringify(file.content, null, 2)}</pre>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <div style={{ padding: '20px', color: '#888', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
                        {directories.length > 0 ? "Select a tab above to navigate." : "No layout configuration found in this folder."}
                    </div>
                )}
            </div>
        </div>
    );
};

window.TabManager = TabManager;
