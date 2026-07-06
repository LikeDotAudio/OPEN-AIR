import re

with open('FrontEnd/frameLayout/FieldComponent.jsx', 'r') as f:
    code = f.read()

# 1. Add `messages` retrieval and `isDisabled` logic before `const style = {`
old_style_def = """    const scaling = pw != null || ph != null;

    const style = {"""

new_style_def = """    const scaling = pw != null || ph != null;

    const messages = (window.useMqttMessages && window.useMqttMessages()) || {};
    let isDisabled = false;

    if (nodeName === 'Q_Knob') {
        const t = topic || '';
        if (t.includes('Low/Q')) {
            const shelf = messages['OpenAir/Gui/EQ_Params/Low/Shelf'];
            let sval = shelf;
            try { if (typeof shelf === 'string') sval = JSON.parse(shelf).value; } catch(e){}
            if (sval == 1 || sval === '1' || sval === true || String(shelf).includes('"value":1')) isDisabled = true;
        } else if (t.includes('High/Q')) {
            const shelf = messages['OpenAir/Gui/EQ_Params/High/Shelf'];
            let sval = shelf;
            try { if (typeof shelf === 'string') sval = JSON.parse(shelf).value; } catch(e){}
            if (sval == 1 || sval === '1' || sval === true || String(shelf).includes('"value":1')) isDisabled = true;
        }
    }

    const style = {"""

code = code.replace(old_style_def, new_style_def)

# 2. Add opacity and pointerEvents to `style`
old_style = """        width: pw != null ? `${pw * 100}%` : (lWidth != null ? window.oaCssLen(lWidth) : '100%'),
        // Honor an explicit height (px or %); otherwise auto when scaling so the
        // widget sizes to content.
        height: lHeight != null ? (ph != null ? `${ph * 100}%` : window.oaCssLen(lHeight)) : (scaling ? 'auto' : '100%'),
        boxSizing: 'border-box',
    };"""

new_style = """        width: pw != null ? `${pw * 100}%` : (lWidth != null ? window.oaCssLen(lWidth) : '100%'),
        // Honor an explicit height (px or %); otherwise auto when scaling so the
        // widget sizes to content.
        height: lHeight != null ? (ph != null ? `${ph * 100}%` : window.oaCssLen(lHeight)) : (scaling ? 'auto' : '100%'),
        boxSizing: 'border-box',
        opacity: isDisabled ? 0.3 : 1,
        pointerEvents: isDisabled ? 'none' : 'auto',
        transition: 'opacity 0.3s ease',
        filter: isDisabled ? 'grayscale(100%)' : 'none'
    };"""

code = code.replace(old_style, new_style)

with open('FrontEnd/frameLayout/FieldComponent.jsx', 'w') as f:
    f.write(code)

