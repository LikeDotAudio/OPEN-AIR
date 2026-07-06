import re

with open("FrontEnd/libControl/faders/GCA/GCA.jsx", "r") as f:
    code = f.read()

# 1. Update the canvas sizing math
old_sizing = """    const width = config?.layout?.width || 120;
    const height = config?.layout?.height || 400;
    const isRGB = config?.is_rgb === true;"""

new_sizing = """    const overallWidth = config?.layout?.width || 120;
    const overallHeight = config?.layout?.height || 400;
    // Account for padding (10px x 2) + borders (2px)
    const paddingX = 22;
    // Account for padding (10px x 2) + borders (4px) + label text (~25px)
    const paddingY = 49;
    const width = Math.max(10, overallWidth - paddingX);
    const height = Math.max(10, overallHeight - paddingY);
    const isRGB = config?.is_rgb === true;"""

code = code.replace(old_sizing, new_sizing)

# 2. Make the wrapper fill the exact config dimension
old_wrapper = """        <div className="gca-wrapper" style={{ 
            backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#3c3f41') : '#3c3f41'), 
            border: '1px solid #555', 
            borderTop: `3px solid ${config?.active_color || '#f4902c'}`, 
            padding: '10px', 
            borderRadius: '4px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            boxShadow: '0 4px 15px rgba(0,0,0,0.3)'
        }}>"""

new_wrapper = """        <div className="gca-wrapper" style={{ 
            width: '100%',
            height: '100%',
            boxSizing: 'border-box',
            backgroundColor: (window.OaTransparency ? window.OaTransparency.bg(config, '#3c3f41') : '#3c3f41'), 
            border: '1px solid #555', 
            borderTop: `3px solid ${config?.active_color || '#f4902c'}`, 
            padding: '10px', 
            borderRadius: '4px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            boxShadow: '0 4px 15px rgba(0,0,0,0.3)'
        }}>"""

code = code.replace(old_wrapper, new_wrapper)

with open("FrontEnd/libControl/faders/GCA/GCA.jsx", "w") as f:
    f.write(code)

print("GCA.jsx modified successfully!")
