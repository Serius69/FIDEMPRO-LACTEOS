/**
 * Business List Management
 * Handles tutorial system and business operations with SEPARATED CRUD functions
 * Compatible with Django backend views and URLs
 */

class BusinessListManager {
    constructor() {
        this.tutorialSteps = [
            {
                element: '#createBusinessBtn',
                title: '¡Bienvenido a tu Dashboard de Negocios!',
                content: 'Este es el botón principal para crear un nuevo negocio. Haz clic aquí cuando quieras agregar un negocio a tu lista.',
                position: 'bottom'
            },
            {
                element: '.business-card:first-child',
                title: 'Tarjetas de Negocio',
                content: 'Cada negocio se muestra en una tarjeta con su imagen, nombre, descripción y datos importantes.',
                position: 'top'
            },
            {
                element: '.business-card:first-child .dropdown',
                title: 'Menú de Opciones',
                content: 'Haz clic en los tres puntos para ver las opciones disponibles: Ver detalles, Editar o Eliminar.',
                position: 'left'
            },
            {
                element: '.pagination',
                title: 'Navegación por Páginas',
                content: 'Si tienes muchos negocios, puedes navegar entre páginas usando estos controles.',
                position: 'top'
            },
            {
                element: '#startTutorial',
                title: '¡Tutorial Completado!',
                content: 'Has completado el tutorial. Puedes volver a verlo en cualquier momento haciendo clic en "Iniciar Tutorial".',
                position: 'bottom'
            }
        ];

        this.currentStep = 0;
        this.modalManager = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAutoTutorial();
        this.waitForModalManager();
    }

    waitForModalManager() {
        // Wait for modal manager to be available
        const checkManager = () => {
            if (window.businessModalManager) {
                this.modalManager = window.businessModalManager;
                console.log('✅ Modal manager connected to list manager');
            } else {
                setTimeout(checkManager, 100);
            }
        };
        checkManager();
    }

    bindEvents() {
        // Tutorial events
        document.getElementById('startTutorial')?.addEventListener('click', () => this.startTutorial());
        document.getElementById('tutorialPrev')?.addEventListener('click', () => this.previousStep());
        document.getElementById('tutorialNext')?.addEventListener('click', () => this.nextStep());
        document.getElementById('tutorialOverlay')?.addEventListener('click', () => this.endTutorial());

        // Keyboard events
        document.addEventListener('keydown', (e) => this.handleKeydown(e));

        // Business operations
        this.bindBusinessEvents();

        // Window events
        window.addEventListener('resize', () => this.handleResize());
    }

    bindBusinessEvents() {
        // ================================
        // CREATE BUSINESS EVENT
        // ================================
        document.addEventListener('click', (e) => {
            const createButton = e.target.closest('#createBusinessBtn, [data-bs-target="#addOrUpdateBusiness"]');
            if (createButton && !createButton.classList.contains('edit-business')) {
                e.preventDefault();
                console.log('➕ CREATE business clicked');
                this.handleCreateBusiness();
            }
        });

        // ================================
        // UPDATE BUSINESS EVENT
        // ================================
        document.addEventListener('click', (e) => {
            const editButton = e.target.closest('.edit-business');
            if (editButton) {
                e.preventDefault();
                const businessId = editButton.dataset.businessId;
                console.log(`✏️ UPDATE business clicked for ID: ${businessId}`);
                this.handleUpdateBusiness(businessId);
            }
        });

        // ================================
        // DELETE BUSINESS EVENT (SOFT DELETE)
        // ================================
        document.addEventListener('click', (e) => {
            const deleteButton = e.target.closest('.delete-business');
            if (deleteButton) {
                e.preventDefault();
                const businessId = deleteButton.dataset.businessId;
                console.log(`🗑️ DELETE business clicked for ID: ${businessId}`);
                this.handleDeleteBusiness(businessId);
            }
        });

        // ================================
        // BUSINESS CARD INTERACTIONS
        // ================================
        document.querySelectorAll('.business-card').forEach(card => {
            this.enhanceBusinessCard(card);
        });
    }

    // ================================
    // SEPARATED CRUD OPERATIONS
    // ================================

    handleCreateBusiness() {
        console.log('🚀 Initiating CREATE business flow');
        
        if (this.modalManager) {
            this.modalManager.openCreateModal();
        } else {
            console.error('❌ Modal manager not available for CREATE');
            this.showToast('error', 'Error: Sistema no listo para crear negocio');
        }
    }

    handleUpdateBusiness(businessId) {
        console.log(`🚀 Initiating UPDATE business flow for ID: ${businessId}`);
        
        if (!businessId) {
            console.error('❌ No business ID provided for UPDATE');
            this.showToast('error', 'Error: ID de negocio no encontrado');
            return;
        }
        
        // Test simple directo primero
        console.log('🧪 Testing simple approach...');
        
        try {
            // Approach 1: Simple direct call
            if (window.simpleEditTest) {
                console.log('🔧 Using simpleEditTest function');
                window.simpleEditTest(businessId);
                return;
            }
            
            // Approach 2: Use modal manager if available
            if (this.modalManager) {
                console.log('🔧 Using modal manager');
                this.modalManager.openUpdateModal(businessId);
            } else if (window.businessModalManager) {
                console.log('🔧 Using global modal manager');
                window.businessModalManager.openUpdateModal(businessId);
            } else {
                // Approach 3: Direct implementation
                console.log('🔧 Using direct implementation');
                this.directEditImplementation(businessId);
            }
        } catch (error) {
            console.error('❌ All approaches failed:', error);
            this.showToast('error', `Error al iniciar edición: ${error.message}`);
        }
    }

    async directEditImplementation(businessId) {
        console.log(`🛠️ Direct edit implementation for ID: ${businessId}`);
        
        try {
            // Show loading
            this.showToast('info', 'Cargando datos del negocio...');
            
            // Fetch data
            const response = await fetch(`/business/api/details/${businessId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📋 Business data loaded:', data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update modal title and form action
            const modal = document.getElementById('addOrUpdateBusiness');
            const form = document.getElementById('businessForm');
            const modalTitle = document.getElementById('addOrUpdateBusinessLabel');
            const submitBtnText = document.getElementById('submitBtnText');
            const businessIdInput = document.getElementById('business_id');
            
            if (modalTitle) {
                modalTitle.innerHTML = '<i class="ri-edit-line me-2"></i>Editar Negocio';
            }
            
            if (submitBtnText) {
                submitBtnText.textContent = 'Actualizar Negocio';
            }
            
            if (form) {
                form.action = `/business/${businessId}/update/`;
            }
            
            if (businessIdInput) {
                businessIdInput.value = businessId;
            }
            
            // Populate form fields
            const nameInput = document.getElementById('id_name');
            const typeSelect = document.getElementById('id_type');
            const locationSelect = document.getElementById('id_location');
            const descriptionTextarea = document.getElementById('id_description');
            
            if (nameInput) {
                nameInput.value = data.name || '';
                console.log(`✅ Name populated: "${nameInput.value}"`);
            }
            
            if (typeSelect) {
                typeSelect.value = data.type || '';
                console.log(`✅ Type populated: "${typeSelect.value}"`);
            }
            
            if (locationSelect) {
                locationSelect.value = data.location || '';
                console.log(`✅ Location populated: "${locationSelect.value}"`);
            }
            
            if (descriptionTextarea) {
                descriptionTextarea.value = data.description || '';
                console.log(`✅ Description populated: "${descriptionTextarea.value}"`);
                
                // Update character count
                const descriptionCount = document.getElementById('descriptionCount');
                if (descriptionCount) {
                    descriptionCount.textContent = descriptionTextarea.value.length;
                }
            }
            
            // Handle image
            if (data.image_src && data.image_src !== '/static/images/business/business-dummy-img.webp') {
                const logoImg = document.getElementById('logo-img');
                const clearBtn = document.getElementById('clearImage');
                const placeholder = document.querySelector('.image-placeholder');
                
                if (logoImg) {
                    logoImg.src = data.image_src;
                    logoImg.style.display = 'block';
                }
                
                if (clearBtn) {
                    clearBtn.style.display = 'inline-block';
                }
                
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
            }
            
            // Show modal
            if (modal) {
                const modalInstance = new bootstrap.Modal(modal);
                modalInstance.show();
                console.log('✅ Edit modal shown successfully');
                this.showToast('success', 'Datos cargados correctamente');
            } else {
                throw new Error('Modal element not found');
            }
            
        } catch (error) {
            console.error('❌ Direct edit implementation failed:', error);
            this.showToast('error', `Error: ${error.message}`);
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    handleDeleteBusiness(businessId) {
        console.log(`🚀 Initiating DELETE business flow for ID: ${businessId}`);
        
        if (!businessId) {
            console.error('❌ No business ID provided for DELETE');
            this.showToast('error', 'Error: ID de negocio no encontrado');
            return;
        }
        
        if (this.modalManager) {
            this.modalManager.openDeleteModal(businessId);
        } else {
            console.error('❌ Modal manager not available for DELETE');
            this.showToast('error', 'Error: Sistema no listo para eliminar negocio');
        }
    }

    // ================================
    // BUSINESS CARD ENHANCEMENTS
    // ================================

    enhanceBusinessCard(card) {
        // Add focus management for accessibility
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const businessId = card.dataset.businessId;
                window.location.href = `/business/overview/${businessId}/`;
            }
        });

        // Add smooth hover effects
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-8px)';
            card.style.transition = 'transform 0.3s ease';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });

        // Add click to view functionality (excluding action buttons)
        card.addEventListener('click', (e) => {
            // Don't navigate if clicking on action buttons
            if (!e.target.closest('.dropdown, .btn, button, a')) {
                const businessId = card.dataset.businessId;
                window.location.href = `/business/overview/${businessId}/`;
            }
        });
    }

    // ================================
    // TUTORIAL SYSTEM
    // ================================

    checkAutoTutorial() {
        if (!localStorage.getItem('businessTutorialCompleted')) {
            setTimeout(() => this.startTutorial(), 1000);
        }
    }

    startTutorial() {
        this.currentStep = 0;
        const overlay = document.getElementById('tutorialOverlay');
        const indicator = document.getElementById('stepIndicator');
        
        if (overlay) overlay.style.display = 'block';
        if (indicator) indicator.style.display = 'block';
        
        this.showStep(this.currentStep);
    }

    showStep(stepIndex) {
        const step = this.tutorialSteps[stepIndex];
        const element = document.querySelector(step.element);
        
        if (!element) {
            // Skip to next step if element doesn't exist
            if (stepIndex < this.tutorialSteps.length - 1) {
                this.currentStep++;
                this.showStep(this.currentStep);
            } else {
                this.endTutorial();
            }
            return;
        }
        
        this.clearSpotlights();
        this.addSpotlight(element);
        this.updateTooltip(step, element);
        this.updateStepIndicator();
        this.scrollToElement(element);
    }

    clearSpotlights() {
        document.querySelectorAll('.tutorial-spotlight').forEach(el => {
            el.classList.remove('tutorial-spotlight');
        });
    }

    addSpotlight(element) {
        element.classList.add('tutorial-spotlight');
    }

    updateTooltip(step, element) {
        const tooltip = document.getElementById('tutorialTooltip');
        const title = document.getElementById('tutorialTitle');
        const content = document.getElementById('tutorialContent');
        const prevBtn = document.getElementById('tutorialPrev');
        const nextBtn = document.getElementById('tutorialNext');
        
        if (title) title.textContent = step.title;
        if (content) content.textContent = step.content;
        
        if (prevBtn) prevBtn.style.display = this.currentStep === 0 ? 'none' : 'block';
        if (nextBtn) nextBtn.textContent = this.currentStep === this.tutorialSteps.length - 1 ? 'Finalizar' : 'Siguiente';
        
        this.positionTooltip(tooltip, element, step.position);
        if (tooltip) tooltip.style.display = 'block';
    }

    positionTooltip(tooltip, element, position) {
        if (!tooltip || !element) return;
        
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let top, left;
        
        switch(position) {
            case 'top':
                top = rect.top - tooltipRect.height - 20;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'bottom':
                top = rect.bottom + 20;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'left':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.left - tooltipRect.width - 20;
                break;
            case 'right':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.right + 20;
                break;
        }
        
        // Keep tooltip within viewport
        top = Math.max(10, Math.min(window.innerHeight - tooltipRect.height - 10, top));
        left = Math.max(10, Math.min(window.innerWidth - tooltipRect.width - 10, left));
        
        tooltip.style.top = top + 'px';
        tooltip.style.left = left + 'px';
    }

    updateStepIndicator() {
        const dots = document.querySelectorAll('.step-dot');
        dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === this.currentStep);
        });
    }

    scrollToElement(element) {
        element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center',
            inline: 'center'
        });
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }

    nextStep() {
        if (this.currentStep < this.tutorialSteps.length - 1) {
            this.currentStep++;
            this.showStep(this.currentStep);
        } else {
            this.endTutorial();
        }
    }

    endTutorial() {
        const overlay = document.getElementById('tutorialOverlay');
        const tooltip = document.getElementById('tutorialTooltip');
        const indicator = document.getElementById('stepIndicator');
        
        if (overlay) overlay.style.display = 'none';
        if (tooltip) tooltip.style.display = 'none';
        if (indicator) indicator.style.display = 'none';
        
        this.clearSpotlights();
        localStorage.setItem('businessTutorialCompleted', 'true');
    }

    handleKeydown(e) {
        const overlay = document.getElementById('tutorialOverlay');
        if (overlay && overlay.style.display === 'block') {
            switch(e.key) {
                case 'Escape':
                    this.endTutorial();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousStep();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextStep();
                    break;
            }
        }
    }

    handleResize() {
        const tooltip = document.getElementById('tutorialTooltip');
        if (tooltip && tooltip.style.display === 'block') {
            const step = this.tutorialSteps[this.currentStep];
            const element = document.querySelector(step.element);
            if (element) {
                this.positionTooltip(tooltip, element, step.position);
            }
        }
    }

    // ================================
    // UTILITY METHODS
    // ================================

    showToast(type, message) {
        const toastContainer = this.getToastContainer();
        const toast = this.createToast(type, message);
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: type === 'error' ? 5000 : 3000
        });
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    getToastContainer() {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }

    createToast(type, message) {
        const toast = document.createElement('div');
        const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
        const icon = type === 'success' ? 'ri-check-line' : 'ri-error-warning-line';
        
        toast.className = `toast align-items-center text-white ${bgClass} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="${icon} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        return toast;
    }

    // ================================
    // SEARCH AND FILTER FUNCTIONALITY
    // ================================

    initializeSearch() {
        const searchInput = document.getElementById('businessSearch');
        if (searchInput) {
            let searchTimeout;
            
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.filterBusinesses(e.target.value);
                }, 300);
            });
        }
    }

    filterBusinesses(searchTerm) {
        const cards = document.querySelectorAll('.business-card');
        const term = searchTerm.toLowerCase().trim();
        let visibleCount = 0;
        
        cards.forEach(card => {
            const name = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
            const description = card.querySelector('.card-description')?.textContent.toLowerCase() || '';
            const location = card.querySelector('.metadata-item span:last-child')?.textContent.toLowerCase() || '';
            
            const matches = name.includes(term) || description.includes(term) || location.includes(term);
            
            if (matches || term === '') {
                card.style.display = 'block';
                this.animateElement(card, 'fadeIn');
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        this.updateEmptyState(visibleCount === 0);
    }

    updateEmptyState(isEmpty) {
        const container = document.getElementById('business-list');
        let searchEmptyState = container.querySelector('.search-empty-state');
        
        if (isEmpty && !searchEmptyState) {
            this.showSearchEmptyState();
        } else if (!isEmpty && searchEmptyState) {
            searchEmptyState.remove();
        }
    }

    showSearchEmptyState() {
        const container = document.getElementById('business-list');
        const emptyState = document.createElement('div');
        emptyState.className = 'col-12 search-empty-state';
        emptyState.innerHTML = `
            <div class="text-center py-5">
                <i class="ri-search-line" style="font-size: 4rem; color: #6c757d;"></i>
                <h3 class="mt-3">No se encontraron negocios</h3>
                <p class="text-muted">Intenta con otros términos de búsqueda.</p>
            </div>
        `;
        container.appendChild(emptyState);
    }

    animateElement(element, animation = 'fadeIn', duration = 300) {
        element.style.animation = `${animation} ${duration}ms ease-in-out`;
        
        setTimeout(() => {
            element.style.animation = '';
        }, duration);
    }

    // ================================
    // PUBLIC API METHODS
    // ================================

    refreshBusinessList() {
        console.log('🔄 Refreshing business list');
        window.location.reload();
    }

    getBusinessCount() {
        return document.querySelectorAll('.business-card').length;
    }

    getVisibleBusinessCount() {
        return document.querySelectorAll('.business-card[style*="display: block"], .business-card:not([style*="display: none"])').length;
    }

    // Check if system is ready for operations
    isSystemReady() {
        const checks = [
            document.getElementById('businessForm') !== null,
            document.getElementById('addOrUpdateBusiness') !== null,
            document.getElementById('removeBusinessModal') !== null,
            this.modalManager !== null
        ];

        const passed = checks.filter(check => check).length;
        console.log(`📊 System ready: ${passed}/${checks.length} checks passed`);
        
        return passed === checks.length;
    }
}

// ================================
// INITIALIZATION
// ================================

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const businessManager = new BusinessListManager();
    
    // Make it globally available for other scripts and debugging
    window.businessManager = businessManager;
    
    // Initialize search functionality
    businessManager.initializeSearch();
    
    console.log('✅ Business List Manager initialized');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BusinessListManager;
}