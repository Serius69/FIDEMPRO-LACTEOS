/**
 * Chart Manager - Manejo central de gráficos
 */
class ChartManager {
    constructor() {
        this.charts = new Map();
        this.currentChartData = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFullscreen();
    }

    setupEventListeners() {
        // Click en imágenes para abrir en pantalla completa
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('chart-image')) {
                const src = event.target.src;
                const alt = event.target.alt;
                const base64Data = src.split(',')[1];
                if (base64Data) {
                    this.openFullscreen(base64Data, alt);
                }
            }
        });

        // Cerrar modal con ESC
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.closeModals();
            }
        });
    }

    setupFullscreen() {
        // Configurar overlay de pantalla completa
        const overlay = document.getElementById('fullscreenOverlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.closeFullscreen();
                }
            });
        }
    }

    downloadChart(chartData, filename = 'grafico.png') {
        try {
            if (!chartData) {
                console.warn('No chart data provided for download');
                return;
            }
            
            const link = document.createElement('a');
            link.href = 'data:image/png;base64,' + chartData;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showNotification('Gráfico descargado exitosamente', 'success');
            console.log('Chart downloaded:', filename);
        } catch (error) {
            console.error('Error downloading chart:', error);
            this.showNotification('Error al descargar el gráfico', 'error');
        }
    }

    openFullscreen(chartData, title = 'Gráfico') {
        try {
            if (!chartData) {
                console.warn('No chart data provided for fullscreen');
                return;
            }
            
            const modal = document.getElementById('fullscreenModal');
            const modalTitle = document.getElementById('fullscreenModalTitle');
            const modalImage = document.getElementById('fullscreenModalImage');
            
            if (modal && modalTitle && modalImage) {
                modalTitle.textContent = title;
                modalImage.src = 'data:image/png;base64,' + chartData;
                modalImage.setAttribute('data-chart-data', chartData);
                this.currentChartData = chartData;
                
                if (typeof bootstrap !== 'undefined') {
                    new bootstrap.Modal(modal).show();
                } else {
                    modal.style.display = 'block';
                    modal.classList.add('show');
                }
            }
        } catch (error) {
            console.error('Error opening fullscreen:', error);
            this.showNotification('Error al abrir el gráfico en pantalla completa', 'error');
        }
    }

    closeFullscreen() {
        const overlay = document.getElementById('fullscreenOverlay');
        if (overlay) {
            overlay.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    closeModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            if (typeof bootstrap !== 'undefined') {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            } else {
                modal.style.display = 'none';
                modal.classList.remove('show');
            }
        });
    }

    downloadCurrentChart() {
        try {
            if (this.currentChartData) {
                const title = document.getElementById('fullscreenModalTitle').textContent;
                const filename = title.toLowerCase().replace(/\s+/g, '-') + '.png';
                this.downloadChart(this.currentChartData, filename);
            }
        } catch (error) {
            console.error('Error downloading current chart:', error);
            this.showNotification('Error al descargar el gráfico', 'error');
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 10000; min-width: 300px;';
        
        const icon = type === 'success' ? 'bx-check-circle' : 
                     type === 'error' ? 'bx-error' : 
                     'bx-info-circle';
        
        notification.innerHTML = `
            <i class="bx ${icon} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    // Método para crear gráficos Chart.js
    createChart(canvasId, config) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        // Destruir gráfico existente si existe
        if (this.charts.has(canvasId)) {
            this.charts.get(canvasId).destroy();
        }

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    // Destruir todos los gráficos
    destroyAllCharts() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
    }
}

// Exportar instancia global
window.chartManager = new ChartManager();

// Funciones globales para compatibilidad
window.downloadChart = (chartData, filename) => window.chartManager.downloadChart(chartData, filename);
window.openFullscreen = (chartData, title) => window.chartManager.openFullscreen(chartData, title);
window.closeFullscreen = () => window.chartManager.closeFullscreen();
window.downloadCurrentChart = () => window.chartManager.downloadCurrentChart();