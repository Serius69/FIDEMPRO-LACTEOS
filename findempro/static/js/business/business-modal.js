/**
 * Business Modal Management
 * Handles SEPARATE create, update, and delete operations
 * Compatible with Django backend soft delete and form handling
 */

class BusinessModalManager {
    constructor() {
        this.createForm = null;
        this.updateForm = null;
        this.deleteForm = null;
        this.modal = null;
        this.deleteModal = null;
        this.currentMode = 'create'; // 'create' or 'update'
        this.currentBusinessId = null;
        this.originalData = null; // Para comparar cambios
        this.csrfToken = this.getCSRFToken();
        
        this.init();
    }

    init() {
        this.setupElements();
        this.bindEvents();
        this.initializeValidation();
    }

    setupElements() {
        this.modal = document.getElementById('addOrUpdateBusiness');
        this.deleteModal = document.getElementById('removeBusinessModal');
        this.createForm = document.getElementById('businessForm');
        this.deleteForm = document.getElementById('deleteBusinessForm');
        
        if (!this.createForm || !this.modal) {
            console.warn('Business modal elements not found');
            return;
        }

        // Form elements using Django field IDs with debugging
        this.elements = {
            businessId: document.getElementById('business_id'),
            imageInput: document.getElementById('id_image_src'),
            logoImg: document.getElementById('logo-img'),
            clearImageBtn: document.getElementById('clearImage'),
            nameInput: document.getElementById('id_name'),
            typeSelect: document.getElementById('id_type'),
            locationSelect: document.getElementById('id_location'),
            descriptionTextarea: document.getElementById('id_description'),
            descriptionCount: document.getElementById('descriptionCount'),
            submitBtn: document.getElementById('submitBtn'),
            submitBtnText: document.getElementById('submitBtnText'),
            modalTitle: document.getElementById('addOrUpdateBusinessLabel'),
            modalTutorial: document.getElementById('modalTutorial')
        };
        
        // DEBUG: Log which elements were found
        console.log('🔍 Form elements setup:', {
            businessId: !!this.elements.businessId,
            imageInput: !!this.elements.imageInput,
            logoImg: !!this.elements.logoImg,
            clearImageBtn: !!this.elements.clearImageBtn,
            nameInput: !!this.elements.nameInput,
            typeSelect: !!this.elements.typeSelect,
            locationSelect: !!this.elements.locationSelect,
            descriptionTextarea: !!this.elements.descriptionTextarea,
            descriptionCount: !!this.elements.descriptionCount,
            submitBtn: !!this.elements.submitBtn,
            submitBtnText: !!this.elements.submitBtnText,
            modalTitle: !!this.elements.modalTitle,
            modalTutorial: !!this.elements.modalTutorial
        });
        
        // Check for missing critical elements
        const criticalElements = ['nameInput', 'typeSelect', 'locationSelect', 'descriptionTextarea'];
        const missingElements = criticalElements.filter(key => !this.elements[key]);
        
        if (missingElements.length > 0) {
            console.error('❌ Critical form elements missing:', missingElements);
            console.error('❌ Available form elements in DOM:', 
                Array.from(this.createForm.querySelectorAll('input, select, textarea'))
                    .map(el => ({ tag: el.tagName, id: el.id, name: el.name }))
            );
        }
    }

    bindEvents() {
        if (!this.createForm) return;

        // Modal events
        this.modal.addEventListener('shown.bs.modal', () => this.onModalShown());
        this.modal.addEventListener('hidden.bs.modal', () => this.onModalHidden());

        // Form events
        this.createForm.addEventListener('submit', (e) => this.handleFormSubmit(e));
        this.createForm.addEventListener('input', (e) => this.handleInputChange(e));

        // Image handling
        if (this.elements.imageInput) {
            this.elements.imageInput.addEventListener('change', (e) => this.handleImageUpload(e));
        }
        
        if (this.elements.clearImageBtn) {
            this.elements.clearImageBtn.addEventListener('click', () => this.clearImage());
        }

        // Description counter
        if (this.elements.descriptionTextarea) {
            this.elements.descriptionTextarea.addEventListener('input', () => this.updateCharacterCount());
        }

        // Delete form
        if (this.deleteForm) {
            this.deleteForm.addEventListener('submit', (e) => this.handleDelete(e));
        }
    }

    // ================================
    // CREATE BUSINESS OPERATIONS
    // ================================
    
    openCreateModal() {
        console.log('📝 Opening CREATE modal');
        this.currentMode = 'create';
        this.currentBusinessId = null;
        this.originalData = null;
        
        this.resetFormForCreate();
        this.showModal();
    }

    resetFormForCreate() {
        // Update UI for create mode
        if (this.elements.modalTitle) {
            this.elements.modalTitle.innerHTML = '<i class="ri-store-2-line me-2"></i>Crear Nuevo Negocio';
        }
        if (this.elements.submitBtnText) {
            this.elements.submitBtnText.textContent = 'Crear Negocio';
        }
        
        // Clear form
        this.createForm.reset();
        this.clearImage();
        this.updateCharacterCount();
        
        // Set form action and clear business ID
        this.createForm.action = '/business/create/';
        if (this.elements.businessId) {
            this.elements.businessId.value = '';
        }
        
        this.clearValidation();
    }

    async handleCreateBusiness(formData) {
        console.log('➕ Creating new business');
        
        try {
            const response = await fetch('/business/create/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('success', data.message || 'Negocio creado exitosamente');
                this.hideModal();
                setTimeout(() => window.location.reload(), 1000);
                return true;
            } else {
                this.showToast('error', data.message || 'Error al crear negocio');
                this.displayFormErrors(data.errors);
                return false;
            }
        } catch (error) {
            console.error('Error creating business:', error);
            this.showToast('error', 'Error de conexión al crear negocio');
            return false;
        }
    }

    // ================================
    // UPDATE BUSINESS OPERATIONS  
    // ================================

    async openUpdateModal(businessId) {
        console.log(`✏️ Opening UPDATE modal for business ${businessId}`);
        this.currentMode = 'update';
        this.currentBusinessId = businessId;
        
        try {
            this.setLoadingState(true, 'Cargando datos del negocio...');
            
            // Load business data
            const businessData = await this.loadBusinessData(businessId);
            
            console.log('✅ Business data loaded successfully:', businessData);
            
            if (businessData && !businessData.error) {
                this.originalData = { ...businessData }; // Save original for comparison
                this.setupFormForUpdate(businessData, businessId);
                this.showModal();
            } else {
                throw new Error(businessData?.error || 'Datos no válidos recibidos');
            }
        } catch (error) {
            console.error('❌ Error loading business for update:', error);
            this.showToast('error', `Error al cargar datos del negocio: ${error.message}`);
        } finally {
            this.setLoadingState(false);
        }
    }

    async loadBusinessData(businessId) {
        console.log(`📡 Loading business data for ID: ${businessId}`);
        
        try {
            const response = await fetch(`/business/api/details/${businessId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken
                }
            });

            console.log(`📡 Response status: ${response.status} ${response.statusText}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`❌ HTTP Error: ${response.status} - ${errorText}`);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // DEBUGGING: Log the received data
            console.log('📋 Raw response data:', data);
            console.log('📋 Data fields detailed check:', {
                id: { value: data.id, type: typeof data.id },
                name: { value: data.name, type: typeof data.name },
                type: { value: data.type, type: typeof data.type },
                location: { value: data.location, type: typeof data.location },
                description: { value: data.description, type: typeof data.description },
                image_src: { value: data.image_src, type: typeof data.image_src }
            });
            
            // Check for backend error in response
            if (data.error) {
                console.error(`❌ Backend error: ${data.error}`);
                throw new Error(data.error);
            }
            
            // Validate required fields
            if (!data.id || !data.name) {
                console.error('❌ Missing required fields in response');
                throw new Error('Respuesta incompleta del servidor');
            }
            
            console.log('✅ Data validation passed');
            return data;
            
        } catch (error) {
            console.error('❌ Exception in loadBusinessData:', error);
            
            // Re-throw with more context
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Error de conexión con el servidor');
            } else if (error.name === 'SyntaxError') {
                throw new Error('Respuesta inválida del servidor');
            } else {
                throw error; // Re-throw the original error
            }
        }
    }

    setupFormForUpdate(businessData, businessId) {
        console.log(`🔧 Setting up form for UPDATE mode with ID: ${businessId}`);
        
        // Update UI for update mode
        if (this.elements.modalTitle) {
            this.elements.modalTitle.innerHTML = '<i class="ri-edit-line me-2"></i>Actualizar Negocio';
            console.log('✅ Modal title updated');
        }
        
        if (this.elements.submitBtnText) {
            this.elements.submitBtnText.textContent = 'Actualizar Negocio';
            console.log('✅ Submit button text updated');
        }
        
        // Set form action and business ID
        this.createForm.action = `/business/${businessId}/update/`;
        console.log(`✅ Form action set to: ${this.createForm.action}`);
        
        if (this.elements.businessId) {
            this.elements.businessId.value = businessId;
            console.log(`✅ Business ID field set to: ${businessId}`);
        }
        
        // Populate form with existing data
        try {
            this.populateForm(businessData);
            console.log('✅ Form populated successfully');
        } catch (error) {
            console.error('❌ Error populating form:', error);
            throw new Error(`Error al llenar el formulario: ${error.message}`);
        }
        
        this.clearValidation();
        console.log('✅ Form validation cleared');
    }

    async loadBusinessData(businessId) {
        console.log(`📡 Loading business data for ID: ${businessId}`);
        
        try {
            const response = await fetch(`/business/api/details/${businessId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.csrfToken
                }
            });

            console.log(`📡 Response status: ${response.status}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // DEBUGGING: Log the received data
            console.log('📋 Received business data:', data);
            console.log('📋 Data fields check:', {
                id: data.id,
                name: data.name,
                type: data.type,
                location: data.location,
                description: data.description,
                image_src: data.image_src
            });
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            return data;
        } catch (error) {
            console.error('❌ Error loading business data:', error);
            throw error;
        }
    }

    populateForm(data) {
        console.log('📋 Starting form population with data:', data);
        
        // Verificar que los elementos existen antes de poblarlos
        const elements = {
            name: this.elements.nameInput,
            type: this.elements.typeSelect,
            location: this.elements.locationSelect,
            description: this.elements.descriptionTextarea
        };
        
        console.log('📋 Form elements availability check:', {
            nameInput: !!elements.name,
            typeSelect: !!elements.type,
            locationSelect: !!elements.location,
            descriptionTextarea: !!elements.description
        });
        
        let populationErrors = [];
        
        // Populate NAME field
        try {
            if (elements.name) {
                const nameValue = data.name || '';
                elements.name.value = nameValue;
                console.log(`✅ Name populated: "${nameValue}"`);
            } else {
                populationErrors.push('Name input element not found');
                console.error('❌ Name input not found');
            }
        } catch (error) {
            populationErrors.push(`Name population error: ${error.message}`);
            console.error('❌ Error setting name:', error);
        }
        
        // Populate TYPE field
        try {
            if (elements.type) {
                const typeValue = data.type || '';
                console.log(`🔍 Attempting to set type to: "${typeValue}"`);
                
                // Check if option exists
                const option = elements.type.querySelector(`option[value="${typeValue}"]`);
                if (option) {
                    elements.type.value = typeValue;
                    console.log(`✅ Type populated: "${typeValue}" (${option.textContent})`);
                } else {
                    console.warn(`⚠️ Type option "${typeValue}" not found. Available options:`);
                    Array.from(elements.type.options).forEach((opt, idx) => {
                        console.log(`  ${idx}: value="${opt.value}" text="${opt.textContent}"`);
                    });
                    // Set to empty/default if option doesn't exist
                    elements.type.value = '';
                }
            } else {
                populationErrors.push('Type select element not found');
                console.error('❌ Type select not found');
            }
        } catch (error) {
            populationErrors.push(`Type population error: ${error.message}`);
            console.error('❌ Error setting type:', error);
        }
        
        // Populate LOCATION field
        try {
            if (elements.location) {
                const locationValue = data.location || '';
                console.log(`🔍 Attempting to set location to: "${locationValue}"`);
                
                // Check if option exists
                const option = elements.location.querySelector(`option[value="${locationValue}"]`);
                if (option) {
                    elements.location.value = locationValue;
                    console.log(`✅ Location populated: "${locationValue}"`);
                } else {
                    console.warn(`⚠️ Location option "${locationValue}" not found. Available options:`);
                    Array.from(elements.location.options).forEach((opt, idx) => {
                        console.log(`  ${idx}: value="${opt.value}" text="${opt.textContent}"`);
                    });
                    // Set to empty/default if option doesn't exist
                    elements.location.value = '';
                }
            } else {
                populationErrors.push('Location select element not found');
                console.error('❌ Location select not found');
            }
        } catch (error) {
            populationErrors.push(`Location population error: ${error.message}`);
            console.error('❌ Error setting location:', error);
        }
        
        // Populate DESCRIPTION field
        try {
            if (elements.description) {
                const descriptionValue = data.description || '';
                elements.description.value = descriptionValue;
                console.log(`✅ Description populated: "${descriptionValue.substring(0, 50)}${descriptionValue.length > 50 ? '...' : ''}"`);
            } else {
                populationErrors.push('Description textarea element not found');
                console.error('❌ Description textarea not found');
            }
        } catch (error) {
            populationErrors.push(`Description population error: ${error.message}`);
            console.error('❌ Error setting description:', error);
        }
        
        // Update character count
        try {
            this.updateCharacterCount();
            console.log('✅ Character count updated');
        } catch (error) {
            console.error('❌ Error updating character count:', error);
        }
        
        // Handle image preview
        try {
            if (data.image_src && data.image_src !== '/static/images/business/business-dummy-img.webp') {
                console.log(`🖼️ Loading image: ${data.image_src}`);
                this.previewImage(data.image_src);
            } else {
                console.log('🖼️ No custom image, clearing preview');
                this.clearImage();
            }
        } catch (error) {
            console.error('❌ Error handling image:', error);
        }
        
        // Report results
        if (populationErrors.length > 0) {
            console.error('❌ Form population completed with errors:', populationErrors);
            throw new Error(`Errores al llenar formulario: ${populationErrors.join(', ')}`);
        } else {
            console.log('✅ Form population completed successfully');
        }
        
        // Final validation - check if form actually has values
        const finalCheck = {
            name: elements.name?.value || '',
            type: elements.type?.value || '',
            location: elements.location?.value || '',
            description: elements.description?.value || ''
        };
        
        console.log('📋 Final form state:', finalCheck);
        
        return finalCheck;
    }

    async handleUpdateBusiness(formData, businessId) {
        console.log(`🔄 Updating business ${businessId}`);
        
        try {
            const response = await fetch(`/business/${businessId}/update/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('success', data.message || 'Negocio actualizado exitosamente');
                this.hideModal();
                setTimeout(() => window.location.reload(), 1000);
                return true;
            } else {
                this.showToast('error', data.message || 'Error al actualizar negocio');
                this.displayFormErrors(data.errors);
                return false;
            }
        } catch (error) {
            console.error('Error updating business:', error);
            this.showToast('error', 'Error de conexión al actualizar negocio');
            return false;
        }
    }

    // ================================
    // DELETE BUSINESS OPERATIONS (SOFT DELETE)
    // ================================

    openDeleteModal(businessId) {
        console.log(`🗑️ Opening DELETE modal for business ${businessId}`);
        
        const deleteBusinessIdInput = document.getElementById('delete-business-id');
        
        if (deleteBusinessIdInput) {
            deleteBusinessIdInput.value = businessId;
        }
        
        // Set the form action for soft delete (UPDATE)
        if (this.deleteForm) {
            this.deleteForm.action = `/business/${businessId}/delete/`;
        }
        
        const modalInstance = new bootstrap.Modal(this.deleteModal);
        modalInstance.show();
    }

    async handleDelete(e) {
        e.preventDefault();
        
        const businessId = document.getElementById('delete-business-id').value;
        if (!businessId) {
            this.showToast('error', 'ID de negocio no encontrado');
            return;
        }
        
        console.log(`🗑️ Soft deleting business ${businessId}`);
        
        try {
            this.setDeleteLoading(true);
            
            // This performs a soft delete (UPDATE is_active = False)
            const response = await fetch(`/business/${businessId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('success', data.message || 'Negocio eliminado exitosamente');
                this.hideDeleteModal();
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showToast('error', data.message || 'Error al eliminar negocio');
            }
        } catch (error) {
            console.error('Error deleting business:', error);
            this.showToast('error', 'Error al eliminar el negocio');
        } finally {
            this.setDeleteLoading(false);
        }
    }

    // ================================
    // UNIFIED FORM SUBMISSION HANDLER
    // ================================

    async handleFormSubmit(e) {
        e.preventDefault();
        e.stopPropagation();

        if (!this.validateForm()) {
            this.createForm.classList.add('was-validated');
            this.showToast('error', 'Por favor corrige los errores en el formulario');
            return;
        }

        this.setSubmitLoading(true);
        
        const formData = new FormData(this.createForm);
        let success = false;
        
        try {
            if (this.currentMode === 'create') {
                success = await this.handleCreateBusiness(formData);
            } else if (this.currentMode === 'update') {
                success = await this.handleUpdateBusiness(formData, this.currentBusinessId);
            }
        } finally {
            this.setSubmitLoading(false);
        }
    }

    // ================================
    // MODAL LIFECYCLE
    // ================================

    onModalShown() {
        // Show tutorial for first-time users
        if (!localStorage.getItem('businessModalTutorialShown') && this.elements.modalTutorial) {
            this.elements.modalTutorial.classList.remove('d-none');
            localStorage.setItem('businessModalTutorialShown', 'true');
        }

        // Focus first input
        const firstInput = this.createForm.querySelector('input:not([type="hidden"]), select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        console.log(`📱 Modal opened in ${this.currentMode} mode`);
    }

    onModalHidden() {
        console.log('📱 Modal closed');
        this.currentMode = 'create';
        this.currentBusinessId = null;
        this.originalData = null;
        this.clearValidation();
    }

    showModal() {
        const modalInstance = new bootstrap.Modal(this.modal);
        modalInstance.show();
    }

    hideModal() {
        const modalInstance = bootstrap.Modal.getInstance(this.modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    }

    hideDeleteModal() {
        const modalInstance = bootstrap.Modal.getInstance(this.deleteModal);
        if (modalInstance) {
            modalInstance.hide();
        }
    }

    // ================================
    // IMAGE HANDLING
    // ================================

    handleImageUpload(e) {
        const file = e.target.files[0];
        if (!file) return;

        const validation = this.validateImageFile(file);
        if (!validation.valid) {
            this.showToast('error', validation.message);
            e.target.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => this.previewImage(e.target.result);
        reader.readAsDataURL(file);
    }

    validateImageFile(file) {
        const maxSize = 5 * 1024 * 1024; // 5MB
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];

        if (file.size > maxSize) {
            return { valid: false, message: 'La imagen no debe superar los 5MB' };
        }

        if (!validTypes.includes(file.type)) {
            return { valid: false, message: 'Formato de imagen no válido. Use PNG, JPG o WEBP' };
        }

        return { valid: true };
    }

    previewImage(src) {
        if (this.elements.logoImg) {
            this.elements.logoImg.src = src;
            this.elements.logoImg.style.display = 'block';
            this.elements.logoImg.classList.add('show');
        }
        
        if (this.elements.clearImageBtn) {
            this.elements.clearImageBtn.style.display = 'inline-block';
            this.elements.clearImageBtn.classList.add('show');
        }

        const placeholder = this.modal.querySelector('.image-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
    }

    clearImage() {
        if (this.elements.imageInput) this.elements.imageInput.value = '';
        if (this.elements.logoImg) {
            this.elements.logoImg.style.display = 'none';
            this.elements.logoImg.classList.remove('show');
            this.elements.logoImg.src = '';
        }
        if (this.elements.clearImageBtn) {
            this.elements.clearImageBtn.style.display = 'none';
            this.elements.clearImageBtn.classList.remove('show');
        }

        const placeholder = this.modal.querySelector('.image-placeholder');
        if (placeholder) {
            placeholder.style.display = 'flex';
        }
    }

    // ================================
    // FORM VALIDATION
    // ================================

    initializeValidation() {
        if (!this.createForm) return;

        const inputs = this.createForm.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let message = '';

        switch (field.name) {
            case 'name':
                if (!value) {
                    isValid = false;
                    message = 'El nombre es requerido';
                } else if (value.length < 2) {
                    isValid = false;
                    message = 'El nombre debe tener al menos 2 caracteres';
                }
                break;
                
            case 'type':
                if (!value) {
                    isValid = false;
                    message = 'Selecciona un tipo de negocio';
                }
                break;
                
            case 'location':
                if (!value) {
                    isValid = false;
                    message = 'Selecciona una ubicación';
                }
                break;
                
            case 'description':
                if (!value) {
                    isValid = false;
                    message = 'La descripción es requerida';
                } else if (value.length < 10) {
                    isValid = false;
                    message = 'La descripción debe tener al menos 10 caracteres';
                }
                break;
        }

        this.setFieldValidation(field, isValid, message);
        return isValid;
    }

    validateForm() {
        const requiredFields = this.createForm.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });

        return isValid;
    }

    setFieldValidation(field, isValid, message) {
        field.classList.toggle('is-invalid', !isValid);
        field.classList.toggle('is-valid', isValid);

        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback && !isValid) {
            feedback.textContent = message;
        }
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
    }

    clearValidation() {
        const fields = this.createForm.querySelectorAll('.is-invalid, .is-valid');
        fields.forEach(field => {
            field.classList.remove('is-invalid', 'is-valid');
        });
        this.createForm.classList.remove('was-validated');
    }

    displayFormErrors(errors) {
        if (!errors) return;
        
        this.clearValidation();
        
        for (const [field, messages] of Object.entries(errors)) {
            const fieldElement = document.getElementById(`id_${field}`) || document.getElementById(field);
            if (fieldElement) {
                const message = Array.isArray(messages) ? messages[0] : messages;
                this.setFieldValidation(fieldElement, false, message);
            }
        }
    }

    // ================================
    // UI STATE MANAGEMENT
    // ================================

    setLoadingState(loading, message = 'Cargando...') {
        if (loading) {
            const loader = document.createElement('div');
            loader.id = 'modalLoader';
            loader.className = 'position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
            loader.style.cssText = 'background: rgba(255,255,255,0.9); z-index: 1050; border-radius: 16px;';
            loader.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3"></div>
                    <div>${message}</div>
                </div>
            `;
            
            this.modal.querySelector('.modal-content').style.position = 'relative';
            this.modal.querySelector('.modal-content').appendChild(loader);
        } else {
            const loader = document.getElementById('modalLoader');
            if (loader) loader.remove();
        }
    }

    setSubmitLoading(loading) {
        if (!this.elements.submitBtn || !this.elements.submitBtnText) return;
        
        if (loading) {
            this.elements.submitBtn.disabled = true;
            this.elements.submitBtn.classList.add('btn-loading');
            
            const actionText = this.currentMode === 'create' ? 'Creando...' : 'Actualizando...';
            this.elements.submitBtnText.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                ${actionText}
            `;
        } else {
            this.elements.submitBtn.disabled = false;
            this.elements.submitBtn.classList.remove('btn-loading');
            
            const actionText = this.currentMode === 'create' ? 'Crear Negocio' : 'Actualizar Negocio';
            this.elements.submitBtnText.textContent = actionText;
        }
    }

    setDeleteLoading(loading) {
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        if (!deleteBtn) return;
        
        if (loading) {
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                Eliminando...
            `;
        } else {
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = '<i class="ri-delete-bin-line me-1"></i>Sí, eliminar';
        }
    }

    // ================================
    // UTILITY METHODS
    // ================================

    updateCharacterCount() {
        if (!this.elements.descriptionTextarea || !this.elements.descriptionCount) return;

        const count = this.elements.descriptionTextarea.value.length;
        const maxLength = 1000;
        
        this.elements.descriptionCount.textContent = count;
        
        this.elements.descriptionCount.classList.remove('warning', 'danger');
        if (count > maxLength * 0.9) {
            this.elements.descriptionCount.classList.add('warning');
        }
        if (count > maxLength) {
            this.elements.descriptionCount.classList.add('danger');
        }
    }

    handleInputChange(e) {
        const field = e.target;
        
        if (field.name === 'description') {
            this.updateCharacterCount();
        }
        
        this.clearFieldError(field);
        
        if (['name', 'description'].includes(field.name)) {
            setTimeout(() => this.validateField(field), 500);
        }
    }

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

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    // ================================
    // PUBLIC API
    // ================================

    // Check if form has unsaved changes
    isDirty() {
        if (this.currentMode !== 'update' || !this.originalData) return false;
        
        const currentData = {
            name: this.elements.nameInput?.value || '',
            type: this.elements.typeSelect?.value || '',
            location: this.elements.locationSelect?.value || '',
            description: this.elements.descriptionTextarea?.value || ''
        };
        
        return JSON.stringify(currentData) !== JSON.stringify({
            name: this.originalData.name || '',
            type: this.originalData.type || '',
            location: this.originalData.location || '',
            description: this.originalData.description || ''
        });
    }

    // Get current form data
    getFormData() {
        return {
            name: this.elements.nameInput?.value || '',
            type: this.elements.typeSelect?.value || '',
            location: this.elements.locationSelect?.value || '',
            description: this.elements.descriptionTextarea?.value || ''
        };
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 BusinessModalManager initializing...');
    
    try {
        const modalManager = new BusinessModalManager();
        window.businessModalManager = modalManager;
        console.log('✅ BusinessModalManager initialized successfully');
        
        // Test function for debugging
        window.testModalManager = function(businessId) {
            console.log(`🧪 Testing modal manager with business ID: ${businessId}`);
            
            if (modalManager) {
                console.log('📋 Modal manager available, testing openUpdateModal...');
                modalManager.openUpdateModal(businessId)
                    .then(() => {
                        console.log('✅ openUpdateModal completed successfully');
                    })
                    .catch(error => {
                        console.error('❌ openUpdateModal failed:', error);
                    });
            } else {
                console.error('❌ Modal manager not available');
            }
        };
        
        // Simple edit test
        window.simpleEditTest = function(businessId) {
            console.log(`🔧 Simple edit test for business ID: ${businessId}`);
            
            // Direct API test
            fetch(`/business/api/details/${businessId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': modalManager.getCSRFToken()
                }
            })
            .then(response => {
                console.log('📡 Response received:', response.status, response.statusText);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('📋 Data received:', data);
                
                // Try manual form population
                const nameInput = document.getElementById('id_name');
                const typeSelect = document.getElementById('id_type'); 
                const locationSelect = document.getElementById('id_location');
                const descriptionTextarea = document.getElementById('id_description');
                
                if (nameInput) nameInput.value = data.name || '';
                if (typeSelect) typeSelect.value = data.type || '';
                if (locationSelect) locationSelect.value = data.location || '';
                if (descriptionTextarea) descriptionTextarea.value = data.description || '';
                
                // Show modal
                const modal = document.getElementById('addOrUpdateBusiness');
                if (modal) {
                    const modalInstance = new bootstrap.Modal(modal);
                    modalInstance.show();
                    console.log('✅ Modal shown with populated data');
                } else {
                    console.error('❌ Modal element not found');
                }
            })
            .catch(error => {
                console.error('❌ Simple edit test failed:', error);
            });
        };
        
    } catch (error) {
        console.error('❌ BusinessModalManager initialization failed:', error);
        console.error('Error details:', error.stack);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BusinessModalManager;
}