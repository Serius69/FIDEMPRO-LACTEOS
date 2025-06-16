// Validation Charts Component

// Global variables for validation charts
let validationPrecisionChart = null;
let validationSummaryChart = null;
let currentChartType = 'bar';

// Initialize charts when validation tab is shown
document.addEventListener('DOMContentLoaded', function() {
    const validationTab = document.getElementById('validation-tab');
    if (validationTab) {
        validationTab.addEventListener('shown.bs.tab', function (e) {
            // Destroy existing charts if they exist
            if (validationPrecisionChart) {
                validationPrecisionChart.destroy();
            }
            if (validationSummaryChart) {
                validationSummaryChart.destroy();
            }
            
            // Initialize charts
            initializeValidationPrecisionChart();
            initializeValidationSummaryChart();
        });
    }
});

function initializeValidationPrecisionChart() {
    const ctx = document.getElementById('validationPrecisionChart');
    if (!ctx) return;
    
    // Prepare data from table
    const tableRows = document.querySelectorAll('#validationDetailTable tbody tr');
    const labels = [];
    const errorData = [];
    const colors = [];
    
    tableRows.forEach(row => {
        const day = row.querySelector('td:first-child').textContent;
        const errorCell = row.querySelector('td:nth-child(7) span');
        if (errorCell) {
            const errorValue = parseFloat(errorCell.textContent);
            
            labels.push(`Día ${day}`);
            errorData.push(errorValue);
            
            // Assign color based on error
            if (errorValue < 10) {
                colors.push('rgba(40, 167, 69, 0.8)'); // Green
            } else if (errorValue < 20) {
                colors.push('rgba(255, 193, 7, 0.8)'); // Yellow
            } else {
                colors.push('rgba(220, 53, 69, 0.8)'); // Red
            }
        }
    });
    
    // Chart configuration
    const config = {
        type: currentChartType,
        data: {
            labels: labels,
            datasets: [{
                label: 'Error Porcentual (%)',
                data: errorData,
                backgroundColor: currentChartType === 'line' ? 'rgba(54, 162, 235, 0.2)' : colors,
                borderColor: currentChartType === 'line' ? 'rgba(54, 162, 235, 1)' : colors.map(c => c.replace('0.8', '1')),
                borderWidth: currentChartType === 'line' ? 2 : 1,
                tension: currentChartType === 'line' ? 0.4 : 0,
                fill: currentChartType === 'line' ? true : false,
                pointBackgroundColor: currentChartType === 'line' ? colors : undefined,
                pointBorderColor: currentChartType === 'line' ? colors.map(c => c.replace('0.8', '1')) : undefined,
                pointRadius: currentChartType === 'line' ? 4 : 0,
                pointHoverRadius: currentChartType === 'line' ? 6 : 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Distribución de Error Porcentual por Día de Simulación',
                    font: {
                        size: 16
                    }
                },
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Error: ${context.parsed.y.toFixed(2)}%`;
                        },
                        afterLabel: function(context) {
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
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Días de Simulación'
                    },
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 20
                    }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            }
        }
    };
    
    validationPrecisionChart = new Chart(ctx, config);
}

function initializeValidationSummaryChart() {
    const ctx = document.getElementById('validationSummaryChart');
    if (!ctx) return;
    
    // Get data from global variables (these should be set in the template)
    const preciseCount = parseInt(ctx.dataset.preciseCount || 0);
    const acceptableCount = parseInt(ctx.dataset.acceptableCount || 0);
    const inaccurateCount = parseInt(ctx.dataset.inaccurateCount || 0);
    
    const data = {
        labels: ['Precisa (<10%)', 'Aceptable (10-20%)', 'Inexacta (>20%)'],
        datasets: [{
            data: [preciseCount, acceptableCount, inaccurateCount],
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
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
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
    
    validationSummaryChart = new Chart(ctx, config);
}

// Toggle chart type
window.toggleValidationChartType = function() {
    currentChartType = currentChartType === 'bar' ? 'line' : 'bar';
    if (validationPrecisionChart) {
        validationPrecisionChart.destroy();
        initializeValidationPrecisionChart();
    }
};

// Download validation chart
window.downloadValidationChart = function() {
    if (!validationPrecisionChart) return;
    
    const url = validationPrecisionChart.toBase64Image();
    const link = document.createElement('a');
    link.download = 'distribucion_precision_' + new Date().getTime() + '.png';
    link.href = url;
    link.click();
};

// Show variable details
window.showVariableDetails = function(variableName) {
    const modal = new bootstrap.Modal(document.getElementById('variableDetailsModal'));
    const modalContent = document.getElementById('variableDetailsContent');
    
    if (!modalContent) return;
    
    // Generate modal content
    modalContent.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6>Información de la Variable</h6>
                <dl class="row">
                    <dt class="col-6">Código:</dt>
                    <dd class="col-6">${variableName}</dd>
                    <dt class="col-6">Descripción:</dt>
                    <dd class="col-6">Variable del modelo</dd>
                    <dt class="col-6">Unidad:</dt>
                    <dd class="col-6">--</dd>
                    <dt class="col-6">Tipo:</dt>
                    <dd class="col-6">Endógena</dd>
                </dl>
            </div>
            <div class="col-md-6">
                <h6>Estadísticas de Validación</h6>
                <dl class="row">
                    <dt class="col-6">Error Promedio:</dt>
                    <dd class="col-6">
                        <span class="badge bg-success">
                            -- %
                        </span>
                    </dd>
                    <dt class="col-6">Días Válidos:</dt>
                    <dd class="col-6">--</dd>
                    <dt class="col-6">Veredicto:</dt>
                    <dd class="col-6">--</dd>
                </dl>
            </div>
        </div>
        <hr>
        <div class="row">
            <div class="col-12">
                <canvas id="variableDetailChart" height="150"></canvas>
            </div>
        </div>
    `;
    
    modal.show();
    
    // Create detail chart after modal is shown
    setTimeout(() => {
        createVariableDetailChart(variableName);
    }, 200);
};

// Create variable detail chart
function createVariableDetailChart(variableName) {
    const ctx = document.getElementById('variableDetailChart');
    if (!ctx) return;
    
    // Sample data - in real implementation, this would come from server
    const days = Array.from({length: 30}, (_, i) => `Día ${i + 1}`);
    const realValues = Array.from({length: 30}, () => Math.random() * 100 + 50);
    const simulatedValues = Array.from({length: 30}, () => Math.random() * 100 + 50);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: days,
            datasets: [{
                label: 'Valor Real',
                data: realValues,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                tension: 0.4
            }, {
                label: 'Valor Simulado',
                data: simulatedValues,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: `Evolución de ${variableName}`
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Valor'
                    }
                }
            }
        }
    });
}