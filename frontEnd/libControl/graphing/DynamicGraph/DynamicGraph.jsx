const DynamicGraph = ({ value: mqttData, config }) => {
    const chartRef = React.useRef(null);
    const chartInstance = React.useRef(null);
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();

    const title = config?.label?.[lang] || config?.label?.En || config?.title || "Dynamic Graph";
    
    // Geometry
    const heightVal = config?.geometry?.height || config?.layout?.height || 400;
    const height = typeof heightVal === 'number' ? `${heightVal}px` : heightVal;
    
    const widthVal = config?.geometry?.width || config?.layout?.width || '100%';
    const width = typeof widthVal === 'number' ? `${widthVal}px` : widthVal;

    // Axes
    const xAxisCfg = config?.axis?.x || {};
    const yAxisCfg = config?.axis?.y || {};
    const showGrid = config?.axis?.show_grid !== false;

    // Data Processing
    const parseCsv = (csvString) => {
        if (!csvString) return [];
        const lines = csvString.split('\n');
        const data = [];
        for (let i = 1; i < lines.length; i++) { 
            const trimmedLine = lines[i].trim();
            if (!trimmedLine) continue; 
            const values = trimmedLine.split(',');
            if (values.length >= 2) {
                const x = parseFloat(values[0]);
                const y = parseFloat(values[1]);
                if (!isNaN(x) && !isNaN(y)) data.push([x, y]);
            }
        }
        return data;
    };

    // Stable signature of everything that affects chart STRUCTURE. Options are
    // re-applied only when this string changes — NOT on every render. `config` gets
    // a fresh identity each render and unrelated MQTT updates re-render every widget,
    // so without this the chart was torn down + redrawn on any GUI change.
    const cfgKey = JSON.stringify({
        datasets: config?.datasets, axis: config?.axis, title, nav: !!config?.Navigation,
    });

    React.useEffect(() => {
        if (!chartRef.current || typeof echarts === 'undefined') return;

        // Init ONCE; reuse the instance afterwards (no dispose/redraw churn).
        if (!chartInstance.current) {
            chartInstance.current = echarts.init(chartRef.current, 'dark');
        }

        const initialSeries = (config?.datasets || []).map(ds => {
            const seriesName = ds.id || ds.label?.[lang] || ds.label?.En || 'Series';
            return {
                id: ds.id,
                name: seriesName,
                type: 'line',
                smooth: ds.style?.smooth === true || (ds.style?.smoothing > 0),
                showSymbol: ds.style?.showSymbol !== false,
                data: ds.initial_csv_data ? parseCsv(ds.initial_csv_data) : [],
                lineStyle: {
                    color: ds.style?.line_color || '#0f0',
                    width: ds.style?.line_width || 2
                },
                itemStyle: { color: ds.style?.line_color || '#0f0' }
            };
        });

        const option = {
            backgroundColor: 'transparent',
            title: {
                text: title,
                left: 'center',
                textStyle: { color: '#ccc', fontSize: 14 }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '10%',
                containLabel: true,
                show: showGrid,
                borderColor: '#333'
            },
            xAxis: {
                type: xAxisCfg.scale === 'log' ? 'log' : 'value',
                name: xAxisCfg.label?.[lang] || xAxisCfg.label?.En || "",
                nameLocation: 'middle',
                nameGap: 25,
                splitLine: { show: showGrid, lineStyle: { color: '#222' } },
                axisLine: { lineStyle: { color: xAxisCfg.color || '#555' } },
                min: xAxisCfg.min,
                max: xAxisCfg.max
            },
            yAxis: {
                type: yAxisCfg.scale === 'log' ? 'log' : 'value',
                name: yAxisCfg.label?.[lang] || yAxisCfg.label?.En || "",
                nameLocation: 'middle',
                nameGap: 40,
                splitLine: { show: showGrid, lineStyle: { color: '#222' } },
                axisLine: { lineStyle: { color: yAxisCfg.color || '#555' } },
                min: yAxisCfg.min,
                max: yAxisCfg.max
            },
            dataZoom: config?.Navigation ? [
                { type: 'inside', start: 0, end: 100 },
                { type: 'slider', bottom: 10, height: 20, borderColor: '#333', handleStyle: { color: '#555' } }
            ] : [],
            series: initialSeries
        };

        chartInstance.current.setOption(option);
    }, [cfgKey, lang]);

    // Resize listener + dispose — mount/unmount only.
    React.useEffect(() => {
        const resizeHandler = () => chartInstance.current && chartInstance.current.resize();
        window.addEventListener('resize', resizeHandler);
        return () => {
            window.removeEventListener('resize', resizeHandler);
            if (chartInstance.current) { chartInstance.current.dispose(); chartInstance.current = null; }
        };
    }, []);

    // Handle incoming real-time data from MQTT
    React.useEffect(() => {
        if (mqttData && chartInstance.current) {
            let parsedMqttData = mqttData;
            if (typeof mqttData === 'string') {
                try {
                    parsedMqttData = JSON.parse(mqttData);
                } catch (e) { return; }
            }

            const updates = [];
            Object.entries(parsedMqttData).forEach(([datasetId, points]) => {
                if (Array.isArray(points)) {
                    // Try to find series by ID first, then fallback to name matching
                    updates.push({
                        id: datasetId,
                        data: points
                    });
                }
            });
            
            if (updates.length > 0) {
                chartInstance.current.setOption({ series: updates });
            }
        }
    }, [mqttData]);

    return (
        <div style={{ width: width, height: height, display: 'flex', flexDirection: 'column' }}>
            <div 
                ref={chartRef} 
                style={{ flexGrow: 1, width: '100%', minHeight: '100px', border: '1px solid #333', borderRadius: '4px', backgroundColor: '#111' }} 
            />
        </div>
    );
};
// Skip re-render when neither the live data nor the config CONTENT changed — this
// stops unrelated GUI changes (which re-render every widget via the MQTT context)
// from cascading into the graph.
window.DynamicGraph = React.memo(DynamicGraph, (prev, next) =>
    prev.value === next.value &&
    JSON.stringify(prev.config) === JSON.stringify(next.config)
);