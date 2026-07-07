-- =============================================================================
-- FindemproAI v2.0 — Canvas Visual: Schema de referencia PostgreSQL
-- Gestionado por Django migrations (simulate app).
-- Este archivo es solo referencia. Usar: python manage.py migrate simulate
-- =============================================================================

-- Proyectos de modelado
CREATE TABLE IF NOT EXISTS simulate_simulationproject (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    domain VARCHAR(50) DEFAULT 'dairy',
    run_specs JSONB DEFAULT '{
        "start_time": 0,
        "stop_time": 365,
        "dt": 1,
        "time_units": "dias",
        "n_runs_montecarlo": 1000,
        "integration_method": "euler",
        "random_seed": null
    }',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Nodos del canvas
CREATE TABLE IF NOT EXISTS simulate_modelnode (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES simulate_simulationproject(id) ON DELETE CASCADE,
    node_type VARCHAR(20) NOT NULL CHECK (node_type IN ('stock','flow','converter','connector','ghost','text_box')),
    label VARCHAR(100) NOT NULL,
    equation TEXT,
    initial_value DOUBLE PRECISION,
    units VARCHAR(50) DEFAULT '',
    position_x DOUBLE PRECISION DEFAULT 100,
    position_y DOUBLE PRECISION DEFAULT 100,
    width DOUBLE PRECISION DEFAULT 120,
    height DOUBLE PRECISION DEFAULT 60,
    style JSONB DEFAULT '{}',
    distribution_config JSONB,
    ghost_of_node_id UUID REFERENCES simulate_modelnode(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conexiones entre nodos
CREATE TABLE IF NOT EXISTS simulate_modeledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES simulate_simulationproject(id) ON DELETE CASCADE,
    source_node_id UUID NOT NULL REFERENCES simulate_modelnode(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES simulate_modelnode(id) ON DELETE CASCADE,
    edge_type VARCHAR(20) DEFAULT 'causal' CHECK (edge_type IN ('causal','flow','info')),
    line_style VARCHAR(20) DEFAULT 'solid' CHECK (line_style IN ('solid','dashed')),
    polarity VARCHAR(5) CHECK (polarity IN ('+','-',NULL)),
    waypoints JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}'
);

-- Páginas de la Interface Window
CREATE TABLE IF NOT EXISTS simulate_interfacepage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES simulate_simulationproject(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    page_order INTEGER DEFAULT 0,
    background_color VARCHAR(20) DEFAULT '#0f172a',
    metadata JSONB DEFAULT '{}'
);

-- Widgets de la Interface Window
CREATE TABLE IF NOT EXISTS simulate_interfacewidget (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES simulate_interfacepage(id) ON DELETE CASCADE,
    widget_type VARCHAR(30) NOT NULL CHECK (widget_type IN (
        'slider','knob','dial','run_button','stop_button','reset_button',
        'time_slider','graph_output','table_output','gauge','numeric_display',
        'scenario_toggle','text_annotation','page_nav'
    )),
    label VARCHAR(100) DEFAULT '',
    linked_node_id UUID REFERENCES simulate_modelnode(id) ON DELETE SET NULL,
    linked_variable VARCHAR(100) DEFAULT '',
    config JSONB DEFAULT '{}',
    position_x DOUBLE PRECISION DEFAULT 50,
    position_y DOUBLE PRECISION DEFAULT 50,
    width DOUBLE PRECISION DEFAULT 200,
    height DOUBLE PRECISION DEFAULT 100,
    style JSONB DEFAULT '{}'
);

-- Resultados de simulación cacheados
CREATE TABLE IF NOT EXISTS simulate_canvassimulationrun (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES simulate_simulationproject(id) ON DELETE CASCADE,
    run_type VARCHAR(20) DEFAULT 'montecarlo' CHECK (run_type IN ('montecarlo','des','sensitivity','scenario')),
    parameters_snapshot JSONB,
    results JSONB,
    statistics JSONB,
    run_duration_ms INTEGER,
    n_runs INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_modelnode_project ON simulate_modelnode(project_id);
CREATE INDEX IF NOT EXISTS idx_modeledge_project ON simulate_modeledge(project_id);
CREATE INDEX IF NOT EXISTS idx_interfacewidget_page ON simulate_interfacewidget(page_id);
CREATE INDEX IF NOT EXISTS idx_canvasrun_project_date ON simulate_canvassimulationrun(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interfacepage_project ON simulate_interfacepage(project_id, page_order);
