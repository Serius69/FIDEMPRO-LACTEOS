/**
 * FindemproAI v2.0 — Model Canvas
 * Canvas interactivo drag-and-drop para modelado stock-and-flow.
 * Usa Cytoscape.js para el grafo. Tres vistas: Model, Map, Equation.
 * Tres modos: Edit, Explore, Presentation.
 */

class FindemproCanvas {
    constructor(containerId, projectId) {
        this.containerId = containerId;
        this.projectId = projectId;
        this.mode = 'edit';         // edit | explore | presentation
        this.currentView = 'model'; // model | map | equation
        this.cy = null;
        this.selectedNode = null;
        this.activeNodeType = null;
        this.unsavedChanges = false;
        this.liveUpdateDebounce = null;
        this._history = [];         // stack de estados para undo
        this._redoStack = [];

        this.init();
    }

    // ─── INICIALIZACIÓN ──────────────────────────────────────────────────────

    async init() {
        await this._loadCytoscape();
        await this.loadProjectData();
        this.setupToolbar();
        this.setupRightPanel();
        this.setupModeControls();
        this.setupViewTabs();
        this._setupAutosave();
        this._showToast('Proyecto cargado', 'info');
    }

    async _loadCytoscape() {
        if (window.cytoscape) return;
        await new Promise((resolve, reject) => {
            const s = document.createElement('script');
            s.src = 'https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js';
            s.onload = resolve;
            s.onerror = reject;
            document.head.appendChild(s);
        });
    }

    async loadProjectData() {
        try {
            const resp = await fetch(`/api/v2/projects/${this.projectId}/`, {
                headers: { 'X-CSRFToken': this._getCsrf() },
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            this.projectData = data;
            this._renderModelView(data.nodes || [], data.edges || []);
        } catch (err) {
            this._showToast(`Error cargando proyecto: ${err.message}`, 'error');
        }
    }

    // ─── RENDERIZADO DEL GRAFO ────────────────────────────────────────────────

    _renderModelView(nodes, edges) {
        const elements = [
            ...nodes.map(n => this._nodeToElement(n)),
            ...edges.map(e => this._edgeToElement(e)),
        ];

        const container = document.getElementById(this.containerId);
        if (!container) return;

        if (this.cy) this.cy.destroy();

        this.cy = cytoscape({
            container,
            elements,
            style: this._getCytoscapeStyles(),
            layout: { name: 'preset' },
            userZoomingEnabled: true,
            userPanningEnabled: true,
            boxSelectionEnabled: true,
            wheelSensitivity: 0.3,
        });

        this._setupCytoscapeEvents();
    }

    _nodeToElement(node) {
        return {
            data: {
                id: node.id,
                label: node.label,
                type: node.node_type,
                equation: node.equation || '',
                initial_value: node.initial_value,
                units: node.units || '',
                distribution_config: node.distribution_config || null,
            },
            position: { x: node.position_x, y: node.position_y },
            classes: node.node_type + (node.distribution_config ? ' has-distribution' : ''),
        };
    }

    _edgeToElement(edge) {
        return {
            data: {
                id: edge.id,
                source: edge.source_node,
                target: edge.target_node,
                label: edge.polarity || '',
                type: edge.edge_type,
            },
            classes: `${edge.line_style || 'solid'} ${edge.edge_type || 'causal'}`,
        };
    }

    _getCytoscapeStyles() {
        return [
            {
                selector: 'node[type="stock"]',
                style: {
                    shape: 'rectangle',
                    'background-color': '#1e3a5f',
                    'border-color': '#3b82f6',
                    'border-width': '3px',
                    color: '#e2e8f0',
                    'font-size': '11px',
                    label: 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    width: '120px',
                    height: '55px',
                    'text-wrap': 'wrap',
                    'text-max-width': '110px',
                },
            },
            {
                selector: 'node[type="flow"]',
                style: {
                    shape: 'diamond',
                    'background-color': '#14532d',
                    'border-color': '#22c55e',
                    'border-width': '2px',
                    color: '#e2e8f0',
                    'font-size': '9px',
                    label: 'data(label)',
                    'text-valign': 'bottom',
                    'text-margin-y': '5px',
                    width: '55px',
                    height: '55px',
                    'text-wrap': 'wrap',
                    'text-max-width': '80px',
                },
            },
            {
                selector: 'node[type="converter"]',
                style: {
                    shape: 'ellipse',
                    'background-color': '#451a03',
                    'border-color': '#f59e0b',
                    'border-width': '2px',
                    color: '#fef3c7',
                    'font-size': '9px',
                    label: 'data(label)',
                    'text-valign': 'center',
                    width: '90px',
                    height: '40px',
                    'text-wrap': 'wrap',
                    'text-max-width': '85px',
                },
            },
            {
                selector: 'node[type="ghost"]',
                style: {
                    shape: 'rectangle',
                    'background-color': '#1e293b',
                    'border-color': '#64748b',
                    'border-width': '2px',
                    'border-style': 'dashed',
                    color: '#94a3b8',
                    'font-size': '9px',
                    label: 'data(label)',
                    'text-valign': 'center',
                    width: '100px',
                    height: '44px',
                    'text-wrap': 'wrap',
                },
            },
            {
                selector: 'node.has-distribution',
                style: {
                    'border-style': 'dashed',
                    'border-color': '#fbbf24',
                    'border-width': '2px',
                },
            },
            {
                selector: 'node:selected',
                style: {
                    'border-color': '#f472b6',
                    'border-width': '3px',
                    'overlay-color': '#f472b6',
                    'overlay-padding': '4px',
                    'overlay-opacity': 0.15,
                },
            },
            {
                selector: 'edge',
                style: {
                    'curve-style': 'bezier',
                    'target-arrow-shape': 'triangle',
                    'line-color': '#475569',
                    'target-arrow-color': '#475569',
                    width: '1.5px',
                    label: 'data(label)',
                    'font-size': '14px',
                    'font-weight': 'bold',
                    color: '#f87171',
                    'text-background-color': '#0f172a',
                    'text-background-opacity': 0.8,
                    'text-background-padding': '2px',
                },
            },
            {
                selector: 'edge.flow',
                style: {
                    'line-color': '#22c55e',
                    'target-arrow-color': '#22c55e',
                    width: '2.5px',
                },
            },
            {
                selector: 'edge.info',
                style: {
                    'line-style': 'dashed',
                    'line-color': '#94a3b8',
                    'target-arrow-shape': 'vee',
                },
            },
            {
                selector: 'edge.dashed',
                style: { 'line-style': 'dashed' },
            },
            {
                selector: 'edge:selected',
                style: { 'line-color': '#f472b6', 'target-arrow-color': '#f472b6' },
            },
        ];
    }

    // ─── EVENTOS DEL CANVAS ───────────────────────────────────────────────────

    _setupCytoscapeEvents() {
        // Node tooltip on hover
        this.cy.on('mouseover', 'node', (evt) => {
            const d = evt.target.data();
            let tip = document.getElementById('cy-tooltip');
            if (!tip) {
                tip = document.createElement('div');
                tip.id = 'cy-tooltip';
                tip.style.cssText = 'position:fixed;background:#1e293b;color:#f8fafc;padding:6px 10px;border-radius:6px;font-size:12px;pointer-events:none;z-index:9999;max-width:240px;line-height:1.4;';
                document.body.appendChild(tip);
            }
            // SEGURIDAD: escapar todo dato del nodo antes de inyectarlo como HTML
            // (label/equation/units pueden contener markup malicioso → stored XSS).
            const esc = (v) => this._esc(v);
            const lines = [`<b>${esc(d.label)}</b> <span style="opacity:.6">[${esc(d.type)}]</span>`];
            if (d.equation) lines.push(`Ec: <code style="font-size:11px">${esc(d.equation)}</code>`);
            if (d.units) lines.push(`Unidades: ${esc(d.units)}`);
            if (d.initial_value != null) lines.push(`Valor inicial: ${esc(d.initial_value)}`);
            tip.innerHTML = lines.join('<br>');
            tip.style.display = 'block';
        });
        this.cy.on('mousemove', 'node', (evt) => {
            const tip = document.getElementById('cy-tooltip');
            if (tip) { tip.style.left = (evt.originalEvent.clientX + 14) + 'px'; tip.style.top = (evt.originalEvent.clientY + 14) + 'px'; }
        });
        this.cy.on('mouseout', 'node', () => {
            const tip = document.getElementById('cy-tooltip');
            if (tip) tip.style.display = 'none';
        });

        // Tap en nodo → abrir panel de propiedades
        this.cy.on('tap', 'node', (evt) => {
            if (this.mode !== 'presentation') {
                this.selectedNode = evt.target;
                this.openNodePanel(evt.target.data());
            }
        });

        // Doble tap en nodo
        this.cy.on('dblclick dbltap', 'node', (evt) => {
            if (this.mode === 'edit') {
                this.openEquationEditor(evt.target.data());
            } else if (this.mode === 'explore') {
                this.openConstantEditor(evt.target.data());
            }
        });

        // Drag de nodo → guardar posición (debounced)
        this.cy.on('dragfree', 'node', (evt) => {
            if (this.mode !== 'edit') return;
            const pos = evt.target.position();
            clearTimeout(this._posSaveTimer);
            this._posSaveTimer = setTimeout(() => {
                this._saveNodePosition(evt.target.id(), pos.x, pos.y);
            }, 600);
        });

        // Click en canvas vacío
        this.cy.on('tap', (evt) => {
            if (evt.target !== this.cy) return;
            if (this.activeNodeType && this.mode === 'edit') {
                this.createNodeAtPosition(this.activeNodeType, evt.position);
            } else {
                this.closeNodePanel();
                this.selectedNode = null;
            }
        });

        // Atajos de teclado — se registran UNA sola vez a nivel document.
        // _setupCytoscapeEvents puede re-ejecutarse (p.ej. al cargar el diagrama causal),
        // por lo que sin el guard se acumularía un handler global por llamada (fuga).
        this._bindGlobalKeydown();
    }

    _bindGlobalKeydown() {
        if (this._globalKeydownBound) return;
        this._globalKeydownBound = true;
        this._onGlobalKeydown = (e) => {
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
            if ((e.key === 'Delete' || e.key === 'Backspace') && this.mode === 'edit') {
                this.deleteSelected();
            }
            if (e.key === 'Escape') {
                this.activeNodeType = null;
                document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
            }
            if (e.ctrlKey && e.key === 'z') { e.preventDefault(); this.undo(); }
            if (e.ctrlKey && e.key === 'y') { e.preventDefault(); this.redo(); }
            if (e.ctrlKey && e.key === 's') { e.preventDefault(); this.saveProject(); }
            if (e.ctrlKey && e.key === 'a') { e.preventDefault(); this.cy.elements().select(); }
        };
        document.addEventListener('keydown', this._onGlobalKeydown);
    }

    /** Limpia los listeners globales; llamar antes de descartar/re-instanciar el canvas. */
    destroy() {
        if (this._onGlobalKeydown) {
            document.removeEventListener('keydown', this._onGlobalKeydown);
            this._globalKeydownBound = false;
            this._onGlobalKeydown = null;
        }
        if (this._onToolbarKeydown) {
            document.removeEventListener('keydown', this._onToolbarKeydown);
            this._onToolbarKeydown = null;
        }
        const tip = document.getElementById('cy-tooltip');
        if (tip) tip.remove();
        if (this.cy && typeof this.cy.destroy === 'function') this.cy.destroy();
    }

    // ─── TOOLBAR ─────────────────────────────────────────────────────────────

    setupToolbar() {
        const toolbar = document.getElementById('canvas-toolbar');
        if (!toolbar) return;

        const tools = [
            { type: 'stock',     icon: '▭', label: 'Stock',     shortcut: 'S' },
            { type: 'flow',      icon: '◆', label: 'Flow',      shortcut: 'F' },
            { type: 'converter', icon: '○', label: 'Converter', shortcut: 'C' },
            { type: 'connector', icon: '→', label: 'Connector', shortcut: 'A' },
            { type: 'ghost',     icon: '◌', label: 'Ghost',     shortcut: 'G' },
        ];

        const sep = '<div class="toolbar-sep"></div>';
        const actions = `
            <button class="tool-btn action-btn" id="btn-undo" title="Deshacer (Ctrl+Z)">↩</button>
            <button class="tool-btn action-btn" id="btn-redo" title="Rehacer (Ctrl+Y)">↪</button>
            ${sep}
            <button class="tool-btn action-btn" id="btn-fit" title="Ajustar vista">⊡</button>
            <button class="tool-btn action-btn" id="btn-save" title="Guardar (Ctrl+S)">💾</button>
            ${sep}
            <button class="tool-btn action-btn" id="btn-run" title="Ejecutar simulación">▶ Simular</button>
        `;

        toolbar.innerHTML = tools.map(t => `
            <button class="tool-btn" data-type="${t.type}" title="${t.label} (${t.shortcut})"
                    data-shortcut="${t.shortcut.toLowerCase()}">
                <span class="tool-icon">${t.icon}</span>
                <span class="tool-label">${t.label}</span>
            </button>
        `).join('') + sep + actions;

        toolbar.querySelectorAll('[data-type]').forEach(btn => {
            btn.addEventListener('click', () => {
                toolbar.querySelectorAll('[data-type]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.activeNodeType = btn.dataset.type;
            });
        });

        document.getElementById('btn-undo')?.addEventListener('click', () => this.undo());
        document.getElementById('btn-redo')?.addEventListener('click', () => this.redo());
        document.getElementById('btn-fit')?.addEventListener('click', () => this.cy.fit(undefined, 40));
        document.getElementById('btn-save')?.addEventListener('click', () => this.saveProject());
        document.getElementById('btn-run')?.addEventListener('click', () => this.runSimulation());

        // Atajos de teclado para herramientas (referencia guardada para poder limpiarla
        // en destroy() y no re-registrar si setupToolbar se re-ejecutara).
        if (this._onToolbarKeydown) document.removeEventListener('keydown', this._onToolbarKeydown);
        this._onToolbarKeydown = (e) => {
            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
            if (e.ctrlKey || e.altKey || e.metaKey) return;
            const found = toolbar.querySelector(`[data-shortcut="${e.key.toLowerCase()}"]`);
            if (found) { e.preventDefault(); found.click(); }
        };
        document.addEventListener('keydown', this._onToolbarKeydown);
    }

    // ─── CONTROLES DE MODO ────────────────────────────────────────────────────

    setupModeControls() {
        const modeBar = document.getElementById('mode-controls');
        if (!modeBar) return;

        modeBar.innerHTML = `
            <div class="mode-group">
                <button class="mode-btn active" data-mode="edit">✏️ Edit</button>
                <button class="mode-btn" data-mode="explore">🔍 Explore</button>
                <button class="mode-btn" data-mode="presentation">📊 Present</button>
            </div>
        `;

        modeBar.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                modeBar.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.setMode(btn.dataset.mode);
            });
        });
    }

    setMode(mode) {
        this.mode = mode;
        const toolbar = document.getElementById('canvas-toolbar');
        const rightPanel = document.getElementById('right-panel');

        if (mode === 'presentation') {
            toolbar?.classList.add('hidden');
            rightPanel?.classList.add('hidden');
            this.cy.userPanningEnabled(false);
            this.cy.userZoomingEnabled(false);
        } else {
            toolbar?.classList.remove('hidden');
            rightPanel?.classList.remove('hidden');
            this.cy.userPanningEnabled(true);
            this.cy.userZoomingEnabled(true);
        }

        // En modo Explore: nodos son arrastrables pero no se pueden añadir
        this.cy.autounselectify(mode === 'presentation');
        document.getElementById('canvas-container')?.setAttribute('data-mode', mode);
    }

    // ─── VISTAS (Model / Map / Equation) ─────────────────────────────────────

    setupViewTabs() {
        const viewTabs = document.getElementById('view-tabs');
        if (!viewTabs) return;

        viewTabs.innerHTML = `
            <button class="view-tab active" data-view="model">Model View</button>
            <button class="view-tab" data-view="map">Map View</button>
            <button class="view-tab" data-view="equation">Equation View</button>
        `;

        viewTabs.querySelectorAll('.view-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                viewTabs.querySelectorAll('.view-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.switchView(tab.dataset.view);
            });
        });
    }

    async switchView(view) {
        this.currentView = view;
        if (view === 'model') {
            await this.loadProjectData();
        } else if (view === 'map') {
            await this._loadMapView();
        } else if (view === 'equation') {
            this._renderEquationView();
        }
    }

    async _loadMapView() {
        try {
            const resp = await fetch(
                `/api/v2/projects/${this.projectId}/simulate/causal-diagram/`,
                { headers: { 'X-CSRFToken': this._getCsrf() } },
            );
            const data = await resp.json();
            if (this.cy) this.cy.destroy();
            this.cy = cytoscape({
                container: document.getElementById(this.containerId),
                elements: data.elements,
                style: data.style,
                layout: { name: 'preset' },
                userZoomingEnabled: true,
                userPanningEnabled: true,
            });
            this._setupCytoscapeEvents();
        } catch (err) {
            this._showToast('Error cargando mapa causal', 'error');
        }
    }

    _renderEquationView() {
        const container = document.getElementById(this.containerId);
        if (!container) return;

        const nodes = this.cy ? this.cy.nodes() : [];
        const rows = [];
        const esc = (v) => this._esc(v);
        nodes.forEach(node => {
            const d = node.data();
            if (!['stock', 'flow', 'converter'].includes(d.type)) return;
            // SEGURIDAD: escapar todos los valores de nodo antes de inyectarlos como HTML.
            const eqOrInit = d.equation || (d.initial_value ?? '—');
            rows.push(`
                <tr>
                    <td><span class="node-badge ${esc(d.type)}">${esc(d.type)}</span></td>
                    <td><strong>${esc(d.label)}</strong></td>
                    <td><code class="equation-code">${esc(eqOrInit)}</code></td>
                    <td>${esc(d.units || '')}</td>
                    <td>${d.distribution_config ? `<span class="dist-badge">🎲 ${esc(d.distribution_config.dist_type)}</span>` : ''}</td>
                    <td>
                        <button class="btn-icon" onclick="canvas.openEquationEditor(${esc(JSON.stringify(d))})">✏️</button>
                    </td>
                </tr>
            `);
        });

        container.innerHTML = `
            <div class="equation-view">
                <h3>Equation View — ${esc(this.projectData?.name || '')}</h3>
                <table class="eq-table">
                    <thead><tr><th>Tipo</th><th>Variable</th><th>Ecuación / Valor Inicial</th><th>Unidades</th><th>Distribución</th><th></th></tr></thead>
                    <tbody>${rows.join('')}</tbody>
                </table>
            </div>
        `;
    }

    // ─── PANEL LATERAL DERECHO ────────────────────────────────────────────────

    setupRightPanel() {
        const panel = document.getElementById('right-panel');
        if (!panel) return;

        panel.innerHTML = `
            <div class="panel-tabs">
                <button class="panel-tab active" data-tab="properties">Propiedades</button>
                <button class="panel-tab" data-tab="run-specs">Run Specs</button>
                <button class="panel-tab" data-tab="sensitivity">Sensibilidad</button>
            </div>
            <div class="panel-content">
                <div id="tab-properties" class="tab-pane active">
                    <p class="panel-hint">Selecciona un nodo para editar sus propiedades.</p>
                </div>
                <div id="tab-run-specs" class="tab-pane hidden">
                    ${this._renderRunSpecsForm()}
                </div>
                <div id="tab-sensitivity" class="tab-pane hidden">
                    ${this._renderSensitivityPanel()}
                </div>
            </div>
        `;

        panel.querySelectorAll('.panel-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                panel.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
                panel.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
                tab.classList.add('active');
                document.getElementById(`tab-${tab.dataset.tab}`)?.classList.remove('hidden');
            });
        });
    }

    openNodePanel(nodeData) {
        const pane = document.getElementById('tab-properties');
        if (!pane) return;

        const distOptions = ['normal', 'lognormal', 'triangular', 'uniform', 'gamma', 'beta', 'weibull']
            .map(d => `<option value="${d}" ${nodeData.distribution_config?.dist_type === d ? 'selected' : ''}>${d.charAt(0).toUpperCase() + d.slice(1)}</option>`)
            .join('');

        pane.innerHTML = `
            <div class="node-panel">
                <div class="node-type-badge badge-${nodeData.type}">${nodeData.type.toUpperCase()}</div>

                <div class="field-group">
                    <label>Nombre</label>
                    <input type="text" id="np-label" value="${this._esc(nodeData.label)}"
                           onchange="canvas.updateNodeProperty('${nodeData.id}', 'label', this.value)">
                </div>

                ${nodeData.type === 'stock' ? `
                <div class="field-group">
                    <label>Valor Inicial</label>
                    <input type="number" id="np-initial" value="${nodeData.initial_value ?? ''}" step="any"
                           onchange="canvas.updateNodeProperty('${nodeData.id}', 'initial_value', parseFloat(this.value))">
                </div>` : ''}

                <div class="field-group">
                    <label>Unidades</label>
                    <input type="text" id="np-units" value="${this._esc(nodeData.units || '')}"
                           placeholder="ej: litros, BOB/dia"
                           onchange="canvas.updateNodeProperty('${nodeData.id}', 'units', this.value)">
                </div>

                ${['flow', 'converter'].includes(nodeData.type) ? `
                <div class="field-group">
                    <label>Ecuación</label>
                    <textarea id="np-equation" rows="3"
                              onchange="canvas.updateNodeProperty('${nodeData.id}', 'equation', this.value)">${this._esc(nodeData.equation || '')}</textarea>
                </div>

                <div class="field-group">
                    <label>Distribución Probabilística</label>
                    <select onchange="canvas.setDistribution('${nodeData.id}', this.value)">
                        <option value="">Sin distribución (determinístico)</option>
                        ${distOptions}
                    </select>
                    ${nodeData.distribution_config
                        ? `<div class="dist-params" id="dist-params-${nodeData.id}">
                               ${this._renderDistParams(nodeData.id, nodeData.distribution_config)}
                           </div>`
                        : ''}
                </div>` : ''}

                <div class="field-group field-actions">
                    <button class="btn-danger btn-sm" onclick="canvas.deleteNode('${nodeData.id}')">🗑 Eliminar</button>
                </div>
            </div>
        `;

        document.querySelector('[data-tab="properties"]')?.click();
    }

    closeNodePanel() {
        const pane = document.getElementById('tab-properties');
        if (pane) pane.innerHTML = '<p class="panel-hint">Selecciona un nodo para editar sus propiedades.</p>';
    }

    _renderRunSpecsForm() {
        const rs = this.projectData?.run_specs || {};
        return `
            <div class="run-specs-form">
                <div class="field-group">
                    <label>Tiempo inicio</label>
                    <input type="number" id="rs-start" value="${rs.start_time ?? 0}"
                           onchange="canvas.updateRunSpec('start_time', parseFloat(this.value))">
                </div>
                <div class="field-group">
                    <label>Tiempo fin</label>
                    <input type="number" id="rs-stop" value="${rs.stop_time ?? 365}"
                           onchange="canvas.updateRunSpec('stop_time', parseFloat(this.value))">
                </div>
                <div class="field-group">
                    <label>DT (paso de tiempo)</label>
                    <input type="number" id="rs-dt" value="${rs.dt ?? 1}" step="0.1" min="0.01"
                           onchange="canvas.updateRunSpec('dt', parseFloat(this.value))">
                </div>
                <div class="field-group">
                    <label>Unidades de tiempo</label>
                    <select id="rs-units" onchange="canvas.updateRunSpec('time_units', this.value)">
                        ${['dias','semanas','meses','años'].map(u =>
                            `<option value="${u}" ${rs.time_units === u ? 'selected' : ''}>${u}</option>`
                        ).join('')}
                    </select>
                </div>
                <div class="field-group">
                    <label>N runs Monte Carlo</label>
                    <input type="number" id="rs-nruns" value="${rs.n_runs_montecarlo ?? 1000}"
                           min="1" max="100000"
                           onchange="canvas.updateRunSpec('n_runs_montecarlo', parseInt(this.value))">
                </div>
                <div class="field-group">
                    <label>Método de integración</label>
                    <select id="rs-method" onchange="canvas.updateRunSpec('integration_method', this.value)">
                        <option value="euler" ${rs.integration_method === 'euler' ? 'selected' : ''}>Euler</option>
                        <option value="runge_kutta_4" ${rs.integration_method === 'runge_kutta_4' ? 'selected' : ''}>Runge-Kutta 4</option>
                        <option value="midpoint" ${rs.integration_method === 'midpoint' ? 'selected' : ''}>Punto Medio</option>
                    </select>
                </div>
                <div class="field-group">
                    <label>Semilla aleatoria</label>
                    <input type="number" id="rs-seed" value="${rs.random_seed ?? ''}"
                           placeholder="Dejar vacío para aleatorio"
                           onchange="canvas.updateRunSpec('random_seed', this.value ? parseInt(this.value) : null)">
                </div>
                <button class="btn-primary btn-block" onclick="canvas.saveRunSpecs()">Guardar Run Specs</button>
            </div>
        `;
    }

    _renderSensitivityPanel() {
        return `
            <div class="sensitivity-panel">
                <p class="panel-hint">Ejecuta una simulación primero para ver el análisis de sensibilidad.</p>
                <div id="sensitivity-results" class="hidden"></div>
            </div>
        `;
    }

    _renderDistParams(nodeId, distConfig) {
        const { dist_type, params } = distConfig;
        const paramDefs = {
            normal:     ['mean', 'std'],
            lognormal:  ['mu', 'sigma'],
            triangular: ['low', 'mode', 'high'],
            uniform:    ['low', 'high'],
            gamma:      ['shape', 'scale'],
            beta:       ['alpha', 'beta', 'low', 'high'],
            weibull:    ['shape', 'scale'],
        };
        const fields = paramDefs[dist_type] || [];
        return fields.map(p => `
            <div class="param-row">
                <label>${p}</label>
                <input type="number" step="any" value="${params[p] ?? ''}"
                       onchange="canvas.updateDistParam('${nodeId}', '${p}', parseFloat(this.value))">
            </div>
        `).join('');
    }

    // ─── OPERACIONES CRUD ─────────────────────────────────────────────────────

    async createNodeAtPosition(nodeType, position) {
        const label = `${nodeType.charAt(0).toUpperCase() + nodeType.slice(1)} ${Date.now() % 10000}`;
        const payload = {
            project: this.projectId,
            node_type: nodeType,
            label,
            position_x: position.x,
            position_y: position.y,
            equation: nodeType === 'converter' ? '0' : null,
            initial_value: nodeType === 'stock' ? 0 : null,
        };

        try {
            const resp = await this._api(`/api/v2/projects/${this.projectId}/nodes/`, 'POST', payload);
            const node = await resp.json();
            this._pushHistory();
            this.cy.add(this._nodeToElement(node));
            this._showToast(`Nodo "${label}" creado`, 'success');
        } catch (err) {
            this._showToast(`Error creando nodo: ${err.message}`, 'error');
        }
    }

    async updateNodeProperty(nodeId, prop, value) {
        if (!this.cy) return;
        const el = this.cy.getElementById(nodeId);
        if (el.length) el.data(prop, value);
        this.unsavedChanges = true;

        try {
            await this._api(`/api/v2/projects/${this.projectId}/nodes/${nodeId}/`, 'PATCH', { [prop]: value });
            if (prop === 'label') {
                el.data('label', value);
                this._triggerLiveUpdate({ [value]: value });
            }
        } catch (err) {
            this._showToast(`Error actualizando propiedad`, 'error');
        }
    }

    async deleteNode(nodeId) {
        if (!confirm('¿Eliminar este nodo y todas sus conexiones?')) return;
        this._pushHistory();
        this.cy.getElementById(nodeId).remove();
        this.closeNodePanel();
        try {
            await this._api(`/api/v2/projects/${this.projectId}/nodes/${nodeId}/`, 'DELETE');
            this._showToast('Nodo eliminado', 'info');
        } catch (err) {
            this._showToast(`Error eliminando nodo`, 'error');
        }
    }

    deleteSelected() {
        const selected = this.cy.$(':selected');
        if (!selected.length) return;
        this._pushHistory();
        const nodeIds = selected.nodes().map(n => n.id());
        const edgeIds = selected.edges().map(e => e.id());

        selected.remove();

        nodeIds.forEach(id => this._api(`/api/v2/projects/${this.projectId}/nodes/${id}/`, 'DELETE').catch(() => {}));
        edgeIds.forEach(id => this._api(`/api/v2/projects/${this.projectId}/edges/${id}/`, 'DELETE').catch(() => {}));
    }

    async _saveNodePosition(nodeId, x, y) {
        try {
            await this._api(`/api/v2/projects/${this.projectId}/nodes/${nodeId}/`, 'PATCH', {
                position_x: x, position_y: y,
            });
        } catch (_) { /* silent */ }
    }

    setDistribution(nodeId, distType) {
        const node = this.cy.getElementById(nodeId);
        if (!node.length) return;

        const distConfig = distType ? { dist_type: distType, params: {} } : null;
        node.data('distribution_config', distConfig);

        if (distType) {
            node.addClass('has-distribution');
        } else {
            node.removeClass('has-distribution');
        }

        const paramContainer = document.getElementById(`dist-params-${nodeId}`);
        if (paramContainer && distConfig) {
            paramContainer.innerHTML = this._renderDistParams(nodeId, distConfig);
        }

        this._api(`/api/v2/projects/${this.projectId}/nodes/${nodeId}/`, 'PATCH', {
            distribution_config: distConfig,
        }).catch(() => this._showToast('Error guardando distribución', 'error'));
    }

    updateDistParam(nodeId, param, value) {
        const node = this.cy.getElementById(nodeId);
        if (!node.length) return;
        const dc = { ...(node.data('distribution_config') || {}) };
        dc.params = { ...(dc.params || {}), [param]: value };
        node.data('distribution_config', dc);
        this._api(`/api/v2/projects/${this.projectId}/nodes/${nodeId}/`, 'PATCH', {
            distribution_config: dc,
        }).catch(() => {});
    }

    updateRunSpec(key, value) {
        if (!this.projectData) this.projectData = {};
        if (!this.projectData.run_specs) this.projectData.run_specs = {};
        this.projectData.run_specs[key] = value;
    }

    async saveRunSpecs() {
        try {
            await this._api(`/api/v2/projects/${this.projectId}/`, 'PATCH', {
                run_specs: this.projectData.run_specs,
            });
            this._showToast('Run specs guardadas', 'success');
        } catch (err) {
            this._showToast('Error guardando run specs', 'error');
        }
    }

    // ─── EDITORES MODALES ─────────────────────────────────────────────────────

    openEquationEditor(nodeData) {
        const modal = this._getOrCreateModal('equation-modal');
        modal.innerHTML = `
            <div class="modal-box">
                <div class="modal-header">
                    <h3>Editor de Ecuación — <span class="badge-${nodeData.type}">${nodeData.label}</span></h3>
                    <button onclick="document.getElementById('equation-modal').classList.add('hidden')">✕</button>
                </div>
                <div class="modal-body">
                    <p class="hint">Variables disponibles: stocks, flows y converters del modelo. Operadores: +, -, *, /, MIN(), MAX(), IF().</p>
                    <textarea id="eq-editor" rows="6" style="width:100%;font-family:monospace">${nodeData.equation || ''}</textarea>
                </div>
                <div class="modal-footer">
                    <button class="btn-secondary" onclick="document.getElementById('equation-modal').classList.add('hidden')">Cancelar</button>
                    <button class="btn-primary" onclick="canvas._applyEquation('${nodeData.id}')">Aplicar</button>
                </div>
            </div>
        `;
        modal.classList.remove('hidden');
    }

    _applyEquation(nodeId) {
        const eq = document.getElementById('eq-editor')?.value?.trim();
        if (eq !== undefined) {
            this.updateNodeProperty(nodeId, 'equation', eq);
            this.cy.getElementById(nodeId).data('equation', eq);
        }
        document.getElementById('equation-modal')?.classList.add('hidden');
    }

    openConstantEditor(nodeData) {
        if (nodeData.type === 'stock') {
            const val = prompt(`Valor inicial de "${nodeData.label}":`, nodeData.initial_value ?? '');
            if (val !== null && !isNaN(parseFloat(val))) {
                this.updateNodeProperty(nodeData.id, 'initial_value', parseFloat(val));
                this._triggerLiveUpdate({ [nodeData.label]: parseFloat(val) });
            }
        } else {
            const val = prompt(`Valor de "${nodeData.label}":`, nodeData.equation ?? '');
            if (val !== null) {
                this.updateNodeProperty(nodeData.id, 'equation', val);
                this._triggerLiveUpdate({ [nodeData.label]: parseFloat(val) });
            }
        }
    }

    // ─── SIMULACIÓN ───────────────────────────────────────────────────────────

    async runSimulation(runType = 'montecarlo', scenario = 'expected') {
        const btn = document.getElementById('btn-run');

        // Validate model before running — surfaces structural errors early
        this._showToast('Validando modelo...', 'info');
        try {
            const validResp = await this._api(
                `/api/v2/projects/${this.projectId}/simulate/validate/`, 'POST', {},
            );
            const validData = await validResp.json();
            if (validData.errors && validData.errors.length > 0) {
                const msgs = validData.errors.slice(0, 3).join('\n');
                this._showToast(`Modelo inválido:\n${msgs}`, 'error');
                return;
            }
        } catch (err) {
            this._showToast(`Error al validar: ${err.message}`, 'error');
            return;
        }

        if (btn) { btn.disabled = true; btn.textContent = '⏳ Simulando...'; }
        this._showToast('Ejecutando simulación...', 'info');

        try {
            const resp = await this._api(`/api/v2/projects/${this.projectId}/simulate/`, 'POST', {
                run_type: runType,
                scenario,
            });
            const data = await resp.json();
            if (data.error) throw new Error(data.error);
            this._showSimulationResults(data);
            this._showToast(`Simulación completada (${data.duration_ms} ms)`, 'success');
        } catch (err) {
            this._showToast(`Error en simulación: ${err.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = '▶ Simular'; }
        }
    }

    _showSimulationResults(data) {
        const panel = document.getElementById('simulation-results');
        if (!panel) return;

        const stats = data.statistics || {};
        const pct = v => v != null ? (v * 100).toFixed(1) + '%' : '—';
        const fmt = v => v != null ? Number(v).toLocaleString('es-BO', { minimumFractionDigits: 2 }) : '—';

        panel.innerHTML = `
            <div class="sim-results">
                <h4>Resultados — ${data.run_type} <small>#${(data.run_id||'').slice(0,8)}</small></h4>
                <div class="kpi-grid">
                    <div class="kpi"><span class="kpi-label">Utilidad promedio</span><span class="kpi-value">${fmt(stats.mean_profit)} BOB</span></div>
                    <div class="kpi"><span class="kpi-label">Desv. estándar</span><span class="kpi-value">${fmt(stats.std_profit)} BOB</span></div>
                    <div class="kpi"><span class="kpi-label">P5 utilidad</span><span class="kpi-value">${fmt(stats.p5_profit)} BOB</span></div>
                    <div class="kpi"><span class="kpi-label">P95 utilidad</span><span class="kpi-value">${fmt(stats.p95_profit)} BOB</span></div>
                    <div class="kpi"><span class="kpi-label">Prob. positiva</span><span class="kpi-value">${pct(stats.probability_positive)}</span></div>
                </div>
                <div class="model-summary">
                    Stocks: ${data.compiled_model_summary?.n_stocks ?? '—'} |
                    Flows: ${data.compiled_model_summary?.n_flows ?? '—'} |
                    Converters: ${data.compiled_model_summary?.n_converters ?? '—'}
                </div>
                <div class="scenario-btns">
                    <button class="btn-sm btn-secondary" onclick="canvas.runSimulation('scenario','pessimistic')">Pesimista</button>
                    <button class="btn-sm btn-primary" onclick="canvas.runSimulation('montecarlo')">Monte Carlo</button>
                    <button class="btn-sm btn-secondary" onclick="canvas.runSimulation('scenario','optimistic')">Optimista</button>
                </div>
            </div>
        `;
        panel.classList.remove('hidden');
    }

    _triggerLiveUpdate(paramChanges) {
        clearTimeout(this.liveUpdateDebounce);
        this.liveUpdateDebounce = setTimeout(async () => {
            try {
                const resp = await this._api(
                    `/api/v2/projects/${this.projectId}/simulate/live-update/`, 'POST',
                    { param_changes: paramChanges },
                );
                const data = await resp.json();
                if (data.delta_results) {
                    this._updateResultsOverlay(data);
                }
            } catch (_) { /* silent: live update best-effort */ }
        }, 400);
    }

    _updateResultsOverlay(data) {
        const el = document.getElementById('live-result-overlay');
        if (!el) return;
        const stats = data.delta_results?.statistics || {};
        el.textContent = stats.mean_profit != null
            ? `Utilidad ~${Number(stats.mean_profit).toLocaleString('es-BO', { maximumFractionDigits: 0 })} BOB`
            : '';
    }

    async validateModel() {
        try {
            const resp = await this._api(
                `/api/v2/projects/${this.projectId}/simulate/validate/`, 'POST', {},
            );
            const data = await resp.json();
            this._showValidationResults(data);
        } catch (err) {
            this._showToast('Error validando modelo', 'error');
        }
    }

    _showValidationResults(data) {
        const container = document.getElementById('validation-panel') || this._getOrCreateModal('validation-modal');
        container.innerHTML = `
            <div class="validation-results ${data.valid ? 'valid' : 'invalid'}">
                <h4>${data.valid ? '✅ Modelo válido' : '❌ Modelo con errores'}</h4>
                ${data.errors.length ? `<ul class="error-list">${data.errors.map(e => `<li>${e}</li>`).join('')}</ul>` : ''}
                ${data.warnings.length ? `<ul class="warning-list">${data.warnings.map(w => `<li>⚠️ ${w}</li>`).join('')}</ul>` : ''}
                <p class="hint">Nodos: ${data.node_count} | Edges: ${data.edge_count}</p>
            </div>
        `;
        container.classList.remove('hidden');
    }

    // ─── UNDO / REDO ─────────────────────────────────────────────────────────

    _pushHistory() {
        this._history.push(this.cy.json());
        this._redoStack = [];
        if (this._history.length > 30) this._history.shift();
    }

    undo() {
        if (!this._history.length) return;
        this._redoStack.push(this.cy.json());
        const prev = this._history.pop();
        this.cy.json(prev);
        this._showToast('Deshecho', 'info');
    }

    redo() {
        if (!this._redoStack.length) return;
        this._history.push(this.cy.json());
        const next = this._redoStack.pop();
        this.cy.json(next);
        this._showToast('Rehecho', 'info');
    }

    // ─── GUARDAR ─────────────────────────────────────────────────────────────

    async saveProject() {
        // Guardar posiciones de todos los nodos de golpe
        const positions = this.cy.nodes().map(n => ({
            id: n.id(),
            position_x: n.position().x,
            position_y: n.position().y,
        }));
        try {
            await this._api(
                `/api/v2/projects/${this.projectId}/nodes/batch-position/`, 'PUT', positions,
            );
            this.unsavedChanges = false;
            this._showToast('Proyecto guardado', 'success');
        } catch (err) {
            this._showToast('Error guardando proyecto', 'error');
        }
    }

    _setupAutosave() {
        setInterval(() => {
            if (this.unsavedChanges) this.saveProject();
        }, 30000); // autosave cada 30 s
    }

    // ─── UTILIDADES ──────────────────────────────────────────────────────────

    async _api(url, method = 'GET', body = null) {
        const opts = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this._getCsrf(),
            },
        };
        if (body && method !== 'GET') opts.body = JSON.stringify(body);
        const resp = await fetch(url, opts);
        if (!resp.ok && resp.status !== 204) {
            let msg = `HTTP ${resp.status}`;
            try { const d = await resp.json(); msg = d.error || d.detail || JSON.stringify(d); } catch (_) {}
            throw new Error(msg);
        }
        return resp;
    }

    _getCsrf() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');
        const cookie = document.cookie.split('; ').find(r => r.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    _esc(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    _getOrCreateModal(id) {
        let el = document.getElementById(id);
        if (!el) {
            el = document.createElement('div');
            el.id = id;
            el.className = 'modal-overlay hidden';
            el.addEventListener('click', (e) => {
                if (e.target === el) el.classList.add('hidden');
            });
            document.body.appendChild(el);
        }
        return el;
    }

    _showToast(message, type = 'info') {
        const container = document.getElementById('toast-container') || (() => {
            const c = document.createElement('div');
            c.id = 'toast-container';
            c.style.cssText = 'position:fixed;bottom:1rem;right:1rem;z-index:9999;display:flex;flex-direction:column;gap:.5rem';
            document.body.appendChild(c);
            return c;
        })();

        const colors = { info: '#3b82f6', success: '#22c55e', error: '#ef4444', warning: '#f59e0b' };
        const toast = document.createElement('div');
        toast.style.cssText = `background:${colors[type]};color:#fff;padding:.6rem 1rem;border-radius:.4rem;
            font-size:.875rem;box-shadow:0 2px 8px rgba(0,0,0,.3);max-width:300px;word-break:break-word`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3500);
    }
}

// ─── INICIALIZACIÓN GLOBAL ────────────────────────────────────────────────────

let canvas = null;

document.addEventListener('DOMContentLoaded', () => {
    const el = document.getElementById('canvas-root');
    if (!el) return;
    const projectId = el.dataset.projectId;
    if (!projectId) { console.error('[FindemproCanvas] data-project-id no encontrado'); return; }
    canvas = new FindemproCanvas('canvas-root', projectId);
    window.canvas = canvas;
});
