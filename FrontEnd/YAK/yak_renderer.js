document.addEventListener('DOMContentLoaded', () => {
    const discoverBtn = document.getElementById('discoverBtn');
    const instrumentSelector = document.getElementById('instrumentSelector');
    const guiContainer = document.getElementById('guiContainer');
    const loader = document.getElementById('loader');
    const loaderText = loader.querySelector('p');
    const appLayout = document.getElementById('appLayout');
    const sidebarNav = document.getElementById('sidebarNav');
    const yakTree = document.getElementById('yakTree');

    // Registry of instruments available for this simulation
    const instruments = {
        'N9340B': {
            basePath: '../../BackEnd/ComProtocols/openair-yak/10_Yak/1_Spectrum_YAK/1_N9340B/',
            schemas: [
                { name: 'Frequency', path: '0_Frequency/yak_frequency.json' },
                { name: 'Bandwidth', path: '1_Bandwidth/yak_bandwidth.json' },
                { name: 'Amplitude', path: '2_Amplitude/yak_amplitude.json' },
                { name: 'Trace', path: '3_Trace/yak_trace.json' },
                { name: 'Markers', path: '7_Markers/yak_markers.json' },
                { name: 'Memory', path: '8_Memory/memory.json' },
                { name: 'System', path: '9_System/yak_system.json' }
            ]
        },
        'HP66102A': {
            basePath: '../../BackEnd/ComProtocols/openair-yak/10_Yak/5_Power_YAK/2_66102A/',
            schemas: [
                { name: 'Instrument', path: '1_INSTrument/instrument.json' },
                { name: 'Source', path: '2_SOURce/source.json' },
                { name: 'Output', path: '3_OUTPut/output.json' },
                { name: 'Measure', path: '4_MEASure/measure.json' },
                { name: 'Trigger', path: '5_TRIGger/trigger.json' },
                { name: 'System', path: '6_SYSTem/system.json' },
                { name: 'Status', path: '7_STATus/status.json' }
            ]
        },
        'Router3235': {
            basePath: '../../BackEnd/ComProtocols/openair-yak/10_Yak/0_Router_YAK/1_3235/',
            schemas: [
                { name: 'Switching Commands', path: '1_Commands/yak_router.json' }
            ]
        }
    };

    let loadedSchemas = {};
    let currentInstrument = null;

    // Reset UI when dropdown changes
    instrumentSelector.addEventListener('change', () => {
        guiContainer.classList.add('hidden');
        discoverBtn.disabled = false;
        discoverBtn.textContent = 'Simulate Discovery Handshake (*IDN?)';
        discoverBtn.classList.add('primary-btn');
        discoverBtn.style.backgroundColor = ''; 
    });

    discoverBtn.addEventListener('click', () => {
        const selectedKey = instrumentSelector.value;
        currentInstrument = instruments[selectedKey];
        loadedSchemas = {};

        // Simulate discovery delay
        guiContainer.classList.remove('hidden');
        appLayout.classList.add('hidden');
        loader.classList.remove('hidden');
        loaderText.textContent = `Parsing schemas for ${selectedKey}...`;
        discoverBtn.disabled = true;
        discoverBtn.textContent = 'Discovering Subsystems...';

        // Fetch all schemas concurrently
        const fetchPromises = currentInstrument.schemas.map(schema => {
            return fetch(currentInstrument.basePath + schema.path)
                .then(res => {
                    if (!res.ok) throw new Error(`HTTP ${res.status}`);
                    return res.json();
                })
                .then(data => {
                    loadedSchemas[schema.name] = data;
                });
        });

        Promise.all(fetchPromises).then(() => {
            setTimeout(() => {
                loader.classList.add('hidden');
                appLayout.classList.remove('hidden');
                discoverBtn.textContent = 'Instrument Fully Loaded';
                discoverBtn.classList.remove('primary-btn');
                discoverBtn.style.backgroundColor = '#10b981'; // Green
                
                buildSidebar();
                
                // Select first tab by default
                if (currentInstrument.schemas.length > 0) {
                    selectTab(currentInstrument.schemas[0].name);
                }
            }, 800);
        }).catch(err => {
            console.error("Failed to fetch YAK JSON schemas", err);
            loader.innerHTML = `<p style="color: #ef4444;">Failed to load instrument schemas: ${err.message}</p>`;
        });
    });

    function buildSidebar() {
        sidebarNav.innerHTML = '';
        currentInstrument.schemas.forEach(schema => {
            const li = document.createElement('li');
            li.className = 'nav-item';
            li.textContent = schema.name;
            li.dataset.tab = schema.name;
            li.addEventListener('click', () => selectTab(schema.name));
            sidebarNav.appendChild(li);
        });
    }

    function selectTab(tabName) {
        Array.from(sidebarNav.children).forEach(li => {
            if (li.dataset.tab === tabName) {
                li.classList.add('active');
            } else {
                li.classList.remove('active');
            }
        });

        const data = loadedSchemas[tabName];
        if (data) {
            renderYakTree(data);
        } else {
            yakTree.innerHTML = '<p style="color: #ef4444;">Schema data not available.</p>';
        }
    }

    function renderYakTree(data) {
        yakTree.innerHTML = '';
        yakTree.className = 'yak-tree';
        
        for (const [key, node] of Object.entries(data)) {
            if (node.blocks) {
                for (const [blockName, blockData] of Object.entries(node.blocks)) {
                    const blockEl = createOcaBlockUI(blockName, blockData);
                    if (blockEl) yakTree.appendChild(blockEl);
                }
            } else if (node.type === 'OcaBlock' || node.type === 'OcaBin') {
                 if (node.fields) {
                    for (const [blockName, blockData] of Object.entries(node.fields)) {
                        const blockEl = createOcaBlockUI(blockName, blockData);
                        if (blockEl) yakTree.appendChild(blockEl);
                    }
                 }
            }
        }
    }

    function createOcaBlockUI(name, block) {
        if (block.type !== 'OcaBlock') return null;

        const container = document.createElement('div');
        container.className = 'oca-block';

        const header = document.createElement('div');
        header.className = 'oca-header';
        
        const title = document.createElement('h2');
        title.className = 'oca-title';
        title.textContent = name.replace(/_/g, ' ');
        header.appendChild(title);

        if (block.description && block.description.En) {
            const desc = document.createElement('p');
            desc.className = 'oca-desc';
            desc.textContent = block.description.En;
            header.appendChild(desc);
        }

        container.appendChild(header);

        if (block.fields) {
            for (const [fieldName, fieldData] of Object.entries(block.fields)) {
                if (fieldData.type === 'OcaBlock') {
                    const controlGroup = renderControlGroup(fieldName, fieldData);
                    if (controlGroup) container.appendChild(controlGroup);
                } else if (fieldData.type === '_GuiActuator') {
                    const dummyGroup = { fields: { 'Execute Command': fieldData } };
                    const controlGroup = renderControlGroup(fieldName, dummyGroup);
                    if (controlGroup) container.appendChild(controlGroup);
                }
            }
        }

        return container;
    }

    function renderControlGroup(name, groupData) {
        const groupEl = document.createElement('div');
        groupEl.className = 'control-group';

        let inputs = [];
        if (groupData.fields && groupData.fields.Input && groupData.fields.Input.fields) {
            for (const [varName, varData] of Object.entries(groupData.fields.Input.fields)) {
                if (varData.type === '_GuiValue') {
                    inputs.push({ name: varName, data: varData });
                }
            }
        }

        inputs.forEach(input => {
            const row = document.createElement('div');
            row.className = 'input-row';

            const labelStr = input.data.label?.En || input.name;
            const unitStr = input.data.domain?.units || '';

            const label = document.createElement('label');
            label.textContent = labelStr;
            row.appendChild(label);

            const inputWrapper = document.createElement('div');
            inputWrapper.className = 'input-with-unit';

            const inputEl = document.createElement('input');
            inputEl.type = 'text';
            inputEl.className = 'gui-input';
            inputEl.placeholder = 'Enter value...';
            inputWrapper.appendChild(inputEl);

            if (unitStr) {
                const unit = document.createElement('div');
                unit.className = 'gui-unit';
                unit.textContent = unitStr;
                inputWrapper.appendChild(unit);
            }

            row.appendChild(inputWrapper);
            groupEl.appendChild(row);
        });

        if (groupData.fields && groupData.fields['Execute Command']) {
            const cmd = groupData.fields['Execute Command'];
            const btn = document.createElement('button');
            btn.className = 'actuator-btn';
            
            let btnText = name.replace(/_/g, ' ');
            if (cmd.label?.En) {
                btnText = cmd.label.En;
            } else if (cmd.label?.inactive?.text?.En) {
                btnText = cmd.label.inactive.text.En;
            }
            
            btn.textContent = btnText;
            
            btn.addEventListener('click', () => {
                alert(`MQTT Publish -> cmd/${instrumentSelector.value}/${name}\nTemplate: ${cmd.message}`);
            });
            
            groupEl.appendChild(btn);
        }

        if (inputs.length === 0 && (!groupData.fields || !groupData.fields['Execute Command'])) {
            return null;
        }

        return groupEl;
    }
});
