/**
 * OcaTextLabel Component
 * Author: Gemini (Collaborator)
 * Version: 20260507.1100.2
 *
 * Description: Feature-rich label component matching Python's BuilderTextLabelCreator.
 */

const OcaTextLabel = ({ value, config }) => {
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const label = getLocalizedText(config?.label_active || config?.label, "");
    const units = config?.units || config?.unit_text || "";
    
    const layout = config?.layout || {};
    const fontSize = layout.font || 12;
    const color = layout.colour || config?.cosmetics?.colors?.text || "#ccc";

    let displayText = label;
    if (value !== undefined && value !== null && value !== "") {
        displayText = `${label ? label + ': ' : ''}${value}${units ? ' ' + units : ''}`;
    } else if (config?.value) {
        displayText = `${label ? label + ': ' : ''}${config.value}${units ? ' ' + units : ''}`;
    }

    return (
        <div style={{ padding: '4px 8px', display: 'flex', alignItems: 'center', minHeight: '25px' }}>
            <span style={{ 
                color: color, 
                fontSize: `${fontSize}px`, 
                fontFamily: 'Segoe UI, sans-serif',
                fontWeight: 'bold'
            }}>
                {displayText}
            </span>
        </div>
    );
};

/**
 * OcaTextValueBox Component
 * Description: Boxed value display matching Python's text_value_box logic.
 */
const OcaTextValueBox = ({ label, value, units = '', config }) => {
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();
    
    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const displayLabel = label || getLocalizedText(config?.label, "");
    const displayUnits = units || config?.unit_text || config?.units || "";
    const color = config?.cosmetics?.colors?.highlight || "#f4902c";

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '5px' }}>
            {displayLabel && (
                <span style={{ fontSize: '10px', color: '#999', marginBottom: '4px', textTransform: 'uppercase', fontWeight: 'bold' }}>
                    {displayLabel}
                </span>
            )}
            <div style={{ 
                backgroundColor: '#111', 
                border: '1px solid #444', 
                borderRadius: '4px', 
                padding: '4px 10px',
                minWidth: '60px',
                textAlign: 'center',
                boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.5)'
            }}>
                <span style={{ 
                    color: color, 
                    fontSize: '14px', 
                    fontFamily: 'monospace',
                    fontWeight: 'bold'
                }}>
                    {value !== undefined ? value : '---'}
                    {displayUnits && <span style={{ fontSize: '10px', marginLeft: '2px', color: '#666' }}>{displayUnits}</span>}
                </span>
            </div>
        </div>
    );
};

window.OcaTextLabel = OcaTextLabel;
window.OcaTextValueBox = OcaTextValueBox;
