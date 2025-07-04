/**
 * Endogenous Variables - Manejo de la pestaña de variables endógenas
 */
class EndogenousVariables {
    constructor() {
        this.filteredData = [];
        this.currentFilters = {
            search: '',
            category: '',
            trend: ''
        };
        this.sortConfig = {
            column: '',
            direction: 'asc'
        };
        this.init();
    }

    init() {
        this.setupTabActivation();
        this.setupFilters();
        this.setupSorting();
        this.setupModals();
        this.updateVariableCounts();
    }

    setupTabActivation() {
        // Actualizar contadores cuando se activa la pestaña
        const endogenousTab = document.getElementById('endogenous-tab');
        if (endogenousTab) {
            endogenousTab.addEventListener('shown.bs.tab', () => {
                setTimeout(() => this.updateVariableCounts(), 100);
            });
        }
    }

    setupFilters() {
        // Configurar filtros de búsqueda
        const searchInput = document.getElementById('endogenousSearch');
        const categoryFilter = document.getElementById('categoryFilter');
        const trendFilter = document.getElementById('trendFilter');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.currentFilters.search = e.target.value;
                this.applyFilters();
            });
        }
        
        if (categoryFilter) {
            categoryFilter.addEventListener('change', (e) => {
                this.currentFilters.category = e.target.value;
                this.applyFilters();
            });
        }
        
        if (trendFilter) {
            trendFilter.addEventListener('change', (e) => {
                this.currentFilters.trend = e.target.value;
                this.applyFilters();
            });
        }
    }

    setupSorting() {
        // Configurar ordenamiento de tabla
        const sortableHeaders = document.querySelectorAll('.sortable');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const sortType = header.dataset.sort;
                this.sortTable(sortType);
            });
        });
    }

    setupModals() {
        // Configurar eventos de modales
        document.addEventListener('click', (event) => {
            // Cerrar modal de gráfico
            const chartModal = document.getElementById('chartModal');
            if (chartModal && event.target === chartModal) {
                this.closeModal(chartModal);
            }
            
            // Cerrar modal de detalles
            const detailsModal = document.getElementById('variableDetailsModal');
            if (detailsModal && event.target === detailsModal) {
                this.closeModal(detailsModal);
            }
            
            // Botones de cerrar
            if (event.target.classList.contains('btn-close')) {
                const modal = event.target.closest('.modal');
                if (modal) {
                    this.closeModal(modal);
                }
            }
        });
    }

    updateVariableCounts() {
        try {
            const rows = document.querySelectorAll('#endogenousTableBody tr[data-category]');
            let financial = 0, operational = 0, quality = 0;
            
            rows.forEach(row => {
                if (row.style.display !== 'none') {
                    const category = row.dataset.category;
                    if (category === 'financial') financial++;
                    else if (category === 'operational') operational++;
                    else if (category === 'quality') quality++;
                }
            });
            
            // Actualizar contadores en UI
            const financialCount = document.getElementById('financialVarsCount');
            const operationalCount = document.getElementById('operationalVarsCount');
            const qualityCount = document.getElementById('qualityVarsCount');
            
            if (financialCount) financialCount.textContent = financial;
            if (operationalCount) operationalCount.textContent = operational;
            if (qualityCount) qualityCount.textContent = quality;
            
            console.log(`Variables count updated: Financial: ${financial}, Operational: ${operational}, Quality: ${quality}`);
        } catch (error) {
            console.error('Error updating variable counts:', error);
        }
    }

    applyFilters() {
        const { search, category, trend } = this.currentFilters;
        const rows = document.querySelectorAll('#endogenousTableBody tr[data-variable]');
        
        rows.forEach(row => {
            let shouldShow = true;
            
            // Filtro de búsqueda
            if (search) {
                const variable = row.dataset.variable.toLowerCase();
                const description = row.querySelector('small')?.textContent.toLowerCase() || '';
                shouldShow = shouldShow && (variable.includes(search.toLowerCase()) || description.includes(search.toLowerCase()));
            }
            
            // Filtro de categoría
            if (category) {
                shouldShow = shouldShow && row.dataset.category === category;
            }
            
            // Filtro de tendencia
            if (trend) {
                shouldShow = shouldShow && row.dataset.trend === trend;
            }
            
            row.style.display = shouldShow ? '' : 'none';
        });
        
        // Actualizar contadores después del filtrado
        this.updateVariableCounts();
        
        // Actualizar paginación si existe
        if (window.paginationManager) {
            // Resetear a la primera página después del filtrado
            window.paginationManager.currentPages.set('endogenousTable', 1);
        }
    }

    sortTable(sortType) {
        const tbody = document.getElementById('endogenousTableBody');
        const rows = Array.from(tbody.querySelectorAll('tr[data-variable]'));
        
        // Determinar dirección de ordenamiento
        if (this.sortConfig.column === sortType) {
            this.sortConfig.direction = this.sortConfig.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortConfig.column = sortType;
            this.sortConfig.direction = 'asc';
        }
        
        rows.sort((a, b) => {
            let aVal, bVal;
            
            switch(sortType) {
                case 'variable':
                    aVal = a.dataset.variable.toLowerCase();
                    bVal = b.dataset.variable.toLowerCase();
                    return this.sortConfig.direction === 'asc' ? 
                           aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                    
                case 'total':
                    aVal = parseFloat(a.querySelector('.variable-total')?.textContent.replace(/[^\d.-]/g, '') || 0);
                    bVal = parseFloat(b.querySelector('.variable-total')?.textContent.replace(/[^\d.-]/g, '') || 0);
                    return this.sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
                    
                case 'average':
                    aVal = parseFloat(a.querySelector('.variable-average')?.textContent.replace(/[^\d.-]/g, '') || 0);
                    bVal = parseFloat(b.querySelector('.variable-average')?.textContent.replace(/[^\d.-]/g, '') || 0);
                    return this.sortConfig.direction === 'asc' ? aVal - bVal : bVal - aVal;
                    
                case 'category':
                    aVal = a.dataset.category;
                    bVal = b.dataset.category;
                    return this.sortConfig.direction === 'asc' ? 
                           aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                    
                default:
                    return 0;
            }
        });
        
        // Reordenar las filas en el DOM
        rows.forEach(row => tbody.appendChild(row));
        
        // Actualizar indicadores de ordenamiento en headers
        this.updateSortIndicators(sortType);
    }

    updateSortIndicators(activeColumn) {
        const headers = document.querySelectorAll('.sortable');
        headers.forEach(header => {
            header.classList.remove('sort-asc', 'sort-desc');
            if (header.dataset.sort === activeColumn) {
                header.classList.add(`sort-${this.sortConfig.direction}`);
            }
        });
    }

    expandChart(chartName, imageSrc) {
        try {
            const modal = document.getElementById('chartModal');
            const modalTitle = document.getElementById('chartModalTitle');
            const modalImage = document.getElementById('chartModalImage');
            
            if (modal && modalTitle && modalImage) {
                modalTitle.textContent = `Gráfico: ${chartName}`;
                modalImage.src = imageSrc || '';
                
                if (typeof bootstrap !== 'undefined') {
                    new bootstrap.Modal(modal).show();
                } else {
                    modal.style.display = 'block';
                    modal.classList.add('show');
                }
            }
        } catch (error) {
            console.error('Error expanding chart:', error);
        }
    }

    showVariableDetails(variableName) {
        try {
            // Obtener datos de la variable
            const row = document.querySelector(`tr[data-variable="${variableName}"]`);
            if (!row) {
                console.warn(`Variable row not found: ${variableName}`);
                return;
            }
            
            const category = row.dataset.category || 'unknown';
            const trend = row.dataset.trend || 'stable';
            const totalElement = row.querySelector('.variable-total');
            const unitElement = row.querySelector('.variable-unit');
            const averageElement = row.querySelector('.variable-average');
            
            const total = totalElement ? totalElement.textContent.trim() : 'N/A';
            const unit = unitElement ? unitElement.textContent.trim() : 'N/A';
            const average = averageElement ? averageElement.textContent.trim() : 'N/A';
            
            // Construir contenido del modal
            const modalBody = document.getElementById('variableDetailsBody');
            const modalTitle = document.getElementById('variableDetailsTitle');
            
            if (modalBody && modalTitle) {
                modalTitle.textContent = `Detalles: ${variableName}`;
                modalBody.innerHTML = this.generateVariableDetailsHTML(variableName, {
                    category, trend, total, unit, average
                });
                
                // Mostrar modal
                const modal = document.getElementById('variableDetailsModal');
                if (modal) {
                    if (typeof bootstrap !== 'undefined') {
                        new bootstrap.Modal(modal).show();
                    } else {
                        modal.style.display = 'block';
                        modal.classList.add('show');
                    }
                }
            }
        } catch (error) {
            console.error('Error showing variable details:', error);
            if (window.chartManager) {
                window.chartManager.showNotification('Error al mostrar los detalles de la variable.', 'error');
            }
        }
    }

    generateVariableDetailsHTML(variableName, data) {
        const { category, trend, total, unit, average } = data;
        
        return `
            <div class="row">
                <div class="col-md-6">
                    <h6>Información General</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Variable:</strong></td><td>${variableName}</td></tr>
                        <tr><td><strong>Categoría:</strong></td><td class="text-capitalize">${category}</td></tr>
                        <tr><td><strong>Unidad:</strong></td><td>${unit}</td></tr>
                        <tr><td><strong>Tendencia:</strong></td><td class="text-capitalize">${trend}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Valores</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Total:</strong></td><td>${total}</td></tr>
                        <tr><td><strong>Promedio:</strong></td><td>${average}</td></tr>
                    </table>
                </div>
            </div>
            <div class="mt-3">
                <h6>Descripción</h6>
                <p class="text-muted">
                    ${this.getVariableDescription(variableName)}
                </p>
            </div>
            <div class="mt-3">
                <h6>Análisis</h6>
                <div class="alert alert-info">
                    <small>
                        ${this.generateVariableAnalysis(variableName, data)}
                    </small>
                </div>
            </div>
        `;
    }

    getVariableDescription(variableName) {
        const descriptions = {
            'IT': 'Ingresos Totales: Suma de todos los ingresos generados durante el período de simulación.',
            'GT': 'Ganancia Total: Diferencia entre ingresos totales y gastos totales del período.',
            'TG': 'Total Gastos: Suma de todos los costos y gastos incurridos durante la simulación.',
            'TPV': 'Total Productos Vendidos: Cantidad total de productos vendidos en el período.',
            'NSC': 'Nivel de Satisfacción del Cliente: Indicador de calidad del servicio prestado.',
            'EOG': 'Eficiencia Operativa General: Medida de la eficiencia en los procesos operativos.',
            'NR': 'Nivel de Rentabilidad: Porcentaje de ganancia sobre los ingresos totales.',
            'PVP': 'Precio de Venta al Público: Precio unitario de venta del producto.',
            'CFD': 'Costo Fijo Diario: Costos fijos que se incurren diariamente.',
            'CVU': 'Costo Variable Unitario: Costo variable por unidad producida.',
            'DPH': 'Demanda Promedio Histórica: Promedio histórico de la demanda.',
            'CPROD': 'Capacidad de Producción: Capacidad máxima de producción diaria.',
            'NEPP': 'Número de Empleados en Producción: Personal asignado a producción.'
        };
        
        return descriptions[variableName] || `Variable endógena ${variableName} del modelo de simulación.`;
    }

    generateVariableAnalysis(variableName, data) {
        const { category, trend, total } = data;
        let analysis = '';
        
        // Análisis por categoría
        switch(category) {
            case 'financial':
                analysis += 'Esta es una variable financiera clave que impacta directamente en la rentabilidad del negocio. ';
                break;
            case 'operational':
                analysis += 'Variable operativa que refleja la eficiencia de los procesos internos. ';
                break;
            case 'quality':
                analysis += 'Indicador de calidad que mide la satisfacción y percepción del cliente. ';
                break;
        }
        
        // Análisis por tendencia
        switch(trend) {
            case 'increasing':
                analysis += 'La tendencia creciente indica una evolución positiva durante el período simulado.';
                break;
            case 'decreasing':
                analysis += 'La tendencia decreciente sugiere la necesidad de revisar estrategias relacionadas.';
                break;
            case 'stable':
                analysis += 'La tendencia estable muestra consistencia en los valores a lo largo del tiempo.';
                break;
        }
        
        return analysis;
    }

    closeModal(modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
    }

    // Exportar datos de variables endógenas
    exportEndogenousData(format = 'csv') {
        const visibleRows = document.querySelectorAll('#endogenousTableBody tr[data-variable]:not([style*="display: none"])');
        
        if (format === 'csv') {
            this.exportToCSV(visibleRows);
        } else if (format === 'json') {
            this.exportToJSON(visibleRows);
        }
    }

    exportToCSV(rows) {
        let csvContent = 'Variable,Valor Total,Unidad,Promedio Diario,Tendencia,Categoria,Descripcion\n';
        
        rows.forEach(row => {
            const variable = row.dataset.variable;
            const category = row.dataset.category;
            const trend = row.dataset.trend;
            const cells = row.querySelectorAll('td');
            
            const total = cells[1]?.textContent.replace(/[,]/g, '') || '';
            const unit = cells[2]?.textContent || '';
            const average = cells[3]?.textContent.replace(/[,]/g, '') || '';
            const description = cells[0]?.querySelector('small')?.textContent || '';
            
            csvContent += `"${variable}","${total}","${unit}","${average}","${trend}","${category}","${description}"\n`;
        });
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `variables_endogenas_${new Date().getTime()}.csv`;
        link.click();
        
        if (window.chartManager) {
            window.chartManager.showNotification('Variables endógenas exportadas a CSV', 'success');
        }
    }

    exportToJSON(rows) {
        const data = [];
        
        rows.forEach(row => {
            const variable = row.dataset.variable;
            const category = row.dataset.category;
            const trend = row.dataset.trend;
            const cells = row.querySelectorAll('td');
            
            data.push({
                variable: variable,
                total: cells[1]?.textContent.trim() || '',
                unit: cells[2]?.textContent.trim() || '',
                average: cells[3]?.textContent.trim() || '',
                trend: trend,
                category: category,
                description: cells[0]?.querySelector('small')?.textContent.trim() || ''
            });
        });
        
        const jsonContent = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonContent], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `variables_endogenas_${new Date().getTime()}.json`;
        link.click();
        
        if (window.chartManager) {
            window.chartManager.showNotification('Variables endógenas exportadas a JSON', 'success');
        }
    }

    // Limpiar filtros
    clearFilters() {
        this.currentFilters = {
            search: '',
            category: '',
            trend: ''
        };
        
        // Limpiar inputs
        const searchInput = document.getElementById('endogenousSearch');
        const categoryFilter = document.getElementById('categoryFilter');
        const trendFilter = document.getElementById('trendFilter');
        
        if (searchInput) searchInput.value = '';
        if (categoryFilter) categoryFilter.value = '';
        if (trendFilter) trendFilter.value = '';
        
        // Aplicar filtros (mostrar todo)
        this.applyFilters();
    }

    // Buscar variable específica
    searchVariable(variableName) {
        const searchInput = document.getElementById('endogenousSearch');
        if (searchInput) {
            searchInput.value = variableName;
            this.currentFilters.search = variableName;
            this.applyFilters();
        }
    }

    // Obtener estadísticas de variables visibles
    getVisibleVariablesStats() {
        const visibleRows = document.querySelectorAll('#endogenousTableBody tr[data-variable]:not([style*="display: none"])');
        
        const stats = {
            total: visibleRows.length,
            byCategory: { financial: 0, operational: 0, quality: 0 },
            byTrend: { increasing: 0, decreasing: 0, stable: 0 }
        };
        
        visibleRows.forEach(row => {
            const category = row.dataset.category;
            const trend = row.dataset.trend;
            
            if (stats.byCategory[category] !== undefined) {
                stats.byCategory[category]++;
            }
            
            if (stats.byTrend[trend] !== undefined) {
                stats.byTrend[trend]++;
            }
        });
        
        return stats;
    }
}

// Instancia global
window.endogenousVariables = new EndogenousVariables();

// Funciones globales para compatibilidad
window.showVariableDetails = (variableName) => window.endogenousVariables.showVariableDetails(variableName);
window.expandChart = (chartName, imageSrc) => window.endogenousVariables.expandChart(chartName, imageSrc);
window.exportEndogenousVariables = (format) => window.endogenousVariables.exportEndogenousData(format);