with open('FrontEnd/frameLayout/FieldComponent.jsx', 'r') as f:
    fc_code = f.read()

old_ltp = """    if (type.toLowerCase().includes('ltp')) {
        return (
            <div style={style}>
                <span style={titleStyle}>{title}</span>
                {window.LTPFader ? <window.LTPFader value={val} onChange={setVal} config={node} /> : <div style={{width: '60px', height: '150px', background: '#444', borderRadius: '30px'}}></div>}
            </div>
        );
    }"""
new_ltp = """    if (type.toLowerCase().includes('ltp')) {
        return (
            <div style={{ ...style, justifyContent: 'center' }}>
                {window.LTPFader ? <window.LTPFader value={val} onChange={setVal} config={node} /> : <div style={{width: '60px', height: '150px', background: '#444', borderRadius: '30px'}}></div>}
            </div>
        );
    }"""
fc_code = fc_code.replace(old_ltp, new_ltp)

with open('FrontEnd/frameLayout/FieldComponent.jsx', 'w') as f:
    f.write(fc_code)

