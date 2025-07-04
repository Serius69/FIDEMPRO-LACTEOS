/**
 * Questionary List Management
 * Enhanced JavaScript functionality for questionary list page
 */

class QuestionaryListManager {
    constructor() {
        this.tooltips = [];
        this.currentTourStep = 0;
        this.tourSteps = [];
        this.init();
    }

    /**
     * Initialize the questionary list functionality
     */
    init() {
        this.initializeTooltips();
        this.setupEventListeners();
        this.initializeFilters();
        this.checkFirstVisit();
    }

    /**
     * Initialize Bootstrap tooltips
     */
    initializeTooltips() {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
            this.tooltips = Array.from(tooltipTriggerList).map(tooltipTriggerEl => {
                return new bootstrap.Tooltip(tooltipTriggerEl, {
                    delay: { show: 500, hide: 100 },
                    animation: true
                });
            });
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Filter toggle
        const filterToggle = document.getElementById('filter-active');
        if (filterToggle) {
            filterToggle.addEventListener('change', (e) => this.handleFilterToggle(e));
        }

        // Search functionality (if search input exists)
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => this.handleSearch(e), 300);
            });
        }

        // Row click handlers
        this.setupRowClickHandlers();

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    /**
     * Handle filter toggle for active/inactive questionnaires
     */
    handleFilterToggle(event) {
        const showOnlyActive = event.target.checked;
        const rows = document.querySelectorAll('tbody tr');
        let visibleCount = 0;

        rows.forEach(row => {
            const statusBadge = row.querySelector('.status-badge');
            if (statusBadge) {
                const isActive = statusBadge.classList.contains('bg-success');
                const shouldShow = !showOnlyActive || isActive;
                
                row.style.display = shouldShow ? '' : 'none';
                if (shouldShow) visibleCount++;

                // Add animation
                if (shouldShow) {
                    row.style.opacity = '0';
                    row.style.transform = 'translateY(-10px)';
                    setTimeout(() => {
                        row.style.transition = 'all 0.3s ease';
                        row.style.opacity = '1';
                        row.style.transform = 'translateY(0)';
                    }, 50);
                }
            }
        });

        this.updateFilterResults(visibleCount, showOnlyActive);
        this.saveFilterPreference(showOnlyActive);
    }

    /**
     * Update filter results display
     */
    updateFilterResults(count, showOnlyActive) {
        // Update any result counters if they exist
        const resultCounter = document.querySelector('.filter-results');
        if (resultCounter) {
            const filterText = showOnlyActive ? 'activos' : 'todos';
            resultCounter.textContent = `Mostrando ${count} cuestionarios ${filterText}`;
        }
    }

    /**
     * Save filter preference to localStorage
     */
    saveFilterPreference(showOnlyActive) {
        localStorage.setItem('questionaryListFilter', showOnlyActive ? 'active' : 'all');
    }

    /**
     * Load filter preference from localStorage
     */
    loadFilterPreference() {
        const savedFilter = localStorage.getItem('questionaryListFilter');
        const filterToggle = document.getElementById('filter-active');
        
        if (filterToggle && savedFilter) {
            filterToggle.checked = savedFilter === 'active';
            filterToggle.dispatchEvent(new Event('change'));
        }
    }

    /**
     * Initialize filters with saved preferences
     */
    initializeFilters() {
        this.loadFilterPreference();
    }

    /**
     * Handle search functionality
     */
    handleSearch(event) {
        const searchTerm = event.target.value.toLowerCase().trim();
        const rows = document.querySelectorAll('tbody tr:not(.empty-row)');
        let visibleCount = 0;

        rows.forEach(row => {
            const questionaryName = row.querySelector('h5')?.textContent.toLowerCase() || '';
            const productName = row.cells[2]?.textContent.toLowerCase() || '';
            
            const matches = questionaryName.includes(searchTerm) || 
                           productName.includes(searchTerm);
            
            row.style.display = matches ? '' : 'none';
            if (matches) visibleCount++;
        });

        this.showSearchResults(visibleCount, searchTerm);
    }

    /**
     * Show search results
     */
    showSearchResults(count, searchTerm) {
        // Remove existing search result message
        const existingMessage = document.querySelector('.search-results-message');
        if (existingMessage) {
            existingMessage.remove();
        }

        if (searchTerm) {
            const message = document.createElement('div');
            message.className = 'search-results-message alert alert-info mb-3';
            message.innerHTML = `
                <i class="fa fa-search"></i> 
                Encontrados ${count} resultado(s) para "${searchTerm}"
                <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
            `;
            
            const tableContainer = document.querySelector('.table-responsive');
            if (tableContainer) {
                tableContainer.parentNode.insertBefore(message, tableContainer);
            }
        }
    }

    /**
     * Setup row click handlers for enhanced interaction
     */
    setupRowClickHandlers() {
        const rows = document.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            // Add hover effects
            row.addEventListener('mouseenter', () => {
                row.style.backgroundColor = '#f8f9fa';
                row.style.transform = 'scale(1.01)';
                row.style.transition = 'all 0.2s ease';
            });

            row.addEventListener('mouseleave', () => {
                row.style.backgroundColor = '';
                row.style.transform = '';
            });

            // Click to view (excluding action buttons)
            row.addEventListener('click', (e) => {
                if (!e.target.closest('.action-buttons')) {
                    const viewLink = row.querySelector('a[href*="result"]');
                    if (viewLink) {
                        window.location.href = viewLink.href;
                    }
                }
            });
        });
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + K for search focus
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Ctrl/Cmd + H for help/tutorial
        if ((event.ctrlKey || event.metaKey) && event.key === 'h') {
            event.preventDefault();
            this.showListTutorial();
        }

        // Escape to clear search
        if (event.key === 'Escape') {
            const searchInput = document.getElementById('search-input');
            if (searchInput && searchInput.value) {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            }
        }
    }

    /**
     * Show tutorial modal
     */
    showListTutorial() {
        const modal = document.getElementById('listTutorialModal');
        if (modal && typeof bootstrap !== 'undefined') {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        }
    }

    /**
     * Start interactive guided tour
     */
    startListTour() {
        // Close tutorial modal first
        const modal = document.getElementById('listTutorialModal');
        if (modal && typeof bootstrap !== 'undefined') {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) bsModal.hide();
        }

        this.setupTourSteps();
        this.createTourOverlay();
        this.currentTourStep = 0;
        
        setTimeout(() => this.showTourStep(0), 300);
    }

    /**
     * Setup tour steps configuration
     */
    setupTourSteps() {
        this.tourSteps = [
            {
                element: '.btn-primary',
                title: 'Crear Nuevo Cuestionario',
                content: 'Use este botón para iniciar un nuevo cuestionario cuando lo necesite.',
                position: 'bottom'
            },
            {
                element: '#filter-active',
                title: 'Filtrar Cuestionarios',
                content: 'Active o desactive este switch para mostrar solo cuestionarios activos o todos.',
                position: 'left'
            },
            {
                element: '.action-buttons',
                title: 'Acciones Disponibles',
                content: 'Cada cuestionario tiene tres acciones: Ver (azul), Editar (amarillo) y Eliminar (rojo).',
                position: 'left'
            },
            {
                element: '.status-badge',
                title: 'Estado del Cuestionario',
                content: 'Los badges indican si un cuestionario está activo (verde) o inactivo (rojo).',
                position: 'top'
            },
            {
                element: '.pagination',
                title: 'Navegación',
                content: 'Use estos controles para navegar entre páginas si tiene muchos cuestionarios.',
                position: 'top'
            }
        ];
    }

    /**
     * Create tour overlay
     */
    createTourOverlay() {
        let overlay = document.getElementById('tourOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'tutorial-overlay';
            overlay.id = 'tourOverlay';
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'block';
    }

    /**
     * Show specific tour step
     */
    showTourStep(index) {
        // Clear previous highlights and tooltips
        this.clearTourElements();

        if (index >= this.tourSteps.length) {
            this.endTour();
            return;
        }

        const step = this.tourSteps[index];
        const element = document.querySelector(step.element);

        if (element) {
            this.highlightElement(element);
            this.createTourTooltip(element, step, index);
            this.scrollToElement(element);
        } else {
            // Skip to next step if element not found
            this.nextTourStep();
        }
    }

    /**
     * Highlight tour element
     */
    highlightElement(element) {
        element.classList.add('tutorial-highlight');
    }

    /**
     * Create tour tooltip
     */
    createTourTooltip(element, step, index) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tutorial-tooltip';
        tooltip.innerHTML = `
            <h5>${step.title}</h5>
            <p>${step.content}</p>
            <div class="d-flex justify-content-between mt-3">
                <button class="btn btn-sm btn-secondary" onclick="questionaryList.endTour()">
                    <i class="fa fa-times"></i> Salir
                </button>
                <div>
                    ${index > 0 ? '<button class="btn btn-sm btn-outline-primary me-2" onclick="questionaryList.previousTourStep()"><i class="fa fa-chevron-left"></i> Anterior</button>' : ''}
                    <button class="btn btn-sm btn-primary" onclick="questionaryList.nextTourStep()">
                        ${index < this.tourSteps.length - 1 ? 'Siguiente <i class="fa fa-chevron-right"></i>' : 'Finalizar <i class="fa fa-check"></i>'}
                    </button>
                </div>
            </div>
            <div class="text-center mt-2">
                <small class="text-muted">Paso ${index + 1} de ${this.tourSteps.length}</small>
                <div class="progress mt-1" style="height: 4px;">
                    <div class="progress-bar" style="width: ${((index + 1) / this.tourSteps.length) * 100}%"></div>
                </div>
            </div>
        `;

        document.body.appendChild(tooltip);
        this.positionTooltip(tooltip, element, step.position);
    }

    /**
     * Position tooltip relative to element
     */
    positionTooltip(tooltip, element, position) {
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

        let top, left;

        switch(position) {
            case 'bottom':
                top = rect.bottom + scrollTop + 10;
                left = rect.left + scrollLeft + rect.width/2 - tooltipRect.width/2;
                break;
            case 'top':
                top = rect.top + scrollTop - tooltipRect.height - 10;
                left = rect.left + scrollLeft + rect.width/2 - tooltipRect.width/2;
                break;
            case 'left':
                top = rect.top + scrollTop + rect.height/2 - tooltipRect.height/2;
                left = rect.left + scrollLeft - tooltipRect.width - 10;
                break;
            case 'right':
                top = rect.top + scrollTop + rect.height/2 - tooltipRect.height/2;
                left = rect.right + scrollLeft + 10;
                break;
            default:
                top = rect.bottom + scrollTop + 10;
                left = rect.left + scrollLeft;
        }

        // Ensure tooltip stays within viewport
        const maxLeft = window.innerWidth - tooltipRect.width - 20;
        const maxTop = window.innerHeight + scrollTop - tooltipRect.height - 20;
        
        left = Math.max(20, Math.min(left, maxLeft));
        top = Math.max(scrollTop + 20, Math.min(top, maxTop));

        tooltip.style.top = top + 'px';
        tooltip.style.left = left + 'px';
    }

    /**
     * Scroll element into view
     */
    scrollToElement(element) {
        element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center',
            inline: 'nearest'
        });
    }

    /**
     * Go to next tour step
     */
    nextTourStep() {
        this.currentTourStep++;
        this.showTourStep(this.currentTourStep);
    }

    /**
     * Go to previous tour step
     */
    previousTourStep() {
        this.currentTourStep--;
        this.showTourStep(this.currentTourStep);
    }

    /**
     * Clear tour elements
     */
    clearTourElements() {
        // Remove highlights
        document.querySelectorAll('.tutorial-highlight').forEach(el => {
            el.classList.remove('tutorial-highlight');
        });

        // Remove tooltips
        document.querySelectorAll('.tutorial-tooltip').forEach(el => {
            el.remove();
        });
    }

    /**
     * End the tour
     */
    endTour() {
        this.clearTourElements();
        
        const overlay = document.getElementById('tourOverlay');
        if (overlay) {
            overlay.remove();
        }

        this.showSuccessMessage('¡Tour completado! Ya conoce todas las funciones de la lista.');
        localStorage.setItem('listTutorialCompleted', 'true');
    }

    /**
     * Check if this is user's first visit
     */
    checkFirstVisit() {
        const hasSeenTutorial = localStorage.getItem('listTutorialShown');
        if (!hasSeenTutorial) {
            setTimeout(() => {
                this.showListTutorial();
                localStorage.setItem('listTutorialShown', 'true');
            }, 1000);
        }
    }

    /**
     * Show success message
     */
    showSuccessMessage(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 end-0 m-3 success-alert';
        alert.style.zIndex = '9999';
        alert.innerHTML = `
            <i class="fa fa-check-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    /**
     * Export functionality (placeholder for future implementation)
     */
    exportToCSV() {
        const rows = document.querySelectorAll('tbody tr:not([style*="display: none"])');
        let csv = 'Cuestionario,Producto,Fecha Creación,Última Actualización,Estado\n';

        rows.forEach(row => {
            const cells = row.cells;
            if (cells.length > 1) {
                const questionary = cells[1].textContent.trim();
                const product = cells[2].textContent.trim();
                const dateCreated = cells[3].textContent.trim();
                const dateUpdated = cells[4].textContent.trim();
                const status = cells[5].textContent.trim();

                csv += `"${questionary}","${product}","${dateCreated}","${dateUpdated}","${status}"\n`;
            }
        });

        this.downloadCSV(csv, 'cuestionarios.csv');
    }

    /**
     * Download CSV file
     */
    downloadCSV(csv, filename) {
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    /**
     * Refresh the page data
     */
    refreshData() {
        const refreshBtn = document.querySelector('.btn-refresh');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Actualizando...';
            refreshBtn.disabled = true;
        }

        // Simulate refresh (in real app, this would be an AJAX call)
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }

    /**
     * Cleanup method
     */
    destroy() {
        // Dispose tooltips
        this.tooltips.forEach(tooltip => {
            if (tooltip.dispose) tooltip.dispose();
        });

        // Remove event listeners
        document.removeEventListener('keydown', this.handleKeyboardShortcuts);
        
        // Clear tour elements
        this.clearTourElements();
        
        const overlay = document.getElementById('tourOverlay');
        if (overlay) {
            overlay.remove();
        }
    }
}

// Global instance
let questionaryList;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    questionaryList = new QuestionaryListManager();
});

// Global functions for backward compatibility
function showListTutorial() {
    if (questionaryList) {
        questionaryList.showListTutorial();
    }
}

function startListTour() {
    if (questionaryList) {
        questionaryList.startListTour();
    }
}

// Export functions for potential use in other scripts
window.QuestionaryListManager = QuestionaryListManager;