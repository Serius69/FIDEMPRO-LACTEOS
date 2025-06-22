/**
 * Product Modal JavaScript Module - CLEAN VERSION
 * Handles product creation, editing, and deletion modals
 */

class ProductModalManager {
    constructor() {
        this.modal = document.getElementById('addOrUpdateProduct');
        this.deleteModal = document.getElementById('removeProductModal');
        this.form = document.getElementById('productForm');
        this.deleteForm = document.getElementById('deleteProductForm');
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
        
        this.isSubmitting = false;
        this.validationRules = {
            name: { min: 3, max: 100, required: true },
            description: { min: 10, max: 1000, required: true },
            type: { required: true },
            fk_business: { required: true }
        };
        
        this.init();
    }

    init() {
        if (!this.form) return; // Modal not present on this page
        
        this.setupEventListeners();
        this.setupImageHandler();
        this.setupValidation();
        this.setupModalHandlers();
        this.setupDeleteModal();
    }

    // EVENT LISTENERS
    setupEventListeners() {
        // Form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmission();
            });
        }

        // Image upload
        if (this.imageInput) {
            this.imageInput.addEventListener('change', (e) => {
                this.handleImageUpload(e);
            });
        }

        // Character counter
        const descriptionField = document.getElementById('product_description');
        if (descriptionField) {
            descriptionField.addEventListener('input', () => {
                this.updateCharacterCount();
            });
        }

        // Real-time validation
        this.setupRealtimeValidation();
    }

    setupModalHandlers() {
        if (this.modal) {
            this.modal.addEventListener('show.bs.modal', () => {
                this.prepareModal();
            });
            
            this.modal.addEventListener('hidden.bs.modal', () => {
                this.resetForm();
            });
        }
    }

    setupDeleteModal() {
        if (this.deleteForm) {
            this.deleteForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleDeletion();
            });
        }
    }

    // IMAGE HANDLING
    setupImageHandler() {
        if (!this.imageInput || !this.imagePreview) return;

        // Drag and drop functionality
        const previewContainer = this.imagePreview.parentElement;
        
        previewContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            previewContainer.classList.add('drag-over');
        });

        previewContainer.addEventListener('dragleave', () => {
            previewContainer.classList.remove('drag-over');
        });

        previewContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            previewContainer.classList.remove('drag-over');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleImageFile(files[0]);
            }
        });
    }

    handleImageUpload(e) {
        const file = e.target.files[0];
        if (file) {
            this.handleImageFile(file);
        }
    }

    handleImageFile(file) {
        const validation = this.validateImageFile(file);
        if (!validation.isValid) {
            this.showAlert('error', validation.message);
            this.imageInput.value = '';
            return;
        }
        this.showImagePreview(file);
    }

    validateImageFile(file) {
        // File size validation (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            return { isValid: false, message: 'La imagen no debe superar los 5MB' };
        }

        // File type validation
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
        if (!allowedTypes.includes(file.type)) {
            return { isValid: false, message: 'Solo se permiten archivos JPG y PNG' };
        }

        return { isValid: true };
    }

    showImagePreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            this.imagePreview.src = e.target.result;
            this.imagePreview.classList.add('image-loaded');
            
            // Add animation
            this.imagePreview.style.opacity = '0';
            setTimeout(() => {
                this.imagePreview.style.opacity = '1';
            }, 100);
        };
        reader.readAsDataURL(file);
    }

    // VALIDATION
    setupValidation() {
        const fields = ['product_name', 'product_description', 'product_type', 'product_fk_business'];
        
        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('blur', () => this.validateField(field));
                field.addEventListener('input', () => this.clearFieldError(field));
            }
        });
    }

    setupRealtimeValidation() {
        const debouncedValidation = this.debounce((field) => {
            this.validateField(field);
        }, 500);

        const nameField = document.getElementById('product_name');
        const descriptionField = document.getElementById('product_description');

        if (nameField) {
            nameField.addEventListener('input', () => {
                if (nameField.value.length >= 3) {
                    debouncedValidation(nameField);
                }
            });
        }

        if (descriptionField) {
            descriptionField.addEventListener('input', () => {
                if (descriptionField.value.length >= 10) {
                    debouncedValidation(descriptionField);
                }
            });
        }
    }

    validateField(field) {
        const fieldName = field.name;
        const value = field.value.trim();
        const rules = this.validationRules[fieldName];
        
        if (!rules) return true;

        let isValid = true;
        let errorMessage = '';

        // Required validation
        if (rules.required && !value) {
            isValid = false;
            errorMessage = this.getRequiredMessage(fieldName);
        }
        // Length validation
        else if (value && rules.min && value.length < rules.min) {
            isValid = false;
            errorMessage = `Debe tener al menos ${rules.min} caracteres`;
        }
        else if (value && rules.max && value.length > rules.max) {
            isValid = false;
            errorMessage = `No puede superar los ${rules.max} caracteres`;
        }

        // Update field state
        if (isValid) {
            this.showFieldSuccess(field);
        } else {
            this.showFieldError(field, errorMessage);
        }

        return isValid;
    }

    getRequiredMessage(fieldName) {
        const messages = {
            name: 'El nombre del producto es requerido',
            description: 'La descripción es requerida',
            type: 'Debe seleccionar un tipo de producto',
            fk_business: 'Debe seleccionar un negocio'
        };
        return messages[fieldName] || 'Este campo es requerido';
    }

    showFieldError(field, message) {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        
        const feedback = field.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = message;
            feedback.style.display = 'block';
        }
    }

    showFieldSuccess(field) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        
        const feedback = field.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.style.display = 'none';
        }
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        
        const feedback = field.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.style.display = 'none';
        }
        
        // Show valid state if field has value
        if (field.value.trim()) {
            this.validateField(field);
        } else {
            field.classList.remove('is-valid');
        }
    }

    validateAllFields() {
        const fields = ['product_name', 'product_description', 'product_type', 'product_fk_business'];
        let isValid = true;
        
        fields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                if (!this.validateField(field)) {
                    isValid = false;
                }
            }
        });
        
        return isValid;
    }

    // CHARACTER COUNTER
    updateCharacterCount() {
        const descriptionField = document.getElementById('product_description');
        if (!descriptionField || !this.charCountElement) return;
        
        const currentLength = descriptionField.value.length;
        const maxLength = 1000;
        
        this.charCountElement.textContent = currentLength;
        
        // Update color based on length
        const parentElement = this.charCountElement.parentElement;
        parentElement.classList.remove('text-warning', 'text-danger');
        
        if (currentLength > maxLength * 0.9) {
            parentElement.classList.add('text-danger');
        } else if (currentLength > maxLength * 0.8) {
            parentElement.classList.add('text-warning');
        }
    }

    // MODAL MANAGEMENT
    prepareModal() {
        this.hideLoading();
        this.hideAlert();
        this.updateCharacterCount();
    }

    showLoading() {
        if (this.modalLoading) this.modalLoading.style.display = 'block';
        if (this.modalContent) this.modalContent.style.display = 'none';
    }

    hideLoading() {
        if (this.modalLoading) this.modalLoading.style.display = 'none';
        if (this.modalContent) this.modalContent.style.display = 'block';
    }

    showAlert(type, message) {
        if (!this.formAlerts) return;
        
        const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
        const iconClass = type === 'error' ? 'ri-error-warning-line' : 'ri-check-double-line';
        
        this.formAlerts.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="${iconClass} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        this.formAlerts.style.display = 'block';
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                this.hideAlert();
            }, 5000);
        }
    }

    hideAlert() {
        if (this.formAlerts) {
            this.formAlerts.style.display = 'none';
            this.formAlerts.innerHTML = '';
        }
    }

    // FORM SUBMISSION
    handleFormSubmission() {
        if (this.isSubmitting) return;
        
        // Validate all fields
        if (!this.validateAllFields()) {
            this.showAlert('error', 'Por favor, corrija los errores en el formulario');
            return;
        }
        
        this.isSubmitting = true;
        this.showSubmitLoading();
        
        const isUpdate = this.productIdField && this.productIdField.value !== '';
        const formData = new FormData(this.form);
        
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
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                this.handleSuccess(isUpdate, data);
            } else {
                this.handleFormErrors(data);
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            this.showAlert('error', 'Ocurrió un error al procesar la solicitud. Por favor, intente nuevamente.');
        })
        .finally(() => {
            this.isSubmitting = false;
            this.hideSubmitLoading();
        });
    }

    handleSuccess(isUpdate, data) {
        // Close modal
        if (window.bootstrap && this.modal) {
            bootstrap.Modal.getInstance(this.modal).hide();
        }
        
        // Show success message
        const message = isUpdate 
            ? 'El producto ha sido actualizado con éxito' 
            : 'El producto ha sido creado con éxito';
            
        this.showSuccessNotification(message, data);
    }

    handleFormErrors(data) {
        if (data.errors) {
            // Show field-specific errors
            for (const field in data.errors) {
                const fieldElement = document.getElementById(`product_${field}`) || document.getElementById(field);
                if (fieldElement) {
                    this.showFieldError(fieldElement, data.errors[field][0]);
                }
            }
        }
        
        // Show general error
        const errorMessage = data.errors?.general?.[0] || 'Se encontraron errores en el formulario';
        this.showAlert('error', errorMessage);
    }

    showSubmitLoading() {
        if (this.submitBtn) {
            this.submitBtn.disabled = true;
            this.submitBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                Guardando...
            `;
        }
    }

    hideSubmitLoading() {
        if (this.submitBtn && this.submitBtnText) {
            this.submitBtn.disabled = false;
            this.submitBtn.innerHTML = `
                <i class="ri-save-3-line align-bottom me-1"></i>
                ${this.submitBtnText.textContent}
            `;
        }
    }

    // FORM RESET
    resetForm() {
        if (this.form) {
            this.form.reset();
        }
        
        // Reset image preview
        if (this.imagePreview) {
            this.imagePreview.src = '/static/images/default-product.png';
            this.imagePreview.classList.remove('image-loaded');
        }
        
        // Reset product ID
        if (this.productIdField) {
            this.productIdField.value = '';
        }
        
        // Reset modal title
        if (this.modalTitle) {
            this.modalTitle.textContent = 'Crear Producto';
        }
        
        // Reset submit button text
        if (this.submitBtnText) {
            this.submitBtnText.textContent = 'Guardar';
        }
        
        // Clear validation states
        const inputs = this.form?.querySelectorAll('.form-control, .form-select') || [];
        inputs.forEach(input => {
            input.classList.remove('is-valid', 'is-invalid');
        });
        
        // Reset character count
        if (this.charCountElement) {
            this.charCountElement.textContent = '0';
            this.charCountElement.parentElement.classList.remove('text-warning', 'text-danger');
        }
        
        // Hide alerts
        this.hideAlert();
    }

    // PUBLIC METHODS
    createNew() {
        this.resetForm();
        if (this.modalTitle) {
            this.modalTitle.textContent = 'Crear Nuevo Producto';
        }
        if (this.submitBtnText) {
            this.submitBtnText.textContent = 'Crear Producto';
        }
        
        // Show modal
        if (window.bootstrap && this.modal) {
            const bsModal = new bootstrap.Modal(this.modal);
            bsModal.show();
        }
    }

    edit(productId) {
        if (!productId) {
            console.error('No product ID provided for editing');
            return;
        }

        this.showLoading();
        
        if (this.modalTitle) {
            this.modalTitle.textContent = 'Actualizar Producto';
        }
        if (this.submitBtnText) {
            this.submitBtnText.textContent = 'Actualizar Producto';
        }
        if (this.productIdField) {
            this.productIdField.value = productId;
        }

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
                this.hideLoading();
                
                // Show modal
                if (window.bootstrap && this.modal) {
                    const bsModal = new bootstrap.Modal(this.modal);
                    bsModal.show();
                }
            })
            .catch(error => {
                console.error('Error loading product details:', error);
                this.hideLoading();
                this.showErrorNotification('No se pudieron cargar los detalles del producto');
            });
    }

    populateForm(data) {
        // Populate form fields
        const fieldMappings = {
            'product_name': 'name',
            'product_type': 'type',
            'product_fk_business': 'fk_business',
            'product_description': 'description'
        };

        for (const [fieldId, dataKey] of Object.entries(fieldMappings)) {
            const field = document.getElementById(fieldId);
            if (field && data[dataKey] !== undefined) {
                field.value = data[dataKey] || '';
                
                // Trigger validation for populated fields
                if (field.value) {
                    this.validateField(field);
                }
            }
        }

        // Update character count
        this.updateCharacterCount();

        // Show image if exists
        if (data.image_src && data.image_src !== 'None' && this.imagePreview) {
            this.imagePreview.src = data.image_src;
            this.imagePreview.classList.add('image-loaded');
        }
    }

    // DELETE FUNCTIONALITY
    confirmDelete(productId) {
        if (!productId) {
            console.error('No product ID provided for deletion');
            return;
        }

        // Configure deletion URL
        if (this.deleteForm) {
            this.deleteForm.action = `/product/delete/${productId}/`;
        }

        // Show confirmation modal
        if (window.bootstrap && this.deleteModal) {
            const bsModal = new bootstrap.Modal(this.deleteModal);
            bsModal.show();
        }
    }

    handleDeletion() {
        const deleteBtn = this.deleteForm?.querySelector('.delete-confirm-btn');
        
        if (deleteBtn) {
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                Eliminando...
            `;
        }

        fetch(this.deleteForm.action, {
            method: 'POST',
            body: new FormData(this.deleteForm),
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            // Django returns redirect (302) after deletion, not JSON
            if (response.ok || response.status === 302) {
                // Close modal
                if (window.bootstrap && this.deleteModal) {
                    bootstrap.Modal.getInstance(this.deleteModal).hide();
                }
                
                // Show success message
                this.showDeleteSuccessNotification();
            } else {
                throw new Error('Error al eliminar el producto');
            }
        })
        .catch(error => {
            console.error('Error deleting product:', error);
            this.showErrorNotification('No se pudo eliminar el producto. Por favor, intente nuevamente.');
        })
        .finally(() => {
            if (deleteBtn) {
                deleteBtn.disabled = false;
                deleteBtn.innerHTML = `
                    <i class="ri-delete-bin-line me-1"></i>
                    ¡Sí, eliminar!
                `;
            }
        });
    }

    // NOTIFICATIONS
    showSuccessNotification(message, data) {
        if (window.Swal) {
            Swal.fire({
                title: 'Éxito',
                text: message,
                icon: 'success',
                confirmButtonText: 'OK',
                timer: 3000,
                timerProgressBar: true,
                showCancelButton: false,
                allowOutsideClick: false
            }).then((result) => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.location.reload();
                }
            });
        } else {
            alert(message);
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                window.location.reload();
            }
        }
    }

    showDeleteSuccessNotification() {
        if (window.Swal) {
            Swal.fire({
                title: 'Producto Eliminado',
                text: 'El producto ha sido eliminado con éxito',
                icon: 'success',
                confirmButtonText: 'OK',
                timer: 3000,
                timerProgressBar: true
            }).then(() => {
                window.location.href = '/product/list';
            });
        } else {
            alert('Producto eliminado con éxito');
            window.location.href = '/product/list';
        }
    }

    showErrorNotification(message) {
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

    // UTILITIES
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

    // CLEANUP
    destroy() {
        console.log('ProductModalManager destroyed');
    }
}

// GLOBAL INSTANCE AND FUNCTIONS
let productModalManager;

function loadProductDetails(productId) {
    if (productModalManager) {
        productModalManager.edit(productId);
    }
}

function createNewProduct() {
    if (productModalManager) {
        productModalManager.createNew();
    }
}

function deleteProduct(productId) {
    if (productModalManager) {
        productModalManager.confirmDelete(productId);
    }
}

// INITIALIZATION
document.addEventListener('DOMContentLoaded', () => {
    try {
        productModalManager = new ProductModalManager();
        
        // Add drag and drop styles
        const style = document.createElement('style');
        style.textContent = `
            .drag-over {
                border: 2px dashed var(--primary-color) !important;
                background: rgba(64, 81, 137, 0.1) !important;
            }
            
            .image-loaded {
                transition: opacity 0.3s ease;
            }
        `;
        document.head.appendChild(style);
        
        console.log('Product Modal Manager initialized successfully');
    } catch (error) {
        console.error('Error initializing Product Modal Manager:', error);
    }
});

// CLEANUP
window.addEventListener('beforeunload', () => {
    if (productModalManager) {
        productModalManager.destroy();
    }
});