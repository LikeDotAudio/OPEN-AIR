// DirectionalButtons Component
// Author: Gemini (Collaborator)
// Version: 20260507.1000.1
//
// Description: D-Pad style buttons matching Python's BuilderInputDirectionalButtonsCreator.

const DirectionalButtons = ({ config, topic, nodeJson }) => {
    const useMqtt = !!topic;
    const publish = window.useMqttPublish ? window.useMqttPublish() : () => {};
    const [lang] = window.useMqttLang ? window.useMqttLang() : ['En'];

    const getLocalizedText = (labelData, fallback) => {
        if (!labelData) return fallback;
        if (typeof labelData === 'string') return labelData;
        return labelData[lang] || labelData.En || fallback;
    };

    const label = getLocalizedText(config?.label_active || config?.label, "");

    const handleDirection = (dir) => {
        if (useMqtt && topic) {
            const actionTopic = `${topic}/${dir}`;
            const payload = {
                value: true,
                src: "gui",
                timestamp: Date.now() / 1000
            };
            publish(actionTopic, payload);
        }
    };

    const btnStyle = {
        width: '40px',
        height: '40px',
        backgroundColor: '#333',
        color: '#fff',
        border: '1px solid #555',
        borderRadius: '4px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        cursor: 'pointer',
        userSelect: 'none',
        fontSize: '18px'
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', backgroundColor: '#222', padding: '10px', borderRadius: '5px', border: '1px solid #444' }}>
            {label && (
                <div style={{ fontSize: '12px', color: 'white', fontWeight: 'bold', marginBottom: '10px' }}>
                    {label}
                </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: '40px 40px 40px', gap: '5px' }}>
                <div />
                <div 
                    style={btnStyle} 
                    onPointerDown={(e) => { e.currentTarget.style.backgroundColor = '#555'; handleDirection('up'); }}
                    onPointerUp={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                    onPointerLeave={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                >⬆</div>
                <div />
                <div 
                    style={btnStyle} 
                    onPointerDown={(e) => { e.currentTarget.style.backgroundColor = '#555'; handleDirection('left'); }}
                    onPointerUp={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                    onPointerLeave={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                >⬅</div>
                <div 
                    style={btnStyle} 
                    onPointerDown={(e) => { e.currentTarget.style.backgroundColor = '#555'; handleDirection('down'); }}
                    onPointerUp={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                    onPointerLeave={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                >⬇</div>
                <div 
                    style={btnStyle} 
                    onPointerDown={(e) => { e.currentTarget.style.backgroundColor = '#555'; handleDirection('right'); }}
                    onPointerUp={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                    onPointerLeave={(e) => { e.currentTarget.style.backgroundColor = '#333'; }}
                >➡</div>
            </div>
        </div>
    );
};

window.DirectionalButtons = DirectionalButtons;
