/**
 * Radar — radial "radar scope" display (mirror of oaGuiElements/Core/graphing/radar,
 * type `_Radar`). Pure SVG (no ECharts dependency) so the polar grid + sweep are
 * fully under our control.
 *
 * Reads the library config shape: data_parameters {min_value,max_value,
 * points_per_revolution,start_angle,clockwise}, visuals {plot_style,radius},
 * grid_system {show_grid,grid_color,ring_interval,spoke_interval,labels},
 * color_thresholds {mid_point,upper_point,colors{safe,warning,critical}}.
 *
 * Live data: `value` may be an array of numbers (one per sample, mapped around the
 * revolution) or an array of [angleDeg, value] pairs. With no data it renders a
 * faint demo sweep so the scope is recognizable in the editor/preview.
 */
const Radar = ({ value, config }) => {
    const c = config || {};
    const cosmetics = c.cosmetics || {};
    const col = cosmetics.colors || {};

    const dp = c.data_parameters || {};
    const minV = dp.min_value != null ? dp.min_value : 0;
    const maxV = dp.max_value != null ? dp.max_value : 100;
    const ppr = dp.points_per_revolution || 360;
    const startAngle = dp.start_angle != null ? dp.start_angle : 90; // degrees, CCW from +x
    const clockwise = dp.clockwise !== false;

    const vis = c.visuals || {};
    const plotStyle = (vis.plot_style || 'area').toLowerCase();

    const grid = c.grid_system || {};
    const showGrid = grid.show_grid !== false;
    const gridColor = grid.grid_color || '#86c0db';
    const ringInterval = grid.ring_interval || 20;
    const spokeInterval = grid.spoke_interval || 30;
    const showValues = grid.labels?.show_values !== false;

    const thr = c.color_thresholds || {};
    const tColors = thr.colors || {};
    const sweepColor = tColors.safe || col.primary || '#0c75ec';
    const bg = col.background || '#0a0f12';

    // Square scope sized to the smaller layout dimension.
    const wRaw = c.geometry?.width || c.layout?.width || 240;
    const hRaw = c.geometry?.height || c.layout?.height || 240;
    const wNum = typeof wRaw === 'number' ? wRaw : 240;
    const hNum = typeof hRaw === 'number' ? hRaw : 240;
    const size = Math.max(120, Math.min(wNum, hNum) || 240);
    const cx = size / 2, cy = size / 2;
    const R = (size / 2) - 14;

    const dir = clockwise ? -1 : 1;
    const toXY = (val, angleDeg) => {
        const rr = R * Math.max(0, Math.min(1, (val - minV) / ((maxV - minV) || 1)));
        const a = (startAngle + dir * angleDeg) * Math.PI / 180;
        return [cx + rr * Math.cos(a), cy - rr * Math.sin(a)];
    };

    // Resolve sweep samples -> [angleDeg, value][]
    let samples = null;
    if (Array.isArray(value) && value.length) {
        if (Array.isArray(value[0])) samples = value.map(([ang, v]) => [ang, v]);
        else samples = value.map((v, i) => [(i / value.length) * 360, v]);
    } else {
        // demo: gentle rotating lobe so the scope isn't blank
        const n = Math.min(ppr, 180);
        samples = Array.from({ length: n }, (_, i) => {
            const ang = (i / n) * 360;
            const v = minV + (maxV - minV) * (0.45 + 0.35 * Math.sin(ang * Math.PI / 90));
            return [ang, v];
        });
    }
    const pts = samples.map(([ang, v]) => toXY(v, ang).join(',')).join(' ');

    // Rings + ring labels
    const rings = [];
    if (showGrid) {
        for (let lv = minV; lv <= maxV + 1e-9; lv += ringInterval) {
            const rr = R * ((lv - minV) / ((maxV - minV) || 1));
            rings.push(<circle key={`r${lv}`} cx={cx} cy={cy} r={rr} fill="none" stroke={gridColor} strokeOpacity="0.25" strokeWidth="1" />);
            if (showValues && lv > minV) {
                rings.push(<text key={`rl${lv}`} x={cx + 2} y={cy - rr + 9} fill={gridColor} fillOpacity="0.7" fontSize="8" fontFamily="Consolas, monospace">{lv}</text>);
            }
        }
    }
    // Spokes
    const spokes = [];
    if (showGrid) {
        for (let ang = 0; ang < 360; ang += spokeInterval) {
            const [ex, ey] = toXY(maxV, ang);
            spokes.push(<line key={`s${ang}`} x1={cx} y1={cy} x2={ex} y2={ey} stroke={gridColor} strokeOpacity="0.18" strokeWidth="1" />);
        }
    }

    const title = c.label_active?.En || c.label?.En || c.app_settings?.title || "";
    const gid = `radar-${c.id || Math.random().toString(36).slice(2, 8)}`;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            {title && <div style={{ color: gridColor, fontSize: 10, fontFamily: 'Consolas, monospace' }}>{title}</div>}
            <svg width={size} height={size} style={{ background: bg, borderRadius: '50%', border: `1px solid ${gridColor}33` }}>
                <defs>
                    <radialGradient id={gid} cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stopColor={sweepColor} stopOpacity="0.55" />
                        <stop offset="100%" stopColor={sweepColor} stopOpacity="0.05" />
                    </radialGradient>
                </defs>
                <circle cx={cx} cy={cy} r={R} fill="none" stroke={gridColor} strokeOpacity="0.4" strokeWidth="1.5" />
                {rings}
                {spokes}
                {plotStyle === 'area'
                    ? <polygon points={pts} fill={`url(#${gid})`} stroke={sweepColor} strokeWidth="1.5" strokeLinejoin="round" />
                    : <polyline points={pts} fill="none" stroke={sweepColor} strokeWidth="1.5" strokeLinejoin="round" />}
                <circle cx={cx} cy={cy} r="2.5" fill={sweepColor} />
            </svg>
        </div>
    );
};
window.Radar = Radar;
