const DynamicGraph = ({ data, title = "Dynamic Graph", width = "100%", height = "400px" }) => {
    const chartRef = React.useRef(null);
    const chartInstance = React.useRef(null);

    React.useEffect(() => {
        if (!chartRef.current) return;

        // Initialize ECharts
        chartInstance.current = echarts.init(chartRef.current, 'dark');

        const option = {
            backgroundColor: 'transparent',
            title: {
                text: title,
                textStyle: { color: '#ccc', fontSize: 14 }
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: { animation: false }
            },
            xAxis: {
                type: 'time',
                splitLine: { show: false },
                axisLine: { lineStyle: { color: '#555' } }
            },
            yAxis: {
                type: 'value',
                boundaryGap: [0, '100%'],
                splitLine: { show: true, lineStyle: { color: '#333' } },
                axisLine: { lineStyle: { color: '#555' } }
            },
            series: [{
                name: 'Data',
                type: 'line',
                showSymbol: false,
                data: data,
                itemStyle: { color: '#0f0' },
                lineStyle: { width: 2 }
            }]
        };

        chartInstance.current.setOption(option);

        // Handle resize
        const resizeHandler = () => chartInstance.current.resize();
        window.addEventListener('resize', resizeHandler);

        return () => {
            window.removeEventListener('resize', resizeHandler);
            chartInstance.current.dispose();
        };
    }, []);

    // Update data when props change
    React.useEffect(() => {
        if (chartInstance.current) {
            chartInstance.current.setOption({
                series: [{
                    data: data
                }]
            });
        }
    }, [data]);

    return (
        <div 
            ref={chartRef} 
            style={{ width: width, height: height, border: '1px solid #444', borderRadius: '4px' }} 
        />
    );
};
window.DynamicGraph = DynamicGraph;