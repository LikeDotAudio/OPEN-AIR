/**
 * Header: AudioDynamics.jsx
 * Purpose: AudioDynamics component or utility.
 * Description: Handles logic and rendering for AudioDynamics component or utility.
 * 
 * Version: 26.07.05.1
 * Change Log:
 * - 2026-07-05: Initial annotation and documentation added.
 */

// AudioDynamics Graph Component
// Renders a specialized dynamics compressor/expander curve based on ECharts.

// Inline comment: Logic for AudioDynamics
const AudioDynamics = ({ value: mqttData, config }) => {
    const chartRef = React.useRef(null);
    const chartInstance = React.useRef(null);
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();

    const title = config?.label?.[lang] || config?.label?.En || config?.title || "Dynamics";
    
    // Geometry
    const heightVal = config?.geometry?.height || config?.layout?.height || 400;
    const height = typeof heightVal === 'number' ? `${heightVal}px` : heightVal;
    
    const widthVal = config?.geometry?.width || config?.layout?.width || '100%';
    const width = typeof widthVal === 'number' ? `${widthVal}px` : widthVal;

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

    const cfgKey = JSON.stringify({ datasets: config?.datasets, title });

    React.useEffect(() => {
        if (!chartRef.current || typeof echarts === 'undefined') return;

        if (!chartInstance.current) {
            chartInstance.current = echarts.init(chartRef.current, 'dark');
        }

        const primaryDataset = (config?.datasets || [])[0];
        const dynamicData = primaryDataset?.initial_csv_data 
            ? parseCsv(primaryDataset.initial_csv_data) 
            : [[-90, -90], [-60, -60], [-40, -40], [-20, -20], [0, -10]]; // Default comp curve

        const option = {
            backgroundColor: '#050505',
            title: {
                text: title,
                left: 10,
                top: 10,
                textStyle: { color: '#888', fontSize: 12, fontWeight: 'normal' }
            },
            grid: {
                left: '8%',
                right: '8%',
                top: '15%',
                bottom: '15%',
                containLabel: true,
                show: true,
                borderColor: '#444'
            },
            xAxis: {
                type: 'value',
                min: -90,
                max: 0,
                interval: 10,
                name: 'IN',
                nameLocation: 'start',
                nameTextStyle: { color: '#ddd', fontWeight: 'bold' },
                splitLine: { show: true, lineStyle: { color: '#333' } },
                axisLabel: { color: '#ddd', fontWeight: 'bold' },
                axisLine: { show: false },
                axisTick: { show: false },
                position: 'top'
            },
            yAxis: {
                type: 'value',
                min: -90,
                max: 0,
                interval: 10,
                position: 'right',
                splitLine: { show: true, lineStyle: { color: '#333' } },
                axisLabel: { color: '#ddd', fontWeight: 'bold' },
                axisLine: { show: false },
                axisTick: { show: false }
            },
            series: [
                {
                    name: 'Reference',
                    type: 'line',
                    data: [[-90, -90], [0, 0]],
                    lineStyle: { color: '#555', width: 2, type: 'dashed' },
                    showSymbol: false,
                    animation: false
                },
                {
                    name: 'Curve',
                    type: 'line',
                    data: dynamicData,
                    lineStyle: { color: '#f48a20', width: 3 },
                    itemStyle: { color: '#f48a20' },
                    showSymbol: false,
                    animationDuration: 300
                },
                {
                    name: 'Threshold Point',
                    type: 'scatter',
                    data: [[-20, -20]], // Default threshold
                    itemStyle: { color: '#e74c3c' },
                    symbolSize: 10,
                    animationDuration: 300
                }
            ],
            graphic: [
                {
                    type: 'text',
                    left: '10%',
                    bottom: '5%',
                    style: {
                        text: 'Scales in dBFS',
                        fill: '#888',
                        fontSize: 12,
                        fontWeight: 'bold'
                    }
                },
                {
                    type: 'text',
                    right: '10%',
                    bottom: '5%',
                    style: {
                        text: 'SK   Cmp   Exp   Gate    OUT',
                        fill: '#aaa',
                        fontSize: 11,
                        fontWeight: 'bold'
                    }
                }
            ]
        };

        chartInstance.current.setOption(option, { notMerge: true });
        
        const handleResize = () => chartInstance.current?.resize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [cfgKey, height, width, lang]);

    // Handle real-time MQTT updates (if implemented in standard way)
    React.useEffect(() => {
        if (!chartInstance.current) return;
        try {
            let thresh = -20;
            let ratio = 2.0;
            let gain = 0;
            let knee = 5.0;

            if (typeof mqttData === 'object' && mqttData !== null) {
                thresh = parseFloat(mqttData.Thresh?.value || mqttData.Thresh) || -20;
                ratio = parseFloat(mqttData.Ratio?.value || mqttData.Ratio) || 2.0;
                gain = parseFloat(mqttData.Gain?.value || mqttData.Gain) || 0;
                knee = parseFloat(mqttData.Knee?.value || mqttData.Knee) || 5.0;
            }

            const newData = [];
            // Generate standard compressor soft-knee curve
            for (let x = -90; x <= 0; x += 1) {
                let y = x;
                const W = Math.max(0.1, knee);
                
                if (x - thresh < -W / 2) {
                    y = x;
                } else if (Math.abs(x - thresh) <= W / 2) {
                    y = x + (1 / ratio - 1) * Math.pow(x - thresh + W / 2, 2) / (2 * W);
                } else {
                    y = thresh + (x - thresh) / ratio;
                }
                
                y += gain;
                newData.push([x, y]);
            }

            const threshPoint = [[thresh, thresh + gain]];

            chartInstance.current.setOption({
                series: [
                    {
                        name: 'Reference',
                        type: 'line',
                        data: [[-90, -90], [0, 0]],
                        lineStyle: { color: '#555', width: 2, type: 'dashed' },
                        showSymbol: false,
                        animation: false
                    },
                    { 
                        name: 'Curve',
                        type: 'line',
                        data: newData,
                        lineStyle: { color: '#f48a20', width: 3 },
                        itemStyle: { color: '#f48a20' },
                        showSymbol: false,
                        animationDuration: 300
                    },
                    {
                        name: 'Threshold Point',
                        type: 'scatter',
                        data: threshPoint,
                        itemStyle: { color: '#e74c3c' },
                        symbolSize: 10,
                        animationDuration: 300
                    }
                ]
            });
        } catch (e) {
            console.error(e);
        }
    }, [mqttData]);

    return (
        <div style={{ padding: '2px', backgroundColor: '#bbcad1', borderRadius: '4px', border: '1px solid #778' }}>
            <div 
                ref={chartRef}
                style={{ width, height, position: 'relative' }}
            />
        </div>
    );
};

window.AudioDynamics = AudioDynamics;
