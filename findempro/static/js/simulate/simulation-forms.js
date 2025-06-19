/**
 * SIMULATION FORMS - Sistema de validación y manejo de formularios
 * Proporciona validación en tiempo real, feedback visual y manejo de errores
 */

class SimulationForms {
    constructor() {
        this.forms = new Map();
        this.validators = new Map();
        this.config = {
            validateOnBlur: true,
            validateOnInput: true,
            showSuccessState: true,
            debounceTime: 300,
            animationDuration: 300
        };
        
        this.init();
    }

    /**
     * Inicializar el sistema de formularios
     */
    init() {
        this.setupValidators();
        this.bindEvents();
        this.initializeForms();
    }

    /**
     * Configurar validadores personalizados
     */
    setupValidators() {
        // Validador para cuestionarios
        this.validators.set('questionary', {
            validate: (value) => {
                if (!value || value.trim() === '') {
                    return { isValid: false, message: 'Debe seleccionar un cuestionario' };
                }
                return { isValid: true, message: '' };
            }
        });

        // Validador para cantidad de tiempo
        this.validators.set('quantity', {
            validate: (value, min = 1, max = 365) => {
                const numValue = parseInt(value);
                if (isNaN(numValue)) {
                    return { isValid: false, message: 'Debe ingresar un número válido' };
                }
                if (numValue < min || numValue > max) {
                    return { isValid: false, message: `El valor debe estar entre ${min} y ${max}` };
                }
                return { isValid: true, message: 'Valor válido' };
            }
        });

        // Validador para unidad de tiempo
        this.validators.set('timeUnit', {
            validate: (value) => {
                const validUnits = ['days', 'weeks', 'months'];
                if (!validUnits.includes(value)) {
                    return { isValid: false, message: 'Seleccione una unidad de tiempo válida' };
                }
                return { isValid: true, message: '' };
            }
        });

        // Validador para nivel de confianza
        this.validators.set('confidence', {
            validate: (value) => {
                const numValue = parseFloat(value);
                if (isNaN(numValue) || numValue < 0.1 || numValue > 0.99) {
                    return { isValid: false, message: 'El nivel de confianza debe estar entre 0.1 y 0.99' };
                }
                return { isValid: true, message: '' };
            }
        });

        // Validador para semilla aleatoria
        this.validators.set('randomSeed', {
            validate: (value) => {
                if (value === '') return { isValid: true, message: '' }; // Opcional
                const numValue = parseInt(value);
                if (isNaN(numValue) || numValue < 0) {
                    return { isValid: false, message: 'La semilla debe ser un número entero positivo' };
                }
                return { isValid: true, message: '' };
            }
        });
    }

    /**
     * Enlazar eventos de formularios
     */
    bindEvents() {
        document.addEventListener('DOMContentLoaded', () => {
            // Configuración de formulario de simulación
            const configForm = document.getElementById('simulationConfigForm');
            if (configForm) {
                this.initializeForm(configForm, 'config');
            }

            // Formulario de inicio de simulación
            const startForm = document.getElementById('simulationStartForm');
            if (startForm) {
                this.initializeForm(startForm, 'start');
            }
        });
    }

    /**
     * Inicializar formulario específico
     */
    initializeForm(formElement, formType) {
        const formData = {
            element: formElement,
            type: formType,
            fields: new Map(),
            isValid: false,
            touched: false
        };

        // Configurar campos del formulario
        this.setupFormFields(formElement, formData);
        
        // Configurar eventos del formulario
        this.setupFormEvents(formElement, formData);

        // Guardar formulario
        this.forms.set(formType, formData);

        console.log(`Formulario ${formType} inicializado`);
    }

    /**
     * Configurar campos del formulario
     */
    setupFormFields(formElement, formData) {
        const fields = formElement.querySelectorAll('input, select, textarea');
        
        fields.forEach(field => {
            const fieldData = {
                element: field,
                validator: this.getFieldValidator(field),
                isValid: false,
                isTouched: false,
                value: field.value,
                errorMessage: '',
                successMessage: ''
            };

            formData.fields.set(field.name || field.id, fieldData);
            this.setupFieldEvents(field, fieldData, formData);
        });
    }

    /**
     * Obtener validador para un campo
     */
    getFieldValidator(field) {
        const fieldName = field.name || field.id;
        
        // Mapear campos a validadores
        const fieldValidatorMap = {
            'selected_questionary_result': 'questionary',
            'selected_quantity_time': 'quantity',
            'selected_unit_time': 'timeUnit',
            'confidence_level': 'confidence',
            'random_seed': 'randomSeed'
        };

        return this.validators.get(fieldValidatorMap[fieldName]);
    }

    /**
     * Configurar eventos para un campo
     */
    setupFieldEvents(field, fieldData, formData) {
        let debounceTimer;

        // Evento input (mientras se escribe)
        if (this.config.validateOnInput) {
            field.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.validateField(fieldData, formData);
                }, this.config.debounceTime);
            });
        }

        // Evento blur (cuando pierde el foco)
        if (this.config.validateOnBlur) {
            field.addEventListener('blur', () => {
                fieldData.isTouched = true;
                this.validateField(fieldData, formData);
            });
        }

        // Evento change (para selects)
        field.addEventListener('change', () => {
            fieldData.isTouched = true;
            this.validateField(fieldData, formData);
            this.handleFieldChange(field, fieldData, formData);
        });

        // Evento focus (para limpiar estados previos)
        field.addEventListener('focus', () => {
            this.clearFieldMessage(fieldData);
        });
    }

    /**
     * Manejar cambios específicos de campos
     */
    handleFieldChange(field, fieldData, formData) {
        const fieldName = field.name || field.id;

        switch (fieldName) {
            case 'selected_questionary_result':
                this.handleQuestionaryChange(field, fieldData);
                break;
            case 'selected_quantity_time':
                this.handleQuantityChange(field, fieldData);
                break;
            case 'selected_unit_time':
                this.handleUnitChange(field, fieldData);
                break;
        }
    }

    /**
     * Manejar cambio en selector de cuestionario
     */
    handleQuestionaryChange(field, fieldData) {
        const selectedOption = field.options[field.selectedIndex];
        
        if (selectedOption && selectedOption.value) {
            const product = selectedOption.dataset.product;
            const business = selectedOption.dataset.business;
            const date = new Date(selectedOption.dataset.date).toLocaleDateString('es-ES');
            
            this.showQuestionaryInfo(field, {
                product,
                business,
                date
            });
        } else {
            this.hideQuestionaryInfo(field);
        }
    }

    /**
     * Mostrar información del cuestionario seleccionado
     */
    showQuestionaryInfo(field, info) {
        let infoCard = document.getElementById('questionaryInfo');
        
        if (!infoCard) {
            infoCard = document.createElement('div');
            infoCard.id = 'questionaryInfo';
            infoCard.className = 'alert alert-info mt-2 fade-in-up';
            field.closest('.form-group').appendChild(infoCard);
        }

        infoCard.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="bx bx-check-circle text-success me-2 mt-1"></i>
                <div>
                    <strong class="text-success">Cuestionario seleccionado</strong>
                    <div class="mt-1">
                        <small class="d-block"><strong>Producto:</strong> ${info.product}</small>
                        <small class="d-block"><strong>Empresa:</strong> ${info.business}</small>
                        <small class="d-block"><strong>Fecha:</strong> ${info.date}</small>
                    </div>
                </div>
            </div>
        `;

        // Animación de entrada
        infoCard.style.opacity = '0';
        infoCard.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            infoCard.style.transition = 'all 0.3s ease';
            infoCard.style.opacity = '1';
            infoCard.style.transform = 'translateY(0)';
        }, 10);
    }

    /**
     * Ocultar información del cuestionario
     */
    hideQuestionaryInfo(field) {
        const infoCard = document.getElementById('questionaryInfo');
        if (infoCard) {
            infoCard.style.transition = 'all 0.3s ease';
            infoCard.style.opacity = '0';
            infoCard.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                infoCard.remove();
            }, 300);
        }
    }

    /**
     * Manejar cambio en cantidad de tiempo
     */
    handleQuantityChange(field, fieldData) {
        const value = parseInt(field.value);
        const unit = document.getElementById('selected_unit_time')?.value || 'days';
        
        if (!isNaN(value) && value > 0) {
            this.updateQuantityHelp(field, value, unit);
        }
    }

    /**
     * Actualizar texto de ayuda para cantidad
     */
    updateQuantityHelp(field, quantity, unit) {
        const helpElement = document.getElementById('quantityHelp');
        if (!helpElement) return;

        const unitText = {
            'days': 'días',
            'weeks': 'semanas', 
            'months': 'meses'
        }[unit] || unit;

        helpElement.innerHTML = `
            <i class="bx bx-info-circle me-1"></i>
            Simulación configurada para <strong>${quantity} ${unitText}</strong>
        `;

        // Calcular duración aproximada en días
        let totalDays = quantity;
        if (unit === 'weeks') totalDays *= 7;
        if (unit === 'months') totalDays *= 30;

        if (totalDays > 90) {
            helpElement.innerHTML += `
                <br><small class="text-warning">
                    <i class="bx bx-time me-1"></i>
                    Simulación larga: puede tomar más tiempo procesarse
                </small>
            `;
        }
    }

    /**
     * Manejar cambio en unidad de tiempo
     */
    handleUnitChange(field, fieldData) {
        const quantityField = document.getElementById('selected_quantity_time');
        if (quantityField && quantityField.value) {
            this.handleQuantityChange(quantityField, fieldData);
        }
    }

    /**
     * Validar campo individual
     */
    validateField(fieldData, formData) {
        const field = fieldData.element;
        const validator = fieldData.validator;
        
        if (!validator) {
            fieldData.isValid = true;
            this.updateFieldUI(fieldData);
            return true;
        }

        // Obtener parámetros adicionales para validación
        const validationParams = this.getValidationParams(field);
        const result = validator.validate(field.value, ...validationParams);
        
        fieldData.isValid = result.isValid;
        fieldData.errorMessage = result.message;
        fieldData.value = field.value;

        this.updateFieldUI(fieldData);
        this.updateFormValidation(formData);

        return result.isValid;
    }

    /**
     * Obtener parámetros de validación adicionales
     */
    getValidationParams(field) {
        const fieldName = field.name || field.id;
        
        switch (fieldName) {
            case 'selected_quantity_time':
                return [1, 365]; // min, max
            default:
                return [];
        }
    }

    /**
     * Actualizar UI del campo
     */
    updateFieldUI(fieldData) {
        const field = fieldData.element;
        const fieldContainer = field.closest('.form-group') || field.closest('.mb-4') || field.closest('.mb-3');
        
        // Limpiar clases previas
        field.classList.remove('is-valid', 'is-invalid');
        
        if (fieldData.isTouched) {
            if (fieldData.isValid) {
                if (this.config.showSuccessState && field.value.trim() !== '') {
                    field.classList.add('is-valid');
                    this.showFieldSuccess(fieldData);
                }
            } else {
                field.classList.add('is-invalid');
                this.showFieldError(fieldData);
            }
        }
    }

    /**
     * Mostrar error en campo
     */
    showFieldError(fieldData) {
        const field = fieldData.element;
        const container = field.closest('.form-group') || field.closest('.mb-4') || field.closest('.mb-3');
        
        if (!container) return;

        let feedback = container.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }

        feedback.textContent = fieldData.errorMessage;
        feedback.style.display = 'block';

        // Animación de shake
        field.style.animation = 'shake 0.5s ease-in-out';
        setTimeout(() => {
            field.style.animation = '';
        }, 500);
    }

    /**
     * Mostrar éxito en campo
     */
    showFieldSuccess(fieldData) {
        const field = fieldData.element;
        const container = field.closest('.form-group') || field.closest('.mb-4') || field.closest('.mb-3');
        
        if (!container) return;

        let feedback = container.querySelector('.valid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'valid-feedback';
            field.parentNode.appendChild(feedback);
        }

        feedback.textContent = fieldData.successMessage || '✓ Válido';
        feedback.style.display = 'block';
    }

    /**
     * Limpiar mensaje del campo
     */
    clearFieldMessage(fieldData) {
        const field = fieldData.element;
        const container = field.closest('.form-group') || field.closest('.mb-4') || field.closest('.mb-3');
        
        if (container) {
            const feedback = container.querySelector('.invalid-feedback');
            if (feedback) {
                feedback.style.display = 'none';
            }
        }
    }

    /**
     * Configurar eventos del formulario
     */
    setupFormEvents(formElement, formData) {
        formElement.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit(formData);
        });

        // Validación en tiempo real del formulario completo
        formElement.addEventListener('input', () => {
            this.updateFormValidation(formData);
        });
    }

    /**
     * Manejar envío del formulario
     */
    handleFormSubmit(formData) {
        // Marcar todos los campos como tocados
        formData.fields.forEach(fieldData => {
            fieldData.isTouched = true;
            this.validateField(fieldData, formData);
        });

        if (formData.isValid) {
            this.processFormSubmission(formData);
        } else {
            this.handleFormErrors(formData);
        }
    }

    /**
     * Procesar envío válido del formulario
     */
    processFormSubmission(formData) {
        const formElement = formData.element;
        
        if (formData.type === 'config') {
            this.handleConfigFormSubmission(formData);
        } else if (formData.type === 'start') {
            this.handleStartFormSubmission(formData);
        }
    }

    /**
     * Manejar envío del formulario de configuración
     */
    handleConfigFormSubmission(formData) {
        const formElement = formData.element;
        const submitBtn = formElement.querySelector('#configureButton');
        
        if (submitBtn) {
            this.updateSubmitButton(submitBtn, 'loading', 'Analizando datos...');
        }

        // Mostrar loading
        if (window.loadingManager) {
            window.loadingManager.show('Analizando datos históricos...');
        }

        // Enviar formulario
        setTimeout(() => {
            formElement.submit();
        }, 100);
    }

    /**
     * Manejar envío del formulario de inicio
     */
    handleStartFormSubmission(formData) {
        const formElement = formData.element;
        const submitBtn = formElement.querySelector('#startSimulationBtn');
        
        if (submitBtn) {
            this.updateSubmitButton(submitBtn, 'loading', 'Iniciando simulación...');
        }

        // Mostrar confirmación
        const confirmed = confirm(
            '¿Está seguro de que desea iniciar la simulación?\n\n' +
            'Este proceso puede tomar varios minutos y generará predicciones ' +
            'basadas en los datos históricos analizados.'
        );

        if (confirmed) {
            if (window.loadingManager) {
                window.loadingManager.show('Iniciando simulación...');
            }
            
            setTimeout(() => {
                formElement.submit();
            }, 100);
        } else {
            this.updateSubmitButton(submitBtn, 'normal', 'Iniciar Simulación');
        }
    }

    /**
     * Actualizar botón de envío
     */
    updateSubmitButton(button, state, text) {
        const buttonText = button.querySelector('.button-text');
        const buttonLoading = button.querySelector('.button-loading');

        switch (state) {
            case 'loading':
                if (buttonText) buttonText.classList.add('d-none');
                if (buttonLoading) buttonLoading.classList.remove('d-none');
                button.disabled = true;
                break;
            case 'normal':
                if (buttonText) {
                    buttonText.classList.remove('d-none');
                    buttonText.textContent = text;
                }
                if (buttonLoading) buttonLoading.classList.add('d-none');
                button.disabled = false;
                break;
        }
    }

    /**
     * Manejar errores del formulario
     */
    handleFormErrors(formData) {
        const errors = [];
        
        formData.fields.forEach((fieldData, fieldName) => {
            if (!fieldData.isValid && fieldData.errorMessage) {
                errors.push(fieldData.errorMessage);
            }
        });

        if (errors.length > 0) {
            this.showFormErrorMessage(errors);
            
            // Enfocar primer campo con error
            const firstErrorField = Array.from(formData.fields.values())
                .find(fieldData => !fieldData.isValid);
            
            if (firstErrorField) {
                firstErrorField.element.focus();
                firstErrorField.element.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }
        }
    }

    /**
     * Mostrar mensaje de error del formulario
     */
    showFormErrorMessage(errors) {
        if (window.simulationCore) {
            const errorMessage = errors.join('<br>');
            window.simulationCore.showMessage(errorMessage, 'error');
        }
    }

    /**
     * Actualizar validación del formulario completo
     */
    updateFormValidation(formData) {
        let allValid = true;
        let touchedFields = 0;

        formData.fields.forEach(fieldData => {
            if (fieldData.isTouched) {
                touchedFields++;
                if (!fieldData.isValid) {
                    allValid = false;
                }
            }
        });

        formData.isValid = allValid && touchedFields > 0;
        formData.touched = touchedFields > 0;

        // Actualizar estado del botón de envío
        this.updateSubmitButtonState(formData);
    }

    /**
     * Actualizar estado del botón de envío
     */
    updateSubmitButtonState(formData) {
        const formElement = formData.element;
        const submitBtn = formElement.querySelector('button[type="submit"]');
        
        if (submitBtn && !submitBtn.disabled) {
            if (formData.isValid) {
                submitBtn.classList.remove('btn-outline-primary');
                submitBtn.classList.add('btn-primary');
                submitBtn.removeAttribute('disabled');
            } else if (formData.touched) {
                submitBtn.classList.add('btn-outline-primary');
                submitBtn.classList.remove('btn-primary');
            }
        }
    }

    /**
     * Inicializar todos los formularios
     */
    initializeForms() {
        // Este método se ejecuta después de que se configuran los eventos
        console.log('Sistema de formularios inicializado');
    }

    /**
     * Validar formulario específico
     */
    validateForm(formType) {
        const formData = this.forms.get(formType);
        if (!formData) return false;

        let isValid = true;
        formData.fields.forEach(fieldData => {
            if (!this.validateField(fieldData, formData)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * Obtener datos del formulario
     */
    getFormData(formType) {
        const formData = this.forms.get(formType);
        if (!formData) return null;

        const data = {};
        formData.fields.forEach((fieldData, fieldName) => {
            data[fieldName] = fieldData.value;
        });

        return data;
    }

    /**
     * Resetear formulario
     */
    resetForm(formType) {
        const formData = this.forms.get(formType);
        if (!formData) return;

        formData.element.reset();
        formData.fields.forEach(fieldData => {
            fieldData.isValid = false;
            fieldData.isTouched = false;
            fieldData.value = '';
            fieldData.errorMessage = '';
            this.updateFieldUI(fieldData);
        });

        formData.isValid = false;
        formData.touched = false;
    }

    /**
     * Destruir instancia
     */
    destroy() {
        this.forms.clear();
        this.validators.clear();
    }
}

// Crear instancia global
const simulationForms = new SimulationForms();

// Exportar para uso global
window.SimulationForms = SimulationForms;
window.simulationForms = simulationForms;