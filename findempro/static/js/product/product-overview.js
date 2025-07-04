/**
 * Product Overview JavaScript Module
 * Handles pagination, animations, and product overview interactions
 */

class ProductOverviewManager {
    constructor() {
        this.currentPage = 1;
        this.isLoading = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAnimations();
        this.setupTooltips();
        this.setupPagination();
        this.setupLazyLoading();
    }

    setupEventListeners() {
        // Variable pagination events
        this.setupVariablePagination();
        
        // Card hover effects
        this.setupCardEffects();
        
        // Tab switching events
        this.setupTabEvents();
        
        // Modal events
        this.setupModalEvents();
    }

    setupVariablePagination() {
        const paginationLinks = document.querySelectorAll('.pagination-link');
        paginationLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                if (page && !this.isLoading) {
                    this.loadVariablesPage(page);
                }
            });
        });
    }

    loadVariablesPage(page) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoadingState();
        
        const url = new URL(window.location.href);
        url.searchParams.set('page', page);
        
        fetch(url.toString(), {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            this.updateVariablesContent(html);
            this.currentPage = parseInt(page);
            this.updateURL(page);
        })
        .catch(error => {
            console.error('Error loading variables page:', error);
            this.showErrorMessage('Error al cargar las variables. Por favor, intente nuevamente.');
        })
        .finally(() => {
            this.isLoading = false;
            this.hideLoadingState();
        });
    }

    updateVariablesContent(html) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        const newVariablesGrid = doc.querySelector('.variables-grid');
        const newPagination = doc.querySelector('.variables-pagination');
        
        const currentVariablesGrid = document.querySelector('.variables-grid');
        const currentPagination = document.querySelector('.variables-pagination');
        
        if (newVariablesGrid && currentVariablesGrid) {
            // Fade out current content
            currentVariablesGrid.style.opacity = '0';
            
            setTimeout(() => {
                currentVariablesGrid.innerHTML = newVariablesGrid.innerHTML;
                currentVariablesGrid.style.opacity = '1';
                
                // Update pagination if exists
                if (newPagination && currentPagination) {
                    currentPagination.innerHTML = newPagination.innerHTML;
                }
                
                // Re-setup event listeners for new content
                this.setupVariablePagination();
                this.setupCardEffects();
                this.setupAnimations();
            }, 200);
        }
    }

    updateURL(page) {
        const url = new URL(window.location.href);
        url.searchParams.set('page', page);
        window.history.replaceState({}, '', url.toString());
    }

    showLoadingState() {
        const variablesGrid = document.querySelector('.variables-grid');
        if (variablesGrid) {
            variablesGrid.style.position = 'relative';
            
            // Create loading overlay
            const loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'loading-overlay';
            loadingOverlay.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p class="mt-2 text-muted">Cargando variables...</p>
                </div>
            `;
            
            variablesGrid.appendChild(loadingOverlay);
        }
    }

    hideLoadingState() {
        const loadingOverlay = document.querySelector('.loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }

    setupCardEffects() {
        // Area cards hover effects
        const areaCards = document.querySelectorAll('.area-card');
        areaCards.forEach(card => {
            this.setupCardHoverEffect(card);
        });

        // Variable cards hover effects
        const variableCards = document.querySelectorAll('.variable-card');
        variableCards.forEach(card => {
            this.setupCardHoverEffect(card);
        });

        // Simulation cards hover effects
        const simulationCards = document.querySelectorAll('.simulation-card');
        simulationCards.forEach(card => {
            this.setupCardHoverEffect(card);
        });

        // Report items hover effects
        const reportItems = document.querySelectorAll('.report-item');
        reportItems.forEach(item => {
            this.setupCardHoverEffect(item);
        });
    }

    setupCardHoverEffect(card) {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-2px)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });
    }

    setupAnimations() {
        // Setup intersection observer for animations
        if ('IntersectionObserver' in window) {
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };

            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('fade-in');
                        observer.unobserve(entry.target);
                    }
                });
            }, observerOptions);

            // Observe cards for animation
            const animatableElements = document.querySelectorAll(
                '.area-card, .variable-card, .simulation-card, .report-item'
            );
            
            animatableElements.forEach((el, index) => {
                el.style.animationDelay = `${index * 0.1}s`;
                observer.observe(el);
            });
        }
    }

    setupTabEvents() {
        const tabLinks = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabLinks.forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const targetId = e.target.getAttribute('href');
                
                if (targetId === '#product-variable') {
                    // Variables tab activated - trigger animations
                    setTimeout(() => {
                        this.setupAnimations();
                    }, 100);
                }
            });
        });
    }

    setupModalEvents() {
        // Handle area modal events
        const areaModal = document.getElementById('addOrUpdateArea');
        if (areaModal) {
            areaModal.addEventListener('hidden.bs.modal', () => {
                this.resetModalForm('areaForm');
            });
        }

        // Handle product modal events
        const productModal = document.getElementById('addOrUpdateProduct');
        if (productModal) {
            productModal.addEventListener('hidden.bs.modal', () => {
                this.resetModalForm('productForm');
            });
        }
    }

    setupTooltips() {
        // Initialize Bootstrap tooltips
        if (window.bootstrap && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    }

    setupPagination() {
        // Enhanced pagination with keyboard navigation
        document.addEventListener('keydown', (e) => {
            const activeTab = document.querySelector('.nav-link.active[href="#product-variable"]');
            if (!activeTab) return;

            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                e.preventDefault();
                const direction = e.key === 'ArrowLeft' ? 'prev' : 'next';
                this.navigatePage(direction);
            }
        });
    }

    navigatePage(direction) {
        const paginationLinks = document.querySelectorAll('.pagination-link');
        const currentPageLink = document.querySelector('.page-item.active .page-link');
        
        if (!currentPageLink) return;

        let targetPage;
        if (direction === 'prev') {
            const prevLink = document.querySelector('.pagination-link[data-page="' + (this.currentPage - 1) + '"]');
            if (prevLink) {
                targetPage = this.currentPage - 1;
            }
        } else {
            const nextLink = document.querySelector('.pagination-link[data-page="' + (this.currentPage + 1) + '"]');
            if (nextLink) {
                targetPage = this.currentPage + 1;
            }
        }

        if (targetPage) {
            this.loadVariablesPage(targetPage);
        }
    }

    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        const src = img.dataset.src;
                        
                        if (src) {
                            img.style.backgroundImage = `url(${src})`;
                            img.classList.remove('loading-skeleton');
                            observer.unobserve(img);
                        }
                    }
                });
            });

            // Observe images with data-src
            const lazyImages = document.querySelectorAll('[data-src]');
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }

    resetModalForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            
            // Clear validation classes
            const inputs = form.querySelectorAll('.form-control, .form-select');
            inputs.forEach(input => {
                input.classList.remove('is-valid', 'is-invalid');
            });
            
            // Clear alerts
            const alerts = form.querySelectorAll('.alert');
            alerts.forEach(alert => {
                alert.remove();
            });
        }
    }

    showErrorMessage(message) {
        if (window.Swal) {
            Swal.fire({
                title: 'Error',
                text: message,
                icon: 'error',
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 5000,
                timerProgressBar: true
            });
        } else {
            // Fallback notification
            const notification = document.createElement('div');
            notification.className = 'alert alert-danger alert-dismissible fade show position-fixed';
            notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }
    }

    showSuccessMessage(message) {
        if (window.Swal) {
            Swal.fire({
                title: 'Éxito',
                text: message,
                icon: 'success',
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true
            });
        }
    }

    // Area Management Functions
    loadAreaDetails(areaId) {
        if (!areaId) {
            console.error('No area ID provided');
            return;
        }

        this.showModalLoading('addOrUpdateArea');

        fetch(`/area/get_details/${areaId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                this.populateAreaForm(data);
                this.hideModalLoading('addOrUpdateArea');
            })
            .catch(error => {
                console.error('Error loading area details:', error);
                this.hideModalLoading('addOrUpdateArea');
                this.showErrorMessage('No se pudieron cargar los detalles del área');
            });
    }

    populateAreaForm(data) {
        // Populate area form fields
        const fields = ['area_name', 'area_description'];
        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            const dataKey = fieldId.replace('area_', '');
            if (field && data[dataKey] !== undefined) {
                field.value = data[dataKey] || '';
            }
        });

        // Update modal title
        const modalTitle = document.getElementById('addOrUpdateAreaLabel');
        if (modalTitle) {
            modalTitle.textContent = 'Actualizar Área';
        }
    }

    showModalLoading(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const modalBody = modal.querySelector('.modal-body');
            if (modalBody) {
                modalBody.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <p class="mt-2 text-muted">Cargando datos...</p>
                    </div>
                `;
            }
        }
    }

    hideModalLoading(modalId) {
        // This would typically restore the original modal content
        // Implementation depends on how the modal is structured
        console.log(`Hide loading for modal: ${modalId}`);
    }

    // Report Management
    downloadReport(reportId) {
        if (!reportId) {
            console.error('No report ID provided');
            return;
        }

        // Show loading state
        const downloadBtn = document.querySelector(`[data-report-id="${reportId}"]`);
        if (downloadBtn) {
            const originalContent = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<i class="ri-loader-4-line spinner"></i>';
            downloadBtn.disabled = true;

            setTimeout(() => {
                downloadBtn.innerHTML = originalContent;
                downloadBtn.disabled = false;
            }, 2000);
        }

        // Trigger download
        window.location.href = `/reports/download/${reportId}/`;
    }

    // Statistics and Metrics
    updateStatistics() {
        // Update any dynamic statistics if needed
        const areaCount = document.querySelectorAll('.area-card').length;
        const variableCount = document.querySelectorAll('.variable-card').length;
        const simulationCount = document.querySelectorAll('.simulation-card').length;

        console.log(`Statistics - Areas: ${areaCount}, Variables: ${variableCount}, Simulations: ${simulationCount}`);
    }

    // Utility Functions
    debounce(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    throttle(func, limit) {
        let lastFunc;
        let lastRan;
        return function(...args) {
            if (!lastRan) {
                func(...args);
                lastRan = Date.now();
            } else {
                clearTimeout(lastFunc);
                lastFunc = setTimeout(() => {
                    if ((Date.now() - lastRan) >= limit) {
                        func(...args);
                        lastRan = Date.now();
                    }
                }, limit - (Date.now() - lastRan));
            }
        };
    }

    // Cleanup
    destroy() {
        // Remove event listeners and clean up resources
        console.log('ProductOverviewManager destroyed');
    }
}

// Enhanced Error Handling
class ErrorHandler {
    static handle(error, context = 'Unknown') {
        console.error(`[ProductOverviewManager] ${context}:`, error);
        
        const userMessage = this.getUserFriendlyMessage(error);
        this.showNotification(userMessage);
    }

    static getUserFriendlyMessage(error) {
        if (error.name === 'NetworkError' || error.message.includes('fetch')) {
            return 'Error de conexión. Por favor, verifique su conexión a internet.';
        }
        
        if (error.status === 404) {
            return 'El recurso solicitado no fue encontrado.';
        }
        
        if (error.status >= 500) {
            return 'Error del servidor. Por favor, intente nuevamente más tarde.';
        }
        
        return 'Ha ocurrido un error inesperado. Por favor, intente nuevamente.';
    }

    static showNotification(message) {
        if (window.Swal) {
            Swal.fire({
                title: 'Error',
                text: message,
                icon: 'error',
                confirmButtonText: 'OK'
            });
        } else {
            alert(message);
        }
    }
}

// Global Functions for backward compatibility
let productOverviewManager;

function loadAreaDetails(areaId) {
    if (productOverviewManager) {
        productOverviewManager.loadAreaDetails(areaId);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        productOverviewManager = new ProductOverviewManager();
        
        // Setup additional styles for loading overlay
        const style = document.createElement('style');
        style.textContent = `
            .loading-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255, 255, 255, 0.9);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 100;
            }
            
            .loading-spinner {
                text-align: center;
            }
            
            .spinner {
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        console.log('Product Overview Manager initialized successfully');
    } catch (error) {
        ErrorHandler.handle(error, 'Initialization');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (productOverviewManager) {
        productOverviewManager.destroy();
    }
});