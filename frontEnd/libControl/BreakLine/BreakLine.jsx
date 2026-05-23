const BreakLine = ({ config }) => {
    const orientation = config?.orientation || 'horizontal';
    const color = config?.color || '#333';
    const thickness = config?.thickness || 1;
    const margin = config?.margin || '10px';

    const style = orientation === 'horizontal' 
        ? { width: '100%', height: thickness, backgroundColor: color, margin: `${margin} 0` }
        : { height: '100%', width: thickness, backgroundColor: color, margin: `0 ${margin}` };

    return <div style={style} />;
};
window.BreakLine = BreakLine;