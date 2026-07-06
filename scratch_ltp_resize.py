import re

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'r') as f:
    code = f.read()

old_sizing = """    const width  = config?.layout?.width  || config?.width  || 100;
    const height = config?.layout?.height || config?.height || 400;"""

new_sizing = """    const cfgWidth  = config?.layout?.width  || config?.width  || 100;
    const cfgHeight = config?.layout?.height || config?.height || 400;
    const [width, setWidth] = React.useState(typeof cfgWidth === 'number' ? cfgWidth : 100);
    const [height, setHeight] = React.useState(typeof cfgHeight === 'number' ? cfgHeight : 400);

    React.useLayoutEffect(() => {
        if (!wrapperRef.current) return;
        const needsObserver = typeof cfgWidth === 'string' || typeof cfgHeight === 'string';
        if (!needsObserver) {
            setWidth(cfgWidth);
            setHeight(cfgHeight);
            return;
        }
        const ro = new ResizeObserver(entries => {
            for (let entry of entries) {
                const rect = entry.contentRect;
                if (rect.width > 0) setWidth(rect.width);
                if (rect.height > 0) setHeight(rect.height);
            }
        });
        ro.observe(wrapperRef.current);
        return () => ro.disconnect();
    }, [cfgWidth, cfgHeight]);"""

code = code.replace(old_sizing, new_sizing)

old_wrapper = """        <div ref={wrapperRef} className="ltp-wrapper" style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            position: 'relative',
            width: '100%',
            height: '100%',
            justifyContent: 'center'
        }}>
            <div style={{ position: 'relative', width, height }}>"""

new_wrapper = """        <div ref={wrapperRef} className="ltp-wrapper" style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            position: 'relative',
            width: typeof cfgWidth === 'string' ? cfgWidth : `${cfgWidth}px`,
            height: typeof cfgHeight === 'string' ? cfgHeight : `${cfgHeight}px`,
            justifyContent: 'center'
        }}>
            <div style={{ position: 'relative', width, height }}>"""

code = code.replace(old_wrapper, new_wrapper)

with open('FrontEnd/libControl/faders/LTPFader/LTPFader.jsx', 'w') as f:
    f.write(code)

