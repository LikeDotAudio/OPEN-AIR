const DynamicGraph = ({ value: mqttData, config }) => {
    const chartRef = React.useRef(null);
    const chartInstance = React.useRef(null);
    const [lang] = window.useMqttLang();

    const title = config?.label?.[lang] || config?.label?.En || config?.title || "Dynamic Graph";
    
    // Geometry
    const heightVal = config?.geometry?.height || config?.layout?.height;
    const height = heightVal ? (typeof heightVal === 'number' ? `${heightVal}px` : heightVal) : "400px";
    
    const widthVal = config?.geometry?.width || config?.layout?.width;
    const width = widthVal ? (typeof widthVal === 'number' ? `${widthVal}px` : widthVal) : "100%";

    // Axes
    const xAxisCfg = config?.axis?.x || {};
    const yAxisCfg = config?.axis?.y || {};
    const showGrid = config?.axis?.show_grid !== false;

    // Data Processing
    const parseCsv = (csvString) => {
        if (!csvString) return [];
        const lines = csvString.split('\n');
        const data = [];
        for (let i = 1; i < lines.length; i++) { // Skip header line
            const trimmedLine = lines[i].trim();
            if (!trimmedLine) continue; // Skip empty lines
            const values = trimmedLine.split(',');
            if (values.length >= 2) {
                const x = parseFloat(values[0]);
                const y = parseFloat(values[1]);
                if (!isNaN(x) && !isNaN(y)) data.push([x, y]);
            }
        }
        return data;
    };

    React.useEffect(() => {
        if (!chartRef.current) return;

        chartInstance.current = echarts.init(chartRef.current, 'dark');

        const initialSeries = (config?.datasets || []).map(ds => ({
            name: ds.label?.[lang] || ds.label?.En || ds.id || 'Series',
            type: 'line',
            smooth: ds.style?.smooth === true, // Enable smoothing if specified
            showSymbol: ds.style?.showSymbol !== false, // Default show symbol, disable if specified false
            data: ds.initial_csv_data ? parseCsv(ds.initial_csv_data) : [],
            lineStyle: {
                color: ds.style?.line_color || '#0f0',
                width: ds.style?.line_width || 2
            },
            itemStyle: { color: ds.style?.line_color || '#0f0' }
        }));

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
            ] : [], // Only add dataZoom if Navigation is enabled in config
            series: initialSeries
        };

        chartInstance.current.setOption(option);

        const resizeHandler = () => chartInstance.current.resize();
        window.addEventListener('resize', resizeHandler);

        return () => {
            window.removeEventListener('resize', resizeHandler);
            if (chartInstance.current) {
                chartInstance.current.dispose();
                chartInstance.current = null;
            }
        };
    }, [config, lang, title, xAxisCfg, yAxisCfg, showGrid]); // Re-init if config changes

    // Handle incoming real-time data from MQTT
    React.useEffect(() => {
        if (mqttData && chartInstance.current) {
            // MQTT data might come as a stringified JSON object or directly as an object.
            let parsedMqttData = mqttData;
            if (typeof mqttData === 'string') {
                try {
                    parsedMqttData = JSON.parse(mqttData);
                } catch (e) {
                    console.error("Failed to parse MQTT data:", e);
                    return; // Skip if parsing fails
                }
            }

            // Expecting mqttData to be an object like: { "ds_sine": [[x1, y1], ...], "ds_cosine": [[x1, y1], ...] }
            const updates = [];
            Object.entries(parsedMqttData).forEach(([datasetId, points]) => {
                if (Array.isArray(points)) {
                    updates.push({
                        name: datasetId, // Use the key (e.g., 'ds_sine') as the series name
                        data: points
                    });
                }
            });
            
            if (updates.length > 0) {
                chartInstance.current.setOption({ series: updates });
            }
        }
    }, [mqttData]); // Re-run when mqttData prop changes

    return (
        <div style={{ width: width, height: height, display: 'flex', flexDirection: 'column' }}>
            <div 
                ref={chartRef} 
                style={{ flexGrow: 1, width: '100%', minHeight: '100px', border: '1px solid #333', borderRadius: '4px', backgroundColor: '#111' }} 
            />
        </div>
    );
};
window.DynamicGraph = DynamicGraph;