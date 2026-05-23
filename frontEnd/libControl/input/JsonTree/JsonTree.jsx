const JsonNode = ({ nodeKey, value, isLast }) => {
    const [isExpanded, setIsExpanded] = React.useState(false);
    const isObject = value !== null && typeof value === 'object';
    const isArray = Array.isArray(value);

    const toggleExpand = () => setIsExpanded(!isExpanded);

    const keyStyle = { color: '#88C0D0', marginRight: '5px' };
    const stringStyle = { color: '#A3BE8C' };
    const numberStyle = { color: '#D08770' };
    const booleanStyle = { color: '#B48EAD' };
    const nullStyle = { color: '#5E81AC' };

    const renderValue = (val) => {
        if (typeof val === 'string') return <span style={stringStyle}>"{val}"</span>;
        if (typeof val === 'number') return <span style={numberStyle}>{val}</span>;
        if (typeof val === 'boolean') return <span style={booleanStyle}>{val ? 'true' : 'false'}</span>;
        if (val === null) return <span style={nullStyle}>null</span>;
        return <span>{String(val)}</span>;
    };

    if (!isObject) {
        return (
            <div style={{ marginLeft: '20px', fontFamily: 'monospace', fontSize: '12px' }}>
                <span style={keyStyle}>"{nodeKey}"</span>: {renderValue(value)}{!isLast && ','}
            </div>
        );
    }

    const keys = Object.keys(value);
    const openBracket = isArray ? '[' : '{';
    const closeBracket = isArray ? ']' : '}';

    return (
        <div style={{ marginLeft: '20px', fontFamily: 'monospace', fontSize: '12px' }}>
            <span onClick={toggleExpand} style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center' }}>
                <span style={{ 
                    display: 'inline-block', 
                    width: '12px', 
                    textAlign: 'center', 
                    color: '#fff', 
                    fontSize: '10px',
                    marginRight: '4px',
                    transition: 'transform 0.1s',
                    transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)'
                }}>
                    ▶
                </span>
                {nodeKey !== null && <span style={keyStyle}>"{nodeKey}"</span>}
                {nodeKey !== null && <span>: </span>}
                <span style={{ color: '#ECEFF4' }}>{openBracket}</span>
                {!isExpanded && <span style={{ color: '#666', padding: '0 5px' }}>{keys.length} items</span>}
                {!isExpanded && <span style={{ color: '#ECEFF4' }}>{closeBracket}{!isLast && ','}</span>}
            </span>
            
            {isExpanded && (
                <div>
                    {keys.map((k, index) => (
                        <JsonNode 
                            key={k} 
                            nodeKey={isArray ? null : k} 
                            value={value[k]} 
                            isLast={index === keys.length - 1} 
                        />
                    ))}
                    <div style={{ marginLeft: '16px', color: '#ECEFF4' }}>
                        {closeBracket}{!isLast && ','}
                    </div>
                </div>
            )}
        </div>
    );
};

const OcaJsonTree = ({ value, config }) => {
    const [jsonData, setJsonData] = React.useState(null);
    const [error, setError] = React.useState(null);

    const title = config?.label_active?.En || config?.label?.En || "JSON Data";
    const height = config?.layout?.height || config?.height || 400;

    React.useEffect(() => {
        // If value comes in over MQTT, parse it
        if (value && typeof value === 'string') {
            try {
                setJsonData(JSON.parse(value));
                setError(null);
            } catch(e) {
                // Not valid JSON, maybe just wrap it
                setJsonData({ raw_payload: value });
                setError(null);
            }
        } else if (value !== null && typeof value === 'object') {
            setJsonData(value);
            setError(null);
        } else if (config?.json_source) {
            // If it's a static file source requested from the server
            // In a real app we'd fetch this from the backend
            setJsonData({ message: `Loading from ${config.json_source} not supported in browser without an API.` });
        }
    }, [value, config]);

    return (
        <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            width: '100%', 
            height: '100%', 
            backgroundColor: '#1E1E1E',
            border: '1px solid #333',
            borderRadius: '4px',
            overflow: 'hidden'
        }}>
            {/* Header */}
            <div style={{ 
                backgroundColor: '#2b2b2b', 
                padding: '8px 15px', 
                borderBottom: '1px solid #111',
                color: '#fff',
                fontSize: '12px',
                fontWeight: 'bold',
                display: 'flex',
                justifyContent: 'space-between'
            }}>
                <span>{title}</span>
            </div>

            {/* Body */}
            <div style={{ 
                padding: '10px', 
                overflow: 'auto', 
                height: height,
                backgroundColor: '#121212',
                color: '#ECEFF4'
            }}>
                {error && <div style={{ color: '#BF616A' }}>{error}</div>}
                {!jsonData && !error && <div style={{ color: '#888' }}>Waiting for data...</div>}
                {jsonData && (
                    <div style={{ marginLeft: '-20px' }}>
                        <JsonNode nodeKey="root" value={jsonData} isLast={true} />
                    </div>
                )}
            </div>
        </div>
    );
};

window.OcaJsonTree = OcaJsonTree;