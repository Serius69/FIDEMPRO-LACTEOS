/**
 * Product List JavaScript Module
 * Handles tutorial system, filtering, search, and product management
 */

class ProductListManager {
    constructor() {
        this.tutorialSteps = [
            {
                title: "Paso 1: Filtrar por Negocio",
                content: "Use este menú para filtrar los productos por negocio. Puede ver todos los productos o solo los de un negocio específico.",
                element: "#business-select"
            },
            {
                title: "Paso 2: Buscar Productos", 
                content: "Use la barra de búsqueda para encontrar productos específicos por nombre, descripción o negocio.",
                element: "#search-input"
            },
            {
                title: "Paso 3: Crear Nuevo Producto",
                content: "Haga clic en este botón para crear un nuevo producto. Se abrirá un formulario donde podrá ingresar todos los detalles.",
                element: "#createProductBtn"
            },
            {
                title: "Paso 4: Tarjetas de Producto",
                content: "Cada tarjeta muestra información del producto. Puede ver detalles, editar o eliminar usando el menú de tres puntos.",
                element: ".product-card"
            },
            {
                title: "Paso 5: Acciones del Producto",
                content: "Use estas opciones para: Vista (ver detalles completos), Editar (modificar información), Eliminar (borrar el producto).",
                element: ".product-menu"
            }
        ];
        
        this.currentStep = 1;
        this.tutorialActive = false;
        this.originalDropdownState = null;
        this.searchTimeout = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeTooltips();
        this.setupCardAnimations();
        this.setupSearchHighlighting();
        this.checkAutoTutorial();
        this.setupLazyLoading();
    }

    setupEventListeners() {
        // Tutorial events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.tutorialActive) {
                this.endTutorial();
            }
        });

        // Tutorial overlay click
        const overlay = document.getElementById('tutorialOverlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.endTutorial();
                }
            });
        }

        // Search functionality
        this.setupSearchEvents();
        
        // Filter events
        this.setupFilterEvents();
        
        // Product management events
        this.setupProductEvents();
        
        // Form submission events
        this.setupFormEvents();
    }

    setupSearchEvents() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    if (e.target.value.length >= 3 || e.target.value.length === 0) {
                        this.submitFilterForm();
                    }
                }, 500);
            });

            // Auto-focus if has value
            if (searchInput.value) {
                searchInput.focus();
            }
        }
    }

    setupFilterEvents() {
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.addEventListener('change', () => {
                this.submitFilterForm();
            });
        }
    }

    setupProductEvents() {
        // Delete product events
        document.addEventListener('click', (e) => {
            if (e.target.closest('.delete-product')) {
                e.preventDefault();
                const productId = e.target.closest('.delete-product').dataset.productId;
                this.setupDeleteForm(productId);
            }
        });

        // Create product button reset
        const createBtn = document.getElementById('createProductBtn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.resetProductForm();
            });
        }
    }

    setupFormEvents() {
        const applyFiltersBtn = document.getElementById('apply-filters');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', (e) => {
                this.handleFormSubmission(e.target);
            });
        }
    }

    // Tutorial System
    startTutorial() {
        if (localStorage.getItem('productListTutorialCompleted') === 'true') {
            if (!confirm('¿Desea ver el tutorial nuevamente?')) {
                return;
            }
        }
        
        this.tutorialActive = true;
        this.currentStep = 1;
        document.getElementById('tutorialOverlay').style.display = 'block';
        this.showStep(1);
    }

    showStep(step) {
        // Hide all tooltips
        document.querySelectorAll('.tutorial-tooltip').forEach(tooltip => {
            tooltip.style.display = 'none';
        });

        // Remove spotlight from all elements
        document.querySelectorAll('.tutorial-spotlight').forEach(el => {
            el.classList.remove('tutorial-spotlight');
        });
        
        const stepData = this.tutorialSteps[step - 1];
        if (!stepData) {
            this.endTutorial();
            return;
        }

        const element = document.querySelector(stepData.element);
        if (element) {
            element.classList.add('tutorial-spotlight');
            this.positionTooltip(`step${step}Tooltip`, element);
        } else if (step === 4) {
            // If no products, skip to end
            this.endTutorial();
            return;
        }

        // Special handling for dropdown step
        if (step === 5) {
            this.handleDropdownStep(element);
        }
    }

    positionTooltip(tooltipId, targetElement) {
        const tooltip = document.getElementById(tooltipId);
        if (!tooltip || !targetElement) return;

        const rect = targetElement.getBoundingClientRect();
        
        tooltip.style.display = 'block';
        
        setTimeout(() => {
            const tooltipRect = tooltip.getBoundingClientRect();
            
            // Position tooltip
            if (rect.top > window.innerHeight / 2) {
                tooltip.style.top = (rect.top + window.scrollY - tooltipRect.height - 10) + 'px';
            } else {
                tooltip.style.top = (rect.bottom + window.scrollY + 10) + 'px';
            }
            
            const leftPosition = Math.max(10, Math.min(
                rect.left + (rect.width / 2) - (tooltipRect.width / 2),
                window.innerWidth - tooltipRect.width - 10
            ));
            
            tooltip.style.left = leftPosition + 'px';
        }, 10);
    }

    handleDropdownStep(menuElement) {
        if (menuElement) {
            const dropdown = menuElement.nextElementSibling;
            this.originalDropdownState = dropdown ? dropdown.classList.contains('show') : false;
            
            if (!this.originalDropdownState && menuElement.click) {
                menuElement.click();
            }
        }
    }

    nextStep(step) {
        this.currentStep = step;
        this.showStep(step);
    }

    endTutorial() {
        this.tutorialActive = false;
        document.getElementById('tutorialOverlay').style.display = 'none';
        
        document.querySelectorAll('.tutorial-tooltip').forEach(tooltip => {
            tooltip.style.display = 'none';
        });
        
        document.querySelectorAll('.tutorial-spotlight').forEach(el => {
            el.classList.remove('tutorial-spotlight');
        });
        
        // Close any dropdowns opened by tutorial
        if (this.originalDropdownState === false) {
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                const dropdownToggle = menu.previousElementSibling;
                if (dropdownToggle && dropdownToggle.classList.contains('product-menu')) {
                    dropdownToggle.click();
                }
            });
        }
        
        this.originalDropdownState = null;
        localStorage.setItem('productListTutorialCompleted', 'true');
    }

    checkAutoTutorial() {
        if (!localStorage.getItem('productListTutorialCompleted')) {
            const hasProducts = document.querySelectorAll('.product-card').length > 0;
            if (!hasProducts) {
                setTimeout(() => {
                    this.startTutorial();
                }, 1500);
            }
        }
    }

    // Search and Filter Functions
    submitFilterForm() {
        const form = document.getElementById('filterForm');
        if (form) {
            form.submit();
        }
    }

    clearSearch() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.value = '';
            this.submitFilterForm();
        }
    }

    handleFormSubmission(button) {
        const originalText = button.innerHTML;
        
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Aplicando...';
        button.disabled = true;
        
        // Re-enable button after timeout (fallback)
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
    }

    // Search highlighting
    setupSearchHighlighting() {
        const searchQuery = this.getSearchQuery();
        if (searchQuery) {
            this.highlightSearchResults(searchQuery);
        }
    }

    getSearchQuery() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('search') || '';
    }

    highlightSearchResults(searchTerm) {
        if (!searchTerm) return;

        const productCards = document.querySelectorAll('.product-card');
        productCards.forEach(card => {
            const textElements = card.querySelectorAll('.product-name, .product-description, .product-business');
            textElements.forEach(element => {
                const text = element.textContent;
                if (text.toLowerCase().includes(searchTerm.toLowerCase())) {
                    const regex = new RegExp(`(${this.escapeRegExp(searchTerm)})`, 'gi');
                    element.innerHTML = text.replace(regex, '<span class="search-highlight">$1</span>');
                }
            });
        });
    }

    escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Product Management
    setupDeleteForm(productId) {
        const deleteForm = document.getElementById('deleteProductForm');
        if (deleteForm) {
            deleteForm.action = `/product/delete/${productId}/`;
        }
    }

    resetProductForm() {
        const form = document.getElementById('productForm');
        if (form) {
            form.reset();
            const productIdField = document.getElementById('product_id');
            if (productIdField) {
                productIdField.value = '';
            }
            
            const modalTitle = document.getElementById('addOrUpdateProductLabel');
            if (modalTitle) {
                modalTitle.textContent = 'Crear Producto';
            }
            
            const productImage = document.getElementById('product_logo_img');
            if (productImage) {
                productImage.src = '/static/images/default-product.png';
            }
        }
    }

    // Animation and Visual Effects
    setupCardAnimations() {
        const cards = document.querySelectorAll('.product-card');
        cards.forEach((card, index) => {
            card.style.setProperty('--animation-delay', `${index * 0.1}s`);
            card.classList.add('fade-in');
        });
    }

    // Tooltip Management
    initializeTooltips() {
        if (window.bootstrap && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    }

    // Lazy Loading
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const images = document.querySelectorAll('img[data-src]');
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('loading-skeleton');
                        observer.unobserve(img);
                    }
                });
            });

            images.forEach(img => imageObserver.observe(img));
        }
    }

    // Error Handling
    handleError(error, context = 'Unknown') {
        console.error(`[ProductListManager] ${context}:`, error);
        
        const userMessage = this.getUserFriendlyErrorMessage(error);
        this.showNotification(userMessage, 'error');
    }

    getUserFriendlyErrorMessage(error) {
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

    showNotification(message, type = 'info') {
        if (window.Swal) {
            Swal.fire({
                title: type === 'error' ? 'Error' : 'Información',
                text: message,
                icon: type === 'error' ? 'error' : 'info',
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 5000,
                timerProgressBar: true
            });
        } else {
            // Fallback notification
            this.showFallbackNotification(message, type);
        }
    }

    showFallbackNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : 'info'} alert-dismissible fade show position-fixed`;
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
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Remove event listeners would go here if we stored references
        console.log('ProductListManager destroyed');
    }
}

// Enhanced Product Form Manager (from product-modal.html integration)
class ProductFormManager {
    constructor() {
        this.modal = document.getElementById('addOrUpdateProduct');
        this.form = document.getElementById('productForm');
        this.modalTitle = document.getElementById('addOrUpdateProductLabel');
        this.productIdField = document.getElementById('product_id');
        this.imagePreview = document.getElementById('product_logo_img');
        this.imageInput = document.getElementById('product_image_src');
        this.submitBtn = document.getElementById('submitProductBtn');
        this.submitBtnText = document.getElementById('submitBtnText');
        this.charCountElement = document.getElementById('charCount');
        this.modalLoading = document.getElementById('modalLoading');
        this.modalContent = document.getElementById('modalContent');
        this.formAlerts = document.getElementById('formAlerts');
        
        this.init();
    }
    
    init() {
        if (!this.form) return; // Modal not present on this page
        
        this.setupImageHandler();
        this.setupFormHandler();
        this.setupModalHandlers();
        this.setupValidation();
    }
    
    setupImageHandler() {
        if (this.imageInput) {
            this.imageInput.addEventListener('change', (e) => {
                this.handleImagePreview(e);
            });
        }
    }
    
    setupFormHandler() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => {
                this.submitForm(e);
            });
        }
    }
    
    setupModalHandlers() {
        if (this.modal) {
            this.modal.addEventListener('hidden.bs.modal', () => {
                this.resetForm();
            });
            
            this.modal.addEventListener('show.bs.modal', () => {
                this.prepareModal();
            });
        }
    }
    
    setupValidation() {
        const descriptionField = document.getElementById('product_description');
        if (descriptionField && this.charCountElement) {
            descriptionField.addEventListener('input', () => {
                this.updateCharCount();
            });
        }
        
        // Real-time validation
        const fields = ['product_name', 'product_description'];
        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('blur', () => this.validateField(field));
                field.addEventListener('input', () => this.clearFieldError(field));
            }
        });
    }
    
    handleImagePreview(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        // Validate file size (2MB max)
        if (file.size > 2 * 1024 * 1024) {
            this.showAlert('error', 'La imagen no debe superar los 2MB');
            e.target.value = '';
            return;
        }
        
        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        if (!allowedTypes.includes(file.type)) {
            this.showAlert('error', 'Solo se permiten archivos JPG y PNG');
            e.target.value = '';
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            if (this.imagePreview) {
                this.imagePreview.src = e.target.result;
                this.imagePreview.style.display = 'block';
            }
        };
        reader.readAsDataURL(file);
    }
    
    updateCharCount() {
        const descriptionField = document.getElementById('product_description');
        if (!descriptionField || !this.charCountElement) return;
        
        const currentLength = descriptionField.value.length;
        this.charCountElement.textContent = currentLength;
        
        // Change color based on length
        if (currentLength > 450) {
            this.charCountElement.className = 'text-danger';
        } else if (currentLength > 400) {
            this.charCountElement.className = 'text-warning';
        } else {
            this.charCountElement.className = 'text-muted';
        }
    }
    
    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';
        
        switch (field.id) {
            case 'product_name':
                if (value.length < 3) {
                    isValid = false;
                    errorMessage = 'El nombre debe tener al menos 3 caracteres';
                } else if (value.length > 100) {
                    isValid = false;
                    errorMessage = 'El nombre no puede superar los 100 caracteres';
                }
                break;
            case 'product_description':
                if (value.length < 10) {
                    isValid = false;
                    errorMessage = 'La descripción debe tener al menos 10 caracteres';
                } else if (value.length > 500) {
                    isValid = false;
                    errorMessage = 'La descripción no puede superar los 500 caracteres';
                }
                break;
        }
        
        if (!isValid) {
            this.showFieldError(field, errorMessage);
        } else {
            this.clearFieldError(field);
        }
        
        return isValid;
    }
    
    showFieldError(field, message) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        const feedback = field.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
            feedback.textContent = message;
        }
    }
    
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        if (field.value.trim()) {
            field.classList.add('is-valid');
        } else {
            field.classList.remove('is-valid');
        }
    }
    
    showAlert(type, message) {
        if (!this.formAlerts) return;
        
        const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
        this.formAlerts.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="ri-${type === 'error' ? 'error-warning' : 'check-double'}-line me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        this.formAlerts.style.display = 'block';
    }
    
    hideAlert() {
        if (this.formAlerts) {
            this.formAlerts.style.display = 'none';
            this.formAlerts.innerHTML = '';
        }
    }
    
    prepareModal() {
        if (this.modalLoading) this.modalLoading.style.display = 'none';
        if (this.modalContent) this.modalContent.style.display = 'block';
        this.hideAlert();
    }
    
    submitForm(e) {
        e.preventDefault();
        
        // Validate all fields
        if (!this.validateAllFields()) {
            this.showAlert('error', 'Por favor, corrija los errores en el formulario');
            return;
        }
        
        const isUpdate = this.productIdField && this.productIdField.value !== '';
        const formData = new FormData(this.form);
        
        // Show loading state
        if (this.submitBtn) {
            this.submitBtn.disabled = true;
            this.submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Guardando...';
        }
        
        const url = isUpdate 
            ? `/product/${this.productIdField.value}/update/` 
            : '/product/create/';
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal
                if (window.bootstrap && this.modal) {
                    bootstrap.Modal.getInstance(this.modal).hide();
                }
                
                // Show success message
                this.showSuccessMessage(isUpdate, data);
            } else {
                this.handleFormErrors(data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            this.showAlert('error', 'Ocurrió un error al procesar la solicitud. Por favor, intente nuevamente.');
        })
        .finally(() => {
            this.resetSubmitButton();
        });
    }
    
    validateAllFields() {
        const nameField = document.getElementById('product_name');
        const descriptionField = document.getElementById('product_description');
        const typeField = document.getElementById('product_type');
        const businessField = document.getElementById('product_fk_business');
        
        let isValid = true;
        
        if (nameField && !nameField.value.trim()) {
            this.showFieldError(nameField, 'El nombre es requerido');
            isValid = false;
        } else if (nameField) {
            isValid = this.validateField(nameField) && isValid;
        }
        
        if (descriptionField && !descriptionField.value.trim()) {
            this.showFieldError(descriptionField, 'La descripción es requerida');
            isValid = false;
        } else if (descriptionField) {
            isValid = this.validateField(descriptionField) && isValid;
        }
        
        if (typeField && !typeField.value) {
            this.showFieldError(typeField, 'Debe seleccionar un tipo de producto');
            isValid = false;
        }
        
        if (businessField && !businessField.value) {
            this.showFieldError(businessField, 'Debe seleccionar un negocio');
            isValid = false;
        }
        
        return isValid;
    }
    
    handleFormErrors(data) {
        if (data.errors) {
            for (const field in data.errors) {
                const fieldElement = document.getElementById(`product_${field}`) || document.getElementById(field);
                if (fieldElement) {
                    this.showFieldError(fieldElement, data.errors[field][0]);
                }
            }
        }
        
        let errorMessage = 'Se encontraron errores en el formulario';
        if (data.errors && data.errors.general) {
            errorMessage = data.errors.general[0];
        }
        
        this.showAlert('error', errorMessage);
    }
    
    showSuccessMessage(isUpdate, data) {
        if (window.Swal) {
            Swal.fire({
                title: isUpdate ? 'Producto Actualizado' : 'Producto Creado',
                text: isUpdate ? 'El producto ha sido actualizado con éxito' : 'El producto ha sido creado con éxito',
                icon: 'success',
                confirmButtonText: 'OK',
                timer: 3000,
                timerProgressBar: true
            }).then((result) => {
                if (result.isConfirmed || result.isDismissed) {
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.reload();
                    }
                }
            });
        } else {
            alert(isUpdate ? 'Producto actualizado con éxito' : 'Producto creado con éxito');
            window.location.reload();
        }
    }
    
    resetSubmitButton() {
        if (this.submitBtn && this.submitBtnText) {
            this.submitBtn.disabled = false;
            this.submitBtn.innerHTML = `<i class="ri-save-3-line align-bottom me-1"></i> ${this.submitBtnText.textContent}`;
        }
    }
    
    resetForm() {
        if (this.form) {
            this.form.reset();
        }
        
        if (this.imagePreview) {
            this.imagePreview.src = '/static/images/default-product.png';
        }
        
        this.hideAlert();
        
        // Clear validation classes
        if (this.form) {
            const inputs = this.form.querySelectorAll('.form-control');
            inputs.forEach(input => {
                input.classList.remove('is-invalid', 'is-valid');
            });
        }
        
        // Reset character count
        if (this.charCountElement) {
            this.charCountElement.textContent = '0';
            this.charCountElement.className = 'text-muted';
        }
    }
    
    edit(productId) {
        if (!productId) {
            console.error('No product ID provided');
            return;
        }
        
        this.modalTitle.textContent = 'Actualizar Producto';
        this.productIdField.value = productId;
        this.submitBtnText.textContent = 'Actualizar Producto';
        
        // Show loading
        if (this.modalLoading) this.modalLoading.style.display = 'block';
        if (this.modalContent) this.modalContent.style.display = 'none';
        
        // Load product data
        fetch(`/product/get_details/${productId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                this.populateForm(data);
                
                if (this.modalLoading) this.modalLoading.style.display = 'none';
                if (this.modalContent) this.modalContent.style.display = 'block';
            })
            .catch(error => {
                console.error('Error loading product details:', error);
                if (this.modalLoading) this.modalLoading.style.display = 'none';
                if (this.modalContent) this.modalContent.style.display = 'block';
                
                this.showAlert('error', 'No se pudieron cargar los detalles del producto');
            });
    }
    
    populateForm(data) {
        const fields = ['product_name', 'product_type', 'product_fk_business', 'product_description'];
        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            const dataKey = fieldId.replace('product_', '');
            if (field && data[dataKey] !== undefined) {
                field.value = data[dataKey] || '';
            }
        });
        
        // Update character count
        this.updateCharCount();
        
        // Show image if exists
        if (data.image_src && data.image_src !== 'None' && this.imagePreview) {
            this.imagePreview.src = data.image_src;
        }
    }
}

// Global Functions for backward compatibility
let productListManager;
let productFormManager;

function startTutorial() {
    if (productListManager) {
        productListManager.startTutorial();
    }
}

function nextStep(step) {
    if (productListManager) {
        productListManager.nextStep(step);
    }
}

function endTutorial() {
    if (productListManager) {
        productListManager.endTutorial();
    }
}

function clearSearch() {
    if (productListManager) {
        productListManager.clearSearch();
    }
}

function loadProductDetails(productId) {
    if (productFormManager) {
        productFormManager.edit(productId);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        productListManager = new ProductListManager();
        productFormManager = new ProductFormManager();
        
        console.log('Product List Manager initialized successfully');
    } catch (error) {
        console.error('Error initializing Product List Manager:', error);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (productListManager) {
        productListManager.destroy();
    }
});