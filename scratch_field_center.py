import re

with open('FrontEnd/frameLayout/FieldComponent.jsx', 'r') as f:
    code = f.read()

old_style = """    const style = {
        display: 'flex',
        flexDirection: 'column',
        alignItems: scaling ? 'stretch' : 'center',
        margin: scaling ? 0 : '0 auto',
        width: pw != null ? `${pw * 100}%` : (lWidth != null ? window.oaCssLen(lWidth) : '100%'),
        // Honor an explicit height (px or %); otherwise auto when scaling so the"""

new_style = """    const style = {
        display: 'flex',
        flexDirection: 'column',
        alignItems: scaling ? 'stretch' : 'center',
        margin: scaling ? 0 : '0 auto',
        justifySelf: scaling ? 'stretch' : 'center',
        width: pw != null ? `${pw * 100}%` : (lWidth != null ? window.oaCssLen(lWidth) : '100%'),
        // Honor an explicit height (px or %); otherwise auto when scaling so the"""

code = code.replace(old_style, new_style)

with open('FrontEnd/frameLayout/FieldComponent.jsx', 'w') as f:
    f.write(code)

