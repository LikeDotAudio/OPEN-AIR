// Equalization Graph Component
// Renders a specialized frequency equalization curve based on ECharts.

const Equalization = ({ value: mqttData, config }) => {
    const chartRef = React.useRef(null);
    const chartInstance = React.useRef(null);
    const useMqttLang = window.useMqttLang || (() => ['En', () => {}]);
    const [lang] = useMqttLang();

    const title = config?.label?.[lang] || config?.label?.En || config?.title || "Equalizer";
    
    // Geometry
    const heightVal = config?.geometry?.height || config?.layout?.height || 350;
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
        // Generate a sample smooth curve if no data provided
        let defaultData = [];
        if (primaryDataset?.initial_csv_data) {
            defaultData = parseCsv(primaryDataset.initial_csv_data);
        } else {
            // Sample EQ curve data matching the screenshot feel roughly
            defaultData = [
                [20, -32], [50, -10], [100, 3], [150, 2], [200, 0], [300, -8], 
                [500, -1], [1000, 2], [2000, 1], [5000, 4], [10000, 1], [20000, 0]
            ];
        }

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
                right: '5%',
                top: '15%',
                bottom: '15%',
                containLabel: true,
                show: false,
            },
            xAxis: {
                type: 'log',
                min: 20,
                max: 20000,
                axisLabel: {
                    formatter: function (value) {
                        if (value === 20) return '20';
                        if (value === 200) return '200';
                        if (value === 2000) return '2k';
                        if (value === 20000) return '20k';
                        return '';
                    },
                    color: '#f48a20',
                    fontWeight: 'bold'
                },
                splitLine: { show: false },
                axisLine: { show: false },
                axisTick: { show: false }
            },
            yAxis: {
                type: 'value',
                min: -32,
                max: 32,
                interval: 8,
                axisLabel: {
                    color: '#f48a20',
                    fontWeight: 'bold'
                },
                splitLine: { show: false },
                axisLine: { show: false },
                axisTick: { show: false }
            },
            series: [
                {
                    name: '0dB Ref',
                    type: 'line',
                    data: [[20, 0], [20000, 0]],
                    lineStyle: { color: '#f48a20', width: 1, type: 'dashed' },
                    showSymbol: false,
                    animation: false
                },
                {
                    name: 'EQ Curve',
                    type: 'line',
                    data: defaultData,
                    smooth: true,
                    lineStyle: { color: '#f48a20', width: 2 },
                    itemStyle: { color: '#f48a20' },
                    showSymbol: false,
                    animationDuration: 300
                }
            ],
            graphic: [
                {
                    type: 'text',
                    right: '15%',
                    bottom: '5%',
                    style: {
                        text: 'LoCut  LF  LMF  HMF  HF  HiCut',
                        fill: '#f48a20',
                        fontSize: 11,
                        fontWeight: 'bold'
                    }
                },
                {
                    type: 'text',
                    right: '5%',
                    top: '8%',
                    style: {
                        text: 'On',
                        fill: '#f48a20',
                        fontSize: 12,
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

    // Handle real-time MQTT updates
    React.useEffect(() => {
        if (!mqttData || !chartInstance.current) return;
        try {
            if (typeof mqttData === 'string' && mqttData.includes(',')) {
                const newData = parseCsv("x,y\n" + mqttData);
                if (newData.length) {
                    chartInstance.current.setOption({
                        series: [{}, { data: newData }]
                    });
                }
            }
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

window.Equalization = Equalization;
