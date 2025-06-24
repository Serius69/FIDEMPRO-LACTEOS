/**
 * Validation Charts - Gráficos específicos para la pestaña de validación
 */
class ValidationCharts {
    constructor() {
        this.charts = new Map();
        this.currentChartType = 'bar';
        this.validationData = null;
        this.init();
    }

    init() {
        this.setupTabActivation();
        this.loadValidationData();
    }

    setupTabActivation() {
        // Inicializar gráficos cuando se muestre la pestaña de validación
        const validationTab = document.getElementById('validation-tab');
        if (validationTab) {
            validationTab.addEventListener('shown.bs.tab', () => {
                this.initializeValidationCharts();
            });
        }
    }

    loadValidationData() {
        // Cargar datos de validación desde las tablas
        this.validationData = this.extractValidationData();
    }

    extractValidationData() {
        const data = {
            daily: [],
            summary: {
                precise: 0,
                acceptable: 0,
                inaccurate: 0,
                total: 0
            },
            metrics: {}
        };

        // Extraer datos diarios de la tabla
        const tableRows = document.querySelectorAll('#validationDetailTable tbody tr.validation-row');
        tableRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 7) {
                const day = parseInt(cells[0].textContent.trim());
                const errorSpan = cells[6].querySelector('span');
                const errorValue = errorSpan ? parseFloat(errorSpan.textContent.replace('%', '')) : 0;
                
                data.daily.push({
                    day: day,
                    error: errorValue,
                    status: errorValue < 10 ? 'precise' : errorValue < 20 ? 'acceptable' : 'inaccurate'
                });

                // Contar por categorías
                if (errorValue < 10) data.summary.precise++;
                else if (errorValue < 20) data.summary.acceptable++;
                else data.summary.inaccurate++;
            }
        });

        data.summary.total = data.daily.length;

        // Extraer métricas generales
        const metricsElements = document.querySelectorAll('.validation-kpi-value');
        metricsElements.forEach((element, index) => {
            const label = element.nextElementSibling?.textContent || `Metric ${index}`;
            data.metrics[label] = parseFloat(element.textContent.replace(/[^\d.-]/g, '')) || 0;
        });

        return data;
    }

    initializeValidationCharts() {
        // Destruir gráficos existentes
        this.destroyExistingCharts();
        
        // Crear nuevos gráficos
        this.createPrecisionChart();
        this.createSummaryChart();
        this.createVariablesComparisonChart();
    }

    destroyExistingCharts() {
        this.charts.forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts.clear();
    }

    createPrecisionChart() {
        const ctx = document.getElementById('validationPrecisionChart');
        if (!ctx || !this.validationData) return;

        const data = this.validationData.daily;
        const labels = data.map(item => `Día ${item.day}`);
        const errorData = data.map(item => item.error);
        const colors = data.map(item => {
            if (item.error < 10) return 'rgba(40, 167, 69, 0.8)'; // Verde
            else if (item.error < 20) return 'rgba(255, 193, 7, 0.8)'; // Amarillo
            else return 'rgba(220, 53, 69, 0.8)'; // Rojo
        });

        const config = {
            type: this.currentChartType,
            data: {
                labels: labels,
                datasets: [{
                    label: 'Error Porcentual (%)',
                    data: errorData,
                    backgroundColor: this.currentChartType === 'line' ? 'rgba(54, 162, 235, 0.2)' : colors,
                    borderColor: this.currentChartType === 'line' ? 'rgba(54, 162, 235, 1)' : colors.map(c => c.replace('0.8', '1')),
                    borderWidth: this.currentChartType === 'line' ? 2 : 1,
                    tension: this.currentChartType === 'line' ? 0.4 : 0,
                    fill: this.currentChartType === 'line',
                    pointBackgroundColor: this.currentChartType === 'line' ? colors : undefined,
                    pointBorderColor: this.currentChartType === 'line' ? colors.map(c => c.replace('0.8', '1')) : undefined,
                    pointRadius: this.currentChartType === 'line' ? 4 : 0,
                    pointHoverRadius: this.currentChartType === 'line' ? 6 : 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Distribución de Error Porcentual por Día de Simulación',
                        font: { size: 16 }
                    },
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => `Error: ${context.parsed.y.toFixed(2)}%`,
                            afterLabel: (context) => {
                                const error = context.parsed.y;
                                if (error < 10) return 'Veredicto: ✅ Precisa';
                                else if (error < 20) return 'Veredicto: ⚠️ Aceptable';
                                else return 'Veredicto: ❌ Inexacta';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Error Porcentual (%)'
                        },
                        ticks: {
                            callback: (value) => value + '%'
                        },
                        grid: {
                            color: (context) => {
                                if (context.tick.value === 10) return 'rgba(255, 193, 7, 0.3)';
                                if (context.tick.value === 20) return 'rgba(220, 53, 69, 0.3)';
                                return 'rgba(0, 0, 0, 0.1)';
                            },
                            lineWidth: (context) => {
                                if (context.tick.value === 10 || context.tick.value === 20) return 2;
                                return 1;
                            }
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Días de Simulación'
                        },
                        ticks: {
                            maxTicksLimit: 20,
                            callback: function(value, index) {
                                if (labels.length > 50) {
                                    return index % 5 === 0 ? this.getLabelForValue(value) : '';
                                }
                                return this.getLabelForValue(value);
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                }
            }
        };

        const chart = new Chart(ctx, config);
        this.charts.set('precision', chart);
    }

    createSummaryChart() {
        const ctx = document.getElementById('validationSummaryChart');
        if (!ctx || !this.validationData) return;

        const summary = this.validationData.summary;
        const data = {
            labels: ['Precisa (<10%)', 'Aceptable (10-20%)', 'Inexacta (>20%)'],
            datasets: [{
                data: [summary.precise, summary.acceptable, summary.inaccurate],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ],
                borderColor: [
                    'rgba(40, 167, 69, 1)',
                    'rgba(255, 193, 7, 1)',
                    'rgba(220, 53, 69, 1)'
                ],
                borderWidth: 2
            }]
        };

        const config = {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} días (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        };

        const chart = new Chart(ctx, config);
        this.charts.set('summary', chart);
    }

    createVariablesComparisonChart() {
        const ctx = document.getElementById('variablesComparisonChart');
        if (!ctx) return;

        // Datos de ejemplo para variables clave
        const keyVariables = ['IT', 'GT', 'TPV', 'TPPRO', 'CTAI', 'GO'];
        const labels = [];
        const realData = [];
        const simulatedData = [];

        // Obtener datos de la tabla de validación de variables
        const rows = document.querySelectorAll('#variablesValidationTable tbody tr');
        rows.forEach(row => {
            const varName = row.querySelector('td:first-child strong')?.textContent;
            if (keyVariables.includes(varName)) {
                labels.push(varName);
                const realValue = parseFloat(row.querySelector('td:nth-child(4)')?.textContent.replace(/[^\d.-]/g, '') || 0);
                const simValue = parseFloat(row.querySelector('td:nth-child(5)')?.textContent.replace(/[^\d.-]/g, '') || 0);
                
                // Normalizar valores para mejor visualización
                const maxValue = Math.max(realValue, simValue);
                const normalizedReal = maxValue > 0 ? (realValue / maxValue) * 100 : 0;
                const normalizedSim = maxValue > 0 ? (simValue / maxValue) * 100 : 0;
                
                realData.push(normalizedReal);
                simulatedData.push(normalizedSim);
            }
        });

        if (labels.length === 0) return;

        const config = {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Valores Reales',
                    data: realData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(54, 162, 235, 1)'
                }, {
                    label: 'Valores Simulados',
                    data: simulatedData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(255, 99, 132, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Comparación de Variables Clave (Normalizado)'
                    },
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return context.dataset.label + ': ' + context.parsed.r.toFixed(1) + '%';
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            callback: (value) => value + '%'
                        }
                    }
                }
            }
        };

        const chart = new Chart(ctx, config);
        this.charts.set('variables', chart);
    }

    // Cambiar tipo de gráfico de precisión
    toggleChartType() {
        this.currentChartType = this.currentChartType === 'bar' ? 'line' : 'bar';
        const chart = this.charts.get('precision');
        if (chart) {
            chart.destroy();
            this.createPrecisionChart();
        }
    }

    // Descargar gráfico específico
    downloadChart(chartName) {
        const chart = this.charts.get(chartName);
        if (!chart) return;
        
        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = `validacion_${chartName}_${new Date().getTime()}.png`;
        link.href = url;
        link.click();
        
        if (window.chartManager) {
            window.chartManager.showNotification('Gráfico descargado exitosamente', 'success');
        }
    }

    // Actualizar datos y refrescar gráficos
    refreshCharts() {
        this.loadValidationData();
        this.initializeValidationCharts();
    }
}

// Instancia global
window.validationCharts = new ValidationCharts();

// Funciones globales para compatibilidad
window.toggleValidationChartType = () => window.validationCharts.toggleChartType();
window.downloadValidationChart = (chartName = 'precision') => window.validationCharts.downloadChart(chartName);