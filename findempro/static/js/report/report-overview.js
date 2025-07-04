/**
 * =================================================================
 * REPORT OVERVIEW - JAVASCRIPT LOGIC
 * =================================================================
 */

/**
 * =================================================================
 * GLOBAL VARIABLES AND CONFIGURATION
 * =================================================================
 */

// Chart instances storage
const chartInstances = {};

// Chart configuration
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
            labels: {
                usePointStyle: true,
                padding: 20,
                font: {
                    size: 12,
                    family: "'Inter', sans-serif"
                }
            }
        },
        title: {
            display: false
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#007bff',
            borderWidth: 1,
            cornerRadius: 6,
            displayColors: false,
            titleFont: {
                size: 13,
                weight: 'bold'
            },
            bodyFont: {
                size: 12
            }
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: {
                color: 'rgba(0, 0, 0, 0.1)',
                drawBorder: false
            },
            ticks: {
                font: {
                    size: 11,
                    family: "'Inter', sans-serif"
                },
                color: '#6c757d'
            }
        },
        x: {
            grid: {
                display: false
            },
            ticks: {
                font: {
                    size: 11,
                    family: "'Inter', sans-serif"
                },
                color: '#6c757d'
            }
        }
    },
    interaction: {
        intersect: false,
        mode: 'index'
    },
    animation: {
        duration: 1000,
        easing: 'easeInOutQuart'
    }
};

/**
 * =================================================================
 * INITIALIZATION
 * =================================================================
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    initializeInteractiveElements();
    initializeAccessibility();
    setupEventListeners();
    
    // Initialize lazy loading for charts
    setupLazyLoading();
    
    // Initialize tooltips if Bootstrap is available
    initializeTooltips();
    
    // Setup print functionality
    setupPrintHandling();
});

/**
 * =================================================================
 * CHART INITIALIZATION
 * =================================================================
 */

function initializeCharts() {
    // Initialize sales chart if data is available
    const salesChartElement = document.getElementById('salesChart');
    if (salesChartElement && window.salesChartData) {
        initializeSalesChart(salesChartElement, window.salesChartData);
    }
    
    // Initialize revenue chart if data is available
    const revenueChartElement = document.getElementById('revenueChart');
    if (revenueChartElement && window.revenueChartData) {
        initializeRevenueChart(revenueChartElement, window.revenueChartData);
    }
    
    // Initialize any additional charts
    initializeAdditionalCharts();
}

function initializeSalesChart(element, data) {
    try {
        const ctx = element.getContext('2d');
        
        chartInstances.salesChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Ventas Proyectadas',
                    data: data.data || [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: '#28a745',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    tooltip: {
                        ...chartOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return `Ventas: ${formatNumber(context.parsed.y)} unidades`;
                            }
                        }
                    }
                }
            }
        });
        
        console.log('Sales chart initialized successfully');
    } catch (error) {
        console.error('Error initializing sales chart:', error);
        showChartError(element, 'Error al cargar gráfico de ventas');
    }
}

function initializeRevenueChart(element, data) {
    try {
        const ctx = element.getContext('2d');
        
        chartInstances.revenueChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Ingresos Proyectados',
                    data: data.data || [],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: '#36a2eb',
                    borderWidth: 2,
                    borderRadius: 4,
                    borderSkipped: false,
                    hoverBackgroundColor: 'rgba(54, 162, 235, 0.9)',
                    hoverBorderColor: '#2691d9'
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    tooltip: {
                        ...chartOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return `Ingresos: ${formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                }
            }
        });
        
        console.log('Revenue chart initialized successfully');
    } catch (error) {
        console.error('Error initializing revenue chart:', error);
        showChartError(element, 'Error al cargar gráfico de ingresos');
    }
}

function initializeAdditionalCharts() {
    // Initialize any additional charts that might be present
    const additionalCharts = document.querySelectorAll('[data-chart-type]');
    
    additionalCharts.forEach(chartElement => {
        const chartType = chartElement.dataset.chartType;
        const chartData = window[chartElement.dataset.chartData];
        
        if (chartData) {
            initializeCustomChart(chartElement, chartType, chartData);
        }
    });
}

function initializeCustomChart(element, type, data) {
    try {
        const ctx = element.getContext('2d');
        const chartId = element.id || `chart_${Date.now()}`;
        
        chartInstances[chartId] = new Chart(ctx, {
            type: type,
            data: data,
            options: chartOptions
        });
        
        console.log(`Custom chart ${chartId} initialized successfully`);
    } catch (error) {
        console.error(`Error initializing custom chart ${element.id}:`, error);
        showChartError(element, 'Error al cargar gráfico');
    }
}

function showChartError(element, message) {
    const container = element.closest('.chart-container');
    if (container) {
        container.innerHTML = `
            <div class="chart-error">
                <div class="text-center text-muted py-4">
                    <i class="ri-error-warning-line" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
                    <p class="mb-0">${message}</p>
                </div>
            </div>
        `;
    }
}

/**
 * =================================================================
 * INTERACTIVE ELEMENTS
 * =================================================================
 */

function initializeInteractiveElements() {
    // Initialize expandable sections
    initializeExpandableSections();
    
    // Initialize metric cards interactions
    initializeMetricCards();
    
    // Initialize table interactions
    initializeTableInteractions();
    
    // Initialize variable cards
    initializeVariableCards();
}

function initializeExpandableSections() {
    const expandableHeaders = document.querySelectorAll('[data-expandable]');
    
    expandableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const targetId = this.dataset.expandable;
            const target = document.getElementById(targetId);
            
            if (target) {
                const isExpanded = target.classList.contains('expanded');
                
                if (isExpanded) {
                    target.classList.remove('expanded');
                    this.classList.remove('expanded');
                } else {
                    target.classList.add('expanded');
                    this.classList.add('expanded');
                }
                
                // Update ARIA attributes
                this.setAttribute('aria-expanded', !isExpanded);
            }
        });
    });
}

function initializeMetricCards() {
    const metricCards = document.querySelectorAll('.metric-card');
    
    metricCards.forEach(card => {
        // Add hover effects and animations
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(-2px) scale(1)';
        });
        
        // Add click interaction for detailed view
        card.addEventListener('click', function() {
            const metricName = this.querySelector('.metric-card-label')?.textContent;
            const metricValue = this.querySelector('.metric-card-value')?.textContent;
            
            if (metricName && metricValue) {
                showMetricDetail(metricName, metricValue);
            }
        });
    });
}

function initializeTableInteractions() {
    // Add sorting functionality to results table
    const sortableHeaders = document.querySelectorAll('.results-table th[data-sortable]');
    
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            const column = this.dataset.sortable;
            const table = this.closest('table');
            sortTable(table, column);
        });
    });
    
    // Add row highlighting
    const tableRows = document.querySelectorAll('.results-table tbody tr');
    
    tableRows.forEach(row => {
        row.addEventListener('click', function() {
            // Remove previous highlights
            tableRows.forEach(r => r.classList.remove('table-row-selected'));
            // Add highlight to clicked row
            this.classList.add('table-row-selected');
        });
    });
}

function initializeVariableCards() {
    const variableCards = document.querySelectorAll('.variable-card');
    
    variableCards.forEach(card => {
        // Add interactive effects
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 8px 25px rgba(0, 123, 255, 0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 12px rgba(0, 123, 255, 0.15)';
        });
    });
}

/**
 * =================================================================
 * EVENT LISTENERS
 * =================================================================
 */

function setupEventListeners() {
    // Window resize handler for chart responsiveness
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(handleWindowResize, 300);
    });
    
    // Keyboard navigation
    document.addEventListener('keydown', handleKeyboardNavigation);
    
    // Print button if present
    const printBtn = document.querySelector('[data-action="print"]');
    if (printBtn) {
        printBtn.addEventListener('click', handlePrint);
    }
    
    // Export button if present
    const exportBtn = document.querySelector('[data-action="export"]');
    if (exportBtn) {
        exportBtn.addEventListener('click', handleExport);
    }
}

function handleWindowResize() {
    // Resize all chart instances
    Object.values(chartInstances).forEach(chart => {
        if (chart && typeof chart.resize === 'function') {
            chart.resize();
        }
    });
}

function handleKeyboardNavigation(event) {
    // Escape key to close any open modals or expanded sections
    if (event.key === 'Escape') {
        closeExpandedSections();
        closeModals();
    }
    
    // Arrow keys for table navigation
    if (event.target.closest('.results-table')) {
        handleTableNavigation(event);
    }
}

/**
 * =================================================================
 * UTILITY FUNCTIONS
 * =================================================================
 */

function formatCurrency(value) {
    if (value === null || value === undefined) return 'No disponible';
    
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatNumber(value, decimals = 0) {
    if (value === null || value === undefined) return 'No disponible';
    
    return new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

function formatPercentage(value, decimals = 2) {
    if (value === null || value === undefined) return 'No disponible';
    
    return new Intl.NumberFormat('es-ES', {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value / 100);
}

/**
 * =================================================================
 * TABLE SORTING
 * =================================================================
 */

function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const header = table.querySelector(`th[data-sortable="${column}"]`);
    
    // Determine sort direction
    const currentDirection = header.dataset.sortDirection || 'asc';
    const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
    
    // Update header indicators
    table.querySelectorAll('th[data-sortable]').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
        delete th.dataset.sortDirection;
    });
    
    header.classList.add(`sort-${newDirection}`);
    header.dataset.sortDirection = newDirection;
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = getCellValue(a, column);
        const bValue = getCellValue(b, column);
        
        if (newDirection === 'asc') {
            return aValue > bValue ? 1 : -1;
        } else {
            return aValue < bValue ? 1 : -1;
        }
    });
    
    // Reappend sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

function getCellValue(row, column) {
    const cellIndex = {
        'metric': 0,
        'value': 1,
        'unit': 2
    }[column] || 0;
    
    const cell = row.cells[cellIndex];
    const text = cell.textContent.trim();
    
    // Try to parse as number
    const numericValue = parseFloat(text.replace(/[^0-9.-]/g, ''));
    return isNaN(numericValue) ? text : numericValue;
}

/**
 * =================================================================
 * MODAL AND DETAIL VIEWS
 * =================================================================
 */

function showMetricDetail(metricName, metricValue) {
    // Create modal or detailed view for metric
    const modal = createModal({
        title: `Detalle: ${metricName}`,
        content: `
            <div class="metric-detail">
                <div class="metric-detail-value">${metricValue}</div>
                <div class="metric-detail-description">
                    <p>Información detallada sobre esta métrica.</p>
                    <ul>
                        <li>Método de cálculo</li>
                        <li>Factores que influyen</li>
                        <li>Interpretación de resultados</li>
                    </ul>
                </div>
            </div>
        `,
        size: 'medium'
    });
    
    showModal(modal);
}

function createModal({ title, content, size = 'medium' }) {
    const modal = document.createElement('div');
    modal.className = `modal fade metric-detail-modal`;
    modal.innerHTML = `
        <div class="modal-dialog modal-${size}">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    return modal;
}

function showModal(modal) {
    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Remove modal from DOM when hidden
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
        });
    }
}

function closeModals() {
    const openModals = document.querySelectorAll('.modal.show');
    openModals.forEach(modal => {
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    });
}

/**
 * =================================================================
 * LAZY LOADING
 * =================================================================
 */

function setupLazyLoading() {
    // Implement lazy loading for charts that are not immediately visible
    const chartContainers = document.querySelectorAll('.chart-container');
    
    if ('IntersectionObserver' in window) {
        const chartObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const chartCanvas = entry.target.querySelector('canvas[data-lazy]');
                    if (chartCanvas) {
                        loadLazyChart(chartCanvas);
                        chartObserver.unobserve(entry.target);
                    }
                }
            });
        }, {
            rootMargin: '50px'
        });
        
        chartContainers.forEach(container => {
            const lazyChart = container.querySelector('canvas[data-lazy]');
            if (lazyChart) {
                chartObserver.observe(container);
            }
        });
    }
}

function loadLazyChart(canvas) {
    const chartType = canvas.dataset.chartType;
    const chartData = canvas.dataset.chartData;
    
    if (chartType && chartData && window[chartData]) {
        initializeCustomChart(canvas, chartType, window[chartData]);
        canvas.removeAttribute('data-lazy');
    }
}

/**
 * =================================================================
 * TOOLTIPS AND ACCESSIBILITY
 * =================================================================
 */

