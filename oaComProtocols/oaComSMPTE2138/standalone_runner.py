<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CN Tower HO Scale (1:87) Interactive Blueprint</title>
    <style>
        body {
            background-color: #0d1b2a;
            color: #e0e1dd;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            color: #41e2ba;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 5px;
        }
        p.subtitle {
            color: #778da9;
            margin-bottom: 20px;
        }
        .container {
            display: flex;
            gap: 40px;
            background: #1b263b;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            border: 1px solid #415a77;
        }
        .drawing-area {
            position: relative;
            background-image: 
                linear-gradient(rgba(65, 90, 119, 0.2) 1px, transparent 1px),
                linear-gradient(90deg, rgba(65, 90, 119, 0.2) 1px, transparent 1px);
            background-size: 20px 20px;
            border: 1px solid #415a77;
            border-radius: 8px;
        }
        svg {
            display: block;
        }
        .tower-part {
            fill: #1b263b;
            stroke: #41e2ba;
            stroke-width: 1.5;
            transition: all 0.2s ease-in-out;
            cursor: crosshair;
        }
        .tower-part:hover {
            fill: #41e2ba;
            fill-opacity: 0.3;
            stroke: #fff;
            stroke-width: 2.5;
        }
        .ground-line {
            stroke: #778da9;
            stroke-width: 2;
            stroke-dasharray: 5,5;
        }
        .info-panel {
            width: 350px;
            background: #0d1b2a;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #415a77;
        }
        .info-panel h2 {
            margin-top: 0;
            color: #41e2ba;
            border-bottom: 1px solid #415a77;
            padding-bottom: 10px;
        }
        .dim-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(119, 141, 169, 0.2);
        }
        .dim-label {
            color: #778da9;
            font-weight: bold;
        }
        .dim-val {
            color: #fff;
            font-family: monospace;
            font-size: 1.1em;
        }
        #tooltip {
            position: absolute;
            background: rgba(13, 27, 42, 0.95);
            border: 1px solid #41e2ba;
            color: #fff;
            padding: 12px;
            border-radius: 6px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.1s;
            font-size: 0.9em;
            z-index: 10;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            white-space: pre-line;
        }
        .tooltip-title {
            color: #41e2ba;
            font-weight: bold;
            margin-bottom: 6px;
            border-bottom: 1px solid #415a77;
            padding-bottom: 4px;
            text-transform: uppercase;
        }
    </style>
</head>
<body>

    <h1>CN Tower HO Scale Builder's Blueprint</h1>
    <p class="subtitle">Interactive 1:87 Scale Reference Guide (Hover over structural elements)</p>

    <div class="container">
        <div class="drawing-area" id="svg-container">
            <svg width="400" height="850" id="tower-svg">
                <line x1="50" y1="800" x2="350" y2="800" class="ground-line" />
                <text x="55" y="795" fill="#778da9" font-size="12">Lobby Level (0 mm)</text>
                
                <line x1="50" y1="821.5" x2="350" y2="821.5" class="ground-line" stroke-opacity="0.5" />
                <text x="55" y="835" fill="#778da9" font-size="10">Foundation Bottom (-172 mm)</text>

                <rect x="193" y="169" width="14" height="631" class="tower-part" 
                    data-title="Central Hexagonal Core" 
                    data-dims="Width: 115.0 mm&#10;Total Exposed Height: Runs from base to Main Pod" />

                <polygon points="152,800 248,800 207,326 193,326" class="tower-part" 
                    data-title="Concrete Support Legs" 
                    data-dims="Max Base Footprint: 765.5 mm&#10;Individual Leg Width: 80.5 mm&#10;Top of Support Arms Elevation: 3,793 mm" />
                
                <polygon points="152,800 193,800 193,326" class="tower-part" opacity="0.3" pointer-events="none" />

                <polygon points="193,330 180,330 171.5,310 171.5,300 185,287 215,287 228.5,300 228.5,310 220,330 207,330" class="tower-part" 
                    data-title="The Main Pod" 
                    data-dims="Base Radome Elev: 3,759 mm&#10;Roof Elevation: 4,106 mm&#10;Maximum Diameter: 454.0 mm&#10;Total Pod Height: 347 mm" />

                <polygon points="193,165 180,160 180,155 193,150 207,150 220,155 220,160 207,165" class="tower-part" 
                    data-title="SkyPod Observation Deck" 
                    data-dims="Elevation: 5,138 mm&#10;Diameter: 115.0 mm" />

                <polygon points="197.5,169 202.5,169 200.5,5 199.5,5" class="tower-part" 
                    data-title="Antenna Spire" 
                    data-dims="Upper Platform Base Elev: 5,052 mm&#10;Absolute Peak Elev: 6,360 mm&#10;Base Mast Width: 42.0 mm&#10;Tip Width: 17.2 mm" />
            </svg>
            <div id="tooltip">
                <div class="tooltip-title" id="tt-title">Title</div>
                <div id="tt-content">Content</div>
            </div>
        </div>

        <div class="info-panel">
            <h2>Current Hover Data</h2>
            <div id="panel-content">
                <p style="color: #778da9; font-style: italic;">Hover over a section of the blueprint on the left to view the specific HO scale manufacturing dimensions.</p>
            </div>
            
            <h2 style="margin-top: 40px;">Quick Conversions</h2>
            <div class="dim-row"><span class="dim-label">Scale Ratio</span><span class="dim-val">1:87</span></div>
            <div class="dim-row"><span class="dim-label">Total Height</span><span class="dim-val">6,360 mm</span></div>
            <div class="dim-row"><span class="dim-label">Max Width</span><span class="dim-val">765.5 mm</span></div>
            <div class="dim-row"><span class="dim-label">Main Pod Width</span><span class="dim-val">454.0 mm</span></div>
        </div>
    </div>

    <script>
        const tooltip = document.getElementById('tooltip');
        const ttTitle = document.getElementById('tt-title');
        const ttContent = document.getElementById('tt-content');
        const parts = document.querySelectorAll('.tower-part');
        const container = document.getElementById('svg-container');
        const panelContent = document.getElementById('panel-content');

        parts.forEach(part => {
            part.addEventListener('mousemove', (e) => {
                const title = part.getAttribute('data-title');
                const dims = part.getAttribute('data-dims');
                
                // Update Tooltip
                ttTitle.textContent = title;
                ttContent.textContent = dims;
                tooltip.style.opacity = '1';
                
                // Position Tooltip inside container
                const containerRect = container.getBoundingClientRect();
                let x = e.clientX - containerRect.left + 15;
                let y = e.clientY - containerRect.top + 15;
                
                tooltip.style.left = x + 'px';
                tooltip.style.top = y + 'px';

                // Update Side Panel
                const formattedDims = dims.split('\n').map(line => {
                    const [label, val] = line.split(': ');
                    return `<div class="dim-row"><span class="dim-label">${label}</span><span class="dim-val">${val || ''}</span></div>`;
                }).join('');
                
                panelContent.innerHTML = `
                    <h3 style="color: #fff; margin-bottom: 10px;">${title}</h3>
                    ${formattedDims}
                `;
            });

            part.addEventListener('mouseout', () => {
                tooltip.style.opacity = '0';
                panelContent.innerHTML = `<p style="color: #778da9; font-style: italic;">Hover over a section of the blueprint on the left to view the specific HO scale manufacturing dimensions.</p>`;
            });
        });
    </script>
</body>
</html>