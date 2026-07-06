import re

# 1. Update Equalization.jsx
with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'r') as f:
    eq_code = f.read()

# Insert publishFn
eq_code = eq_code.replace(
    "const Equalization = ({ node, width, height, isChild, lang }) => {\n    const config = node?.config || node;",
    "const Equalization = ({ node, width, height, isChild, lang }) => {\n    const config = node?.config || node;\n    const publishFn = window.useMqttPublish ? window.useMqttPublish() : null;"
)

# Replace local useMqttPublish calls
old_publish_call = """                                        if (window.useMqttPublish) {
                                            const publish = window.useMqttPublish();
                                            const topic = config?.topics ? config.topics[b.name] : `OpenAir/Gui/${config?.command}/${b.name}`;
                                            publish(topic, { value: newFreq, rotValue: newGain });
                                        }"""
new_publish_call = """                                        if (publishFn) {
                                            const topic = config?.topics ? config.topics[b.name] : `OpenAir/Gui/${config?.command}/${b.name}`;
                                            publishFn(topic, { value: newFreq, rotValue: newGain });
                                        }"""
eq_code = eq_code.replace(old_publish_call, new_publish_call)

with open('FrontEnd/libControl/graphing/Equalization/Equalization.jsx', 'w') as f:
    f.write(eq_code)


# 2. Update LTPFader.jsx
with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'r') as f:
    ltp_code = f.read()

# Update onWheel
old_wheel = """        const onWheel = (e) => {
            e.preventDefault();
            const delta = Math.sign(e.deltaY) * -1; // up is positive
            if (e.altKey) {"""
new_wheel = """        const onWheel = (e) => {
            e.preventDefault();
            const delta = Math.sign(e.deltaY) * -1; // up is positive
            const wheelControlsPot = config?.fader_config?.wheel_controls_pot === true || config?.wheel_controls_pot === true;
            if (e.altKey || wheelControlsPot) {"""
ltp_code = ltp_code.replace(old_wheel, new_wheel)

# Update rendering (remove bg, border, padding, label)
old_render = """    return (
        <div ref={wrapperRef} className="ltp-wrapper" style={{
            backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#3c3f41') : '#3c3f41'),
            border: '1px solid #555',
            padding: '8px',
            borderRadius: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            position: 'relative',
        }}>
            <div className="widget-label" style={{
                marginBottom: 6,
                fontWeight: 'bold',
                color: '#dcdcdc',
                fontSize: width < 50 ? 9 : 12,
                textAlign: 'center',
            }}>
                {String(
                    (config?.label?.active?.text?.En)
                    || (typeof config?.label === 'string' ? config.label : null)
                    || 'LTP'
                ).toUpperCase()}
            </div>
            <div style={{ position: 'relative', width, height }}>"""
new_render = """    return (
        <div ref={wrapperRef} className="ltp-wrapper" style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            position: 'relative',
            width: '100%',
            height: '100%',
            justifyContent: 'center'
        }}>
            <div style={{ position: 'relative', width, height }}>"""
ltp_code = ltp_code.replace(old_render, new_render)

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'w') as f:
    f.write(ltp_code)