function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

function initializeAccessibility() {
    // Add ARIA labels to interactive elements
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach((card, index) => {
        card.setAttribute('role', 'button');
        card.setAttribute('tabindex', '0');
        card.setAttribute('aria-label', `Métrica ${index + 1}: Ver detalles`);
    });
    
    // Add keyboard support for interactive elements
    const interactiveElements = document.querySelectorAll('.metric-card, .variable-card');
    interactiveElements.forEach(element => {
        element.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.click();
            }
        });
    });
}

/**
 * =================================================================
 * PRINT AND EXPORT FUNCTIONALITY
 * =================================================================
 */

function setupPrintHandling() {
    // Optimize charts for printing
    window.addEventListener('beforeprint', function() {
        Object.values(chartInstances).forEach(chart => {
            if (chart && chart.options) {
                chart.options.animation = false;
                chart.update('none');
            }
        });
    });
    
    window.addEventListener('afterprint', function() {
        Object.values(chartInstances).forEach(chart => {
            if (chart && chart.options) {
                chart.options.animation = { duration: 1000 };
                chart.update();
            }
        });
    });
}

function handlePrint() {
    window.print();
}

function handleExport() {
    // Implement export functionality
    const reportData = gatherReportData();
    downloadAsJSON(reportData, 'reporte-simulacion.json');
}

function gatherReportData() {
    const data = {
        timestamp: new Date().toISOString(),
        report: {
            title: document.querySelector('.report-header-title')?.textContent || 'Reporte',
            parameters: [],
            metrics: [],
            variables: []
        }
    };
    
    // Gather parameters
    document.querySelectorAll('.parameter-item').forEach(item => {
        const label = item.querySelector('.parameter-label')?.textContent;
        const value = item.querySelector('.parameter-value')?.textContent;
        if (label && value) {
            data.report.parameters.push({ label, value });
        }
    });
    
    // Gather metrics
    document.querySelectorAll('.metric-card').forEach(card => {
        const label = card.querySelector('.metric-card-label')?.textContent;
        const value = card.querySelector('.metric-card-value')?.textContent;
        if (label && value) {
            data.report.metrics.push({ label, value });
        }
    });
    
    return data;
}

function downloadAsJSON(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * =================================================================
 * ERROR HANDLING
 * =================================================================
 */

window.addEventListener('error', function(event) {
    console.error('JavaScript Error in Report Overview:', event.error);
    
    // Show user-friendly error message
    showErrorNotification('Ha ocurrido un error inesperado. Algunos elementos pueden no funcionar correctamente.');
});

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'alert alert-warning alert-dismissible fade show position-fixed';
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
    notification.innerHTML = `
        <i class="ri-error-warning-line me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

/**
 * =================================================================
 * CLEANUP
 * =================================================================
 */

window.addEventListener('beforeunload', function() {
    // Cleanup chart instances
    Object.values(chartInstances).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    
    // Clear any intervals or timeouts
    // (if any were set up)
});

/**
 * =================================================================
 * HELPER FUNCTIONS
 * =================================================================
 */

function closeExpandedSections() {
    document.querySelectorAll('.expanded').forEach(element => {
        element.classList.remove('expanded');
    });
}

function handleTableNavigation(event) {
    // Implement keyboard navigation for tables
    const currentRow = event.target.closest('tr');
    const table = event.target.closest('table');
    
    if (!currentRow || !table) return;
    
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const currentIndex = rows.indexOf(currentRow);
    
    let newIndex = currentIndex;
    
    switch (event.key) {
        case 'ArrowUp':
            newIndex = Math.max(0, currentIndex - 1);
            event.preventDefault();
            break;
        case 'ArrowDown':
            newIndex = Math.min(rows.length - 1, currentIndex + 1);
            event.preventDefault();
            break;
        default:
            return;
    }
    
    if (newIndex !== currentIndex && rows[newIndex]) {
        rows[newIndex].focus();
        rows[newIndex].click();
    }
}