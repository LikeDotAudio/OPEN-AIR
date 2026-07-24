/**
 * Header: YakAutoBuilder.jsx
 * Purpose: Dynamically transforms generic YAK JSON into rich GUI using Library Control schemas.
 */

window.YakAutoBuilder = ({ config, topic, nodeJson }) => {
    console.log("YakAutoBuilder is executing! (v4)");
    const [enrichedTree, setEnrichedTree] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);

    React.useEffect(() => {
        const buildGUI = async () => {
            try {
                setLoading(true);

                // 1. Load the WYSIWYG Grab Bag schemas
                let grabBag;
                if (window.OaEdGrabBagLoader) {
                    grabBag = await window.OaEdGrabBagLoader.load();
                } else {
                    throw new Error("OaEdGrabBagLoader is not available.");
                }

                // Find our target templates
                const components = grabBag.components || [];
                const actMatch = components.find(c => c.name === 'Exhaustive_Actuator_Example');
                const templateActuator = actMatch ? actMatch.schema : undefined;
                const valMatch = components.find(c => c.name === 'text_value_with_units_Example');
                const templateValue = valMatch ? valMatch.schema : undefined;
                
                // Fallbacks if templates are missing in grab bag for some reason
                const fallbackActuator = templateActuator || { type: '_GuiActuator', cosmetics: { bg_color: '#331100' } };
                const fallbackValue = templateValue || { type: '_SmartInput', cosmetics: { bg_color: '#1a1a1a' } };

                // 2. Fetch the generic YAK instrument schema
                // For this demo, we hardcode to N9340B Frequency if path is missing
                const instrumentPath = (config && config.instrument_path) || '1_Spectrum_YAK/1_N9340B/0_Frequency/yak_frequency.json';
                const yakUrl = `./api/yak_frequency.json`;
                
                const res = await fetch(yakUrl);
                if (!res.ok) throw new Error(`Failed to fetch YAK schema: ${res.status}`);
                const yakData = await res.json();

                // 3. Recursive function to merge YAK hardware params with GrabBag UI params
                const enrichNode = (node) => {
                    if (!node || typeof node !== 'object') return node;

                    // If it's a generic YAK actuator
                    if (node.type === '_GuiActuator') {
                        // Deep clone the beautiful grab bag template
                        const enriched = JSON.parse(JSON.stringify(fallbackActuator));
                        
                        // Override with the hardware specific parameters from YAK
                        if (!enriched.interaction) enriched.interaction = {};
                        if (node.message) enriched.interaction.message = node.message;
                        if (node.label) enriched.label = node.label;
                        
                        // Keep YAK's topic if present
                        if (node.topic) enriched.topic = node.topic;

                        return enriched;
                    }
                    
                    // If it's a generic YAK value input
                    if (node.type === '_GuiValue') {
                        // Deep clone the beautiful input template
                        const enriched = JSON.parse(JSON.stringify(fallbackValue));
                        
                        if (node.label) enriched.label = node.label;
                        if (node.domain) enriched.domain = node.domain;
                        if (node.topic) enriched.topic = node.topic;
                        
                        return enriched;
                    }

                    // Traverse blocks and fields
                    const result = Object.assign({}, node);
                    if (result.blocks) {
                        for (const k of Object.keys(result.blocks)) {
                            result.blocks[k] = enrichNode(result.blocks[k]);
                        }
                    }
                    if (result.fields) {
                        for (const k of Object.keys(result.fields)) {
                            result.fields[k] = enrichNode(result.fields[k]);
                        }
                    }

                    // Add a default layout to OcaBlocks so they look like nice panels
                    if (result.type === 'OcaBlock') {
                        result.layout = result.layout || {};
                        result.layout.padx = 15;
                        result.layout.pady = 15;
                        result.layout.column_spacing = 10;
                        result.layout.row_spacing = 10;
                        result.cosmetics = result.cosmetics || {};
                        result.cosmetics.bg_opacity = 0.8;
                    }

                    return result;
                };

                const enriched = enrichNode(yakData);
                setEnrichedTree(enriched);
                setLoading(false);

            } catch (err) {
                console.error(err);
                setError(err.toString());
                setLoading(false);
            }
        };

        buildGUI();
    }, [config && config.instrument_path]);

    if (loading) return <div style={{ color: '#f4902c', padding: '20px' }}>Magic Auto-Builder: Loading YAK schemas...</div>;
    if (error) return <div style={{ color: 'red', padding: '20px' }}>Error: {error}</div>;

    return (
        <div style={{ width: '100%', minHeight: '300px', backgroundColor: '#550055', overflow: 'auto', padding: '10px' }}>
            <h3 style={{ color: '#60a5fa', margin: '0 0 15px 0' }}>Discovered Hardware: {(config && config.instrument_path) || 'Agilent N9340B'}</h3>
            {enrichedTree && Object.entries(enrichedTree).map(([k, v]) => (
                <window.WidgetFactory key={k} nodeName={k} node={v} path_prefix={`YAK_Discovered/${k}`} />
            ))}
        </div>
    );
};

// Register for the WYSIWYG / GUI Engine
if (!window.OA_COMPONENTS) window.OA_COMPONENTS = {};
window.OA_COMPONENTS['YakAutoBuilder'] = window.YakAutoBuilder;
