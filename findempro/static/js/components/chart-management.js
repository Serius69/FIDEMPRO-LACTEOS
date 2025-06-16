// Charts Management Component

// Download chart functionality
window.downloadChart = function(imageData, filename) {
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${imageData}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('Gráfico descargado exitosamente', 'success');
};

// Variables for managing chart loading
let allCharts = [];
let loadedCharts = 0;
const CHARTS_PER_BATCH = 3;
let currentTypeFilter = '';

// Function to load initial charts
function loadInitialCharts() {
    const container = document.getElementById('chartsContainer');
    const loadedContainer = document.getElementById('loadedChartsContainer');
    
    if (container) container.style.display = 'none';
    if (loadedContainer) loadedContainer.style.display = 'block';
    
    // Sort by error descending to show critical ones first
    allCharts.sort((a, b) => b.error_pct - a.error_pct);
    
    loadMoreCharts();
}

// Function to load more charts
function loadMoreCharts() {
    const container = document.getElementById('chartsGrid');
    if (!container) return;
    
    const filteredCharts = currentTypeFilter 
        ? allCharts.filter(c => c.type === currentTypeFilter)
        : allCharts;
    
    const endIndex = Math.min(loadedCharts + CHARTS_PER_BATCH, filteredCharts.length);
    
    for (let i = loadedCharts; i < endIndex; i++) {
        const chartData = filteredCharts[i];
        const chartHtml = createChartCard(chartData);
        container.insertAdjacentHTML('beforeend', chartHtml);
        
        // Apply lazy loading to the image
        const imgElement = container.querySelector(`#chart-${chartData.variable}`);
        if (imgElement && 'IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            });
            imageObserver.observe(imgElement);
        }
    }
    
    loadedCharts = endIndex;
    
    // Update load more button
    const loadMoreContainer = document.getElementById('loadMoreContainer');
    const remaining = filteredCharts.length - loadedCharts;
    if (loadMoreContainer) {
        if (remaining > 0) {
            loadMoreContainer.style.display = 'block';
            const remainingCount = document.getElementById('remainingCount');
            if (remainingCount) remainingCount.textContent = `(${remaining} restantes)`;
        } else {
            loadMoreContainer.style.display = 'none';
        }
    }
    
    // Animate new charts
    animateNewCharts();
}

// Create chart card HTML
function createChartCard(chartData) {
    const statusClass = chartData.status === 'PRECISA' ? 'success' : 
                       chartData.status === 'ACEPTABLE' ? 'warning' : 'danger';
    
    return `
        <div class="col-lg-6 mb-4 chart-card" data-variable="${chartData.variable}" data-type="${chartData.type}">
            <div class="card h-100 shadow-sm">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-0">${chartData.variable}</h6>
                        <small class="text-muted">${chartData.description}</small>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-${statusClass}">
                            ${chartData.error_pct.toFixed(1)}% error
                        </span>
                    </div>
                </div>
                <div class="card-body p-2">
                    <div class="chart-wrapper position-relative">
                        <img id="chart-${chartData.variable}"
                             data-src="data:image/png;base64,${chartData.chart}" 
                             class="img-fluid validation-chart-img lazy" 
                             alt="Gráfico de ${chartData.variable}"
                             loading="lazy">
                        
                        <div class="chart-loading position-absolute top-50 start-50 translate-middle" style="display: none;">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Cargando...</span>
                            </div>
                        </div>
                        
                        <div class="chart-controls position-absolute top-0 end-0 p-2">
                            <button class="btn btn-sm btn-light" 
                                    onclick="expandChart('${chartData.variable}', '${chartData.chart}')"
                                    title="Expandir">
                                <i class="bx bx-expand"></i>
                            </button>
                            <button class="btn btn-sm btn-light" 
                                    onclick="downloadChart('${chartData.chart}', '${chartData.variable}_validation.png')"
                                    title="Descargar">
                                <i class="bx bx-download"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-footer bg-light">
                    <div class="row text-center small">
                        <div class="col-4">
                            <strong>Unidad:</strong><br>${chartData.unit}
                        </div>
                        <div class="col-4">
                            <strong>Días:</strong><br>${chartData.days_count}
                        </div>
                        <div class="col-4">
                            <strong>Cobertura:</strong><br>${chartData.coverage.toFixed(0)}%
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Animate chart entrance
function animateNewCharts() {
    const newCards = document.querySelectorAll('.chart-card:not(.animated)');
    newCards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('animated', 'fadeInUp');
        }, index * 100);
    });
}

// Filter charts by type
window.filterChartsByType = function() {
    const filter = document.getElementById('chartTypeFilter');
    if (!filter) return;
    
    currentTypeFilter = filter.value;
    
    // Reset and reload
    loadedCharts = 0;
    const chartsGrid = document.getElementById('chartsGrid');
    if (chartsGrid) chartsGrid.innerHTML = '';
    
    const loadedContainer = document.getElementById('loadedChartsContainer');
    if (loadedContainer && loadedContainer.style.display !== 'none') {
        loadMoreCharts();
    }
};

// Expand chart in modal or fullscreen
window.expandChart = function(variable, chartData) {
    openFullscreen(chartData, variable);
};

// Handle chart loading errors
document.addEventListener('error', function(e) {
    if (e.target.tagName === 'IMG' && e.target.classList.contains('validation-chart-img')) {
        e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KICA8cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+CiAgPHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkVycm9yIGNhcmdhbmRvIGdyw6FmaWNvPC90ZXh0Pgo8L3N2Zz4=';
        e.target.classList.remove('lazy');
        
        // Log error
        console.error('Failed to load chart for:', e.target.alt);
    }
}, true);