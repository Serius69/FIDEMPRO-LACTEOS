/**
 * SIMULATION CORE - Sistema de simulación principal
 * Maneja toda la lógica central del sistema de simulación
 */

class SimulationCore {
    constructor() {
        this.initialized = false;
        this.config = {
            apiEndpoints: {
                configure: '/simulate/configure/',
                start: '/simulate/start/',
                cancel: '/simulate/cancel/',
                status: '/simulate/status/'
            },
            validation: {
                minQuantity: 1,
                maxQuantity: 365,
                minDemandData: 10
            },
            charts: {
                maxHeight: 400,
                animationDuration: 1000
            }
        };
        this.state = {
            currentStep: 1,
            isLoading: false,
            simulationStarted: false,
            validationErrors: []
        };
        this.init();
    }

    /**
     * Inicializar el sistema de simulación
     */
    init() {
        if (this.initialized) return;
        
        document.addEventListener('DOMContentLoaded', () => {
            this.setupEventListeners();
            this.initializeComponents();
            this.loadUserPreferences();
            this.checkSimulationStatus();
            this.initialized = true;
            
            console.log('SimulationCore initialized successfully');
        });
    }

    /**
     * Configurar todos los event listeners
     */
    setupEventListeners() {
        // Formulario de configuración
        const configForm = document.getElementById('simulationConfigForm');
        if (configForm) {
            configForm.addEventListener('submit', (e) => this.handleConfigFormSubmit(e));
        }

        // Formulario de inicio de simulación
        const startForm = document.getElementById('simulationStartForm');
        if (startForm) {
            startForm.addEventListener('submit', (e) => this.handleStartFormSubmit(e));
        }

        // Selector de cuestionario
        const questionarySelect = document.getElementById('selected_questionary_result');
        if (questionarySelect) {
            questionarySelect.addEventListener('change', (e) => this.handleQuestionaryChange(e));
        }

        // Input de cantidad de tiempo
        const quantityInput = document.getElementById('selected_quantity_time');
        if (quantityInput) {
            quantityInput.addEventListener('input', (e) => this.handleQuantityChange(e));
            quantityInput.addEventListener('blur', (e) => this.validateQuantityInput(e));
        }

        // Botones de ecuaciones
        document.addEventListener('click', (e) => {
            if (e.target.matches('[id^="showMore"]')) {
                const areaId = e.target.id.replace('showMore', '');
                EquationManager.toggleEquations(parseInt(areaId));
            }
        });

        // Botones de cierre de mensajes
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-close')) {
                this.hideMessage(e.target.closest('.error-message, .success-message'));
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));

        // Window events
        window.addEventListener('beforeunload', (e) => this.handlePageUnload(e));
        window.addEventListener('load', () => this.hideLoading());
    }

    /**
     * Inicializar componentes del sistema
     */
    initializeComponents() {
        // Inicializar tooltips
        this.initializeTooltips();
        
        // Inicializar charts
        this.initializeCharts();
        
        // Configurar validación de formularios
        this.setupFormValidation();
        
        // Verificar tutorial
        this.checkTutorialStatus();
        
        // Inicializar indicadores de progreso
        this.updateStepIndicator(this.state.currentStep);
    }

    /**
     * Manejar envío del formulario de configuración
     */
    async handleConfigFormSubmit(e) {
        e.preventDefault();
        
        try {
            // Validar formulario
            const validation = this.validateConfigForm();
            if (!validation.isValid) {
                this.showValidationErrors(validation.errors);
                return;
            }

            // Mostrar confirmación
            const formData = this.getFormData(e.target);
            const confirmed = await this.showConfirmationDialog(formData);
            
            if (!confirmed) return;

            // Procesar formulario
            this.showLoading('Analizando datos históricos...');
            this.updateStepIndicator(2);
            
            // Enviar formulario
            e.target.submit();
            
        } catch (error) {
            console.error('Error in config form submission:', error);
            this.showMessage('Error al procesar la configuración. Intente nuevamente.', 'error');
            this.hideLoading();
        }
    }

    /**
     * Manejar envío del formulario de inicio
     */
    async handleStartFormSubmit(e) {
        e.preventDefault();
        
        try {
            const confirmed = await this.showStartConfirmationDialog();
            if (!confirmed) return;

            this.showLoading('Iniciando simulación...');
            this.updateStepIndicator(3);
            this.state.simulationStarted = true;
            
            // Guardar estado en sessionStorage
            sessionStorage.setItem('simulationStarted', 'true');
            sessionStorage.setItem('simulationStartTime', new Date().toISOString());
            
            // Enviar formulario
            e.target.submit();
            
        } catch (error) {
            console.error('Error starting simulation:', error);
            this.showMessage('Error al iniciar la simulación. Intente nuevamente.', 'error');
            this.hideLoading();
        }
    }

    /**
     * Validar formulario de configuración
     */
    validateConfigForm() {
        const errors = [];
        const questionarySelect = document.getElementById('selected_questionary_result');
        const quantityInput = document.getElementById('selected_quantity_time');
        const unitSelect = document.getElementById('selected_unit_time');

        // Reset validation states
        [questionarySelect, quantityInput, unitSelect].forEach(input => {
            if (input) input.classList.remove('is-invalid');
        });

        // Validar selección de cuestionario
        if (!questionarySelect?.value) {
            questionarySelect?.classList.add('is-invalid');
            errors.push('Debe seleccionar un cuestionario válido');
        }

        // Validar cantidad de tiempo
        const quantity = parseInt(quantityInput?.value);
        if (!quantity || quantity < this.config.validation.minQuantity || quantity > this.config.validation.maxQuantity) {
            quantityInput?.classList.add('is-invalid');
            errors.push(`La duración debe estar entre ${this.config.validation.minQuantity} y ${this.config.validation.maxQuantity}`);
        }

        // Validar unidad de tiempo
        if (!unitSelect?.value) {
            unitSelect?.classList.add('is-invalid');
            errors.push('Debe seleccionar una unidad de tiempo');
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Mostrar errores de validación
     */
    showValidationErrors(errors) {
        const errorMessage = errors.join('<br>');
        this.showMessage(errorMessage, 'error');
        
        // Scroll to first error
        const firstInvalid = document.querySelector('.is-invalid');
        if (firstInvalid) {
            firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstInvalid.focus();
        }
    }

    /**
     * Obtener datos del formulario
     */
    getFormData(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        // Agregar información adicional
        const questionarySelect = document.getElementById('selected_questionary_result');
        if (questionarySelect?.selectedOptions[0]) {
            const option = questionarySelect.selectedOptions[0];
            data.product = option.dataset.product;
            data.date = option.dataset.date;
        }
        
        return data;
    }

    /**
     * Mostrar diálogo de confirmación para configuración
     */
    async showConfirmationDialog(formData) {
        const message = `¿Desea configurar la simulación con los siguientes parámetros?\n\n` +
                       `Producto: ${formData.product || 'No especificado'}\n` +
                       `Duración: ${formData.selected_quantity_time} ${this.getUnitText(formData.selected_unit_time)}\n` +
                       `Fecha del cuestionario: ${formData.date ? new Date(formData.date).toLocaleDateString('es-ES') : 'No especificada'}`;
        
        return confirm(message);
    }

    /**
     * Mostrar diálogo de confirmación para inicio
     */
    async showStartConfirmationDialog() {
        const message = '¿Está seguro de que desea iniciar la simulación?\n\n' +
                       'Este proceso puede tomar varios minutos dependiendo de los parámetros configurados.\n' +
                       'Se ejecutarán cálculos estadísticos complejos y se generarán múltiples escenarios.';
        
        return confirm(message);
    }

    /**
     * Manejar cambio en selector de cuestionario
     */
    handleQuestionaryChange(e) {
        const selectedOption = e.target.selectedOptions[0];
        
        if (selectedOption?.value) {
            const product = selectedOption.dataset.product;
            const date = selectedOption.dataset.date;
            
            this.showMessage(
                `<strong>Cuestionario seleccionado:</strong><br>
                Producto: ${product}<br>
                Fecha: ${new Date(date).toLocaleDateString('es-ES')}`, 
                'success'
            );
            
            this.updateStepIndicator(2);
            this.saveUserPreference('lastSelectedQuestionary', selectedOption.value);
        }
    }

    /**
     * Manejar cambio en input de cantidad
     */
    handleQuantityChange(e) {
        const value = parseInt(e.target.value);
        
        // Aplicar límites
        if (value < this.config.validation.minQuantity) {
            e.target.value = this.config.validation.minQuantity;
        } else if (value > this.config.validation.maxQuantity) {
            e.target.value = this.config.validation.maxQuantity;
        }
        
        // Validar en tiempo real
        this.validateQuantityInput(e);
    }

    /**
     * Validar input de cantidad
     */
    validateQuantityInput(e) {
        const value = parseInt(e.target.value);
        const isValid = value >= this.config.validation.minQuantity && 
                        value <= this.config.validation.maxQuantity;
        
        e.target.classList.toggle('is-invalid', !isValid);
        
        if (!isValid) {
            this.showMessage(
                `La cantidad debe estar entre ${this.config.validation.minQuantity} y ${this.config.validation.maxQuantity}`,
                'error'
            );
        }
    }

    /**
     * Manejar atajos de teclado
     */
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + H para ayuda
        if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
            e.preventDefault();
            if (window.SimulationTutorial) {
                SimulationTutorial.start();
            }
        }
        
        // Escape para cerrar overlays
        if (e.key === 'Escape') {
            this.hideLoading();
            if (window.SimulationTutorial) {
                SimulationTutorial.end();
            }
        }
    }

    /**
     * Manejar descarga de página
     */
    handlePageUnload(e) {
        if (this.state.simulationStarted) {
            e.preventDefault();
            e.returnValue = '¿Está seguro de que desea salir? La simulación se perderá.';
            return e.returnValue;
        }
    }

    /**
     * Actualizar indicador de pasos
     */
    updateStepIndicator(step) {
        this.state.currentStep = step;
        
        for (let i = 1; i <= 3; i++) {
            const stepElement = document.getElementById(`step${i}`);
            if (!stepElement) continue;
            
            stepElement.classList.remove('active', 'completed');
            
            if (i < step) {
                stepElement.classList.add('completed');
            } else if (i === step) {
                stepElement.classList.add('active');
            }
        }
    }

    /**
     * Mostrar overlay de carga
     */
    showLoading(message = 'Procesando...') {
        this.state.isLoading = true;
        const loadingOverlay = document.getElementById('loadingOverlay');
        
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
            const loadingText = loadingOverlay.querySelector('p.mt-3');
            if (loadingText) {
                loadingText.textContent = message;
            }
        }
    }

    /**
     * Ocultar overlay de carga
     */
    hideLoading() {
        this.state.isLoading = false;
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    /**
     * Mostrar mensaje al usuario
     */
    showMessage(message, type = 'info', duration = 5000) {
        const messageContainer = document.getElementById('messageContainer');
        if (!messageContainer) return;

        const alertClass = type === 'error' ? 'error-message' : 'success-message';
        const icon = type === 'error' ? 'bx-error' : 'bx-check-circle';
        
        const messageElement = document.createElement('div');
        messageElement.className = alertClass;
        messageElement.innerHTML = `
            <i class="bx ${icon} me-2"></i>
            ${message}
            <button type="button" class="btn-close" aria-label="Cerrar">&times;</button>
        `;
        
        messageContainer.appendChild(messageElement);
        
        // Auto-hide after duration
        if (duration > 0) {
            setTimeout(() => {
                this.hideMessage(messageElement);
            }, duration);
        }
    }

    /**
     * Ocultar mensaje
     */
    hideMessage(messageElement) {
        if (!messageElement) return;
        
        messageElement.style.animation = 'fadeOut 0.5s ease-out';
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 500);
    }

    /**
     * Inicializar tooltips
     */
    initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    /**
     * Inicializar gráficos
     */
    initializeCharts() {
        // Agregar funcionalidad de zoom a los gráficos
        document.querySelectorAll('.demand-chart-container img').forEach(img => {
            img.style.cursor = 'zoom-in';
            img.addEventListener('click', (e) => {
                this.openChartFullscreen(e.target);
            });
        });
    }

    /**
     * Abrir gráfico en pantalla completa
     */
    openChartFullscreen(imgElement) {
        const modal = document.createElement('div');
        modal.className = 'chart-fullscreen-modal';
        modal.innerHTML = `
            <div class="chart-fullscreen-overlay" onclick="this.parentElement.remove()">
                <div class="chart-fullscreen-content">
                    <img src="${imgElement.src}" alt="${imgElement.alt}" />
                    <button class="chart-close-btn" onclick="this.closest('.chart-fullscreen-modal').remove()">
                        <i class="bx bx-x"></i>
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Agregar estilos si no existen
        if (!document.getElementById('chart-fullscreen-styles')) {
            const styles = document.createElement('style');
            styles.id = 'chart-fullscreen-styles';
            styles.textContent = `
                .chart-fullscreen-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    z-index: 10000;
                }
                .chart-fullscreen-overlay {
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.9);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                }
                .chart-fullscreen-content {
                    position: relative;
                    max-width: 90%;
                    max-height: 90%;
                    cursor: default;
                }
                .chart-fullscreen-content img {
                    max-width: 100%;
                    max-height: 100%;
                    border-radius: 8px;
                }
                .chart-close-btn {
                    position: absolute;
                    top: -15px;
                    right: -15px;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    background: #f44336;
                    color: white;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 20px;
                }
            `;
            document.head.appendChild(styles);
        }
    }

    /**
     * Configurar validación de formularios
     */
    setupFormValidation() {
        // Validación en tiempo real
        const inputs = document.querySelectorAll('.form-control, .form-select');
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
            
            input.addEventListener('input', () => {
                if (input.classList.contains('is-invalid')) {
                    this.validateField(input);
                }
            });
        });
    }

    /**
     * Validar campo individual
     */
    validateField(field) {
        let isValid = true;
        let errorMessage = '';

        // Validaciones según el tipo de campo
        if (field.hasAttribute('required') && !field.value.trim()) {
            isValid = false;
            errorMessage = 'Este campo es requerido';
        } else if (field.type === 'number') {
            const value = parseFloat(field.value);
            const min = parseFloat(field.min);
            const max = parseFloat(field.max);
            
            if (field.value && (isNaN(value) || value < min || value > max)) {
                isValid = false;
                errorMessage = `El valor debe estar entre ${min} y ${max}`;
            }
        }

        // Aplicar estado de validación
        field.classList.toggle('is-invalid', !isValid);
        field.classList.toggle('is-valid', isValid && field.value.trim());

        // Mostrar/ocultar mensaje de error
        let feedbackElement = field.parentNode.querySelector('.invalid-feedback');
        if (!isValid && errorMessage) {
            if (!feedbackElement) {
                feedbackElement = document.createElement('div');
                feedbackElement.className = 'invalid-feedback';
                field.parentNode.appendChild(feedbackElement);
            }
            feedbackElement.textContent = errorMessage;
        } else if (feedbackElement) {
            feedbackElement.remove();
        }

        return isValid;
    }

    /**
     * Verificar estado del tutorial
     */
    checkTutorialStatus() {
        const tutorialCompleted = localStorage.getItem('simulationTutorialCompleted');
        if (!tutorialCompleted && window.SimulationTutorial) {
            setTimeout(() => {
                SimulationTutorial.start();
            }, 1500);
        }
    }

    /**
     * Verificar estado de la simulación
     */
    checkSimulationStatus() {
        const simulationStarted = sessionStorage.getItem('simulationStarted');
        if (simulationStarted === 'true') {
            this.state.simulationStarted = true;
            // Opcional: verificar con el servidor el estado actual
        }
    }

    /**
     * Cargar preferencias del usuario
     */
    loadUserPreferences() {
        const lastQuestionary = localStorage.getItem('lastSelectedQuestionary');
        if (lastQuestionary) {
            const questionarySelect = document.getElementById('selected_questionary_result');
            if (questionarySelect) {
                questionarySelect.value = lastQuestionary;
            }
        }
    }

    /**
     * Guardar preferencia del usuario
     */
    saveUserPreference(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (error) {
            console.warn('Could not save user preference:', error);
        }
    }

    /**
     * Obtener texto de unidad de tiempo
     */
    getUnitText(unit) {
        const units = {
            'days': 'días',
            'weeks': 'semanas',
            'months': 'meses'
        };
        return units[unit] || unit;
    }

    /**
     * Limpiar recursos
     */
    destroy() {
        // Remover event listeners globales
        document.removeEventListener('keydown', this.handleKeyboardShortcuts);
        window.removeEventListener('beforeunload', this.handlePageUnload);
        
        // Limpiar estado
        this.state = {
            currentStep: 1,
            isLoading: false,
            simulationStarted: false,
            validationErrors: []
        };
        
        this.initialized = false;
    }
}

/**
 * EQUATION MANAGER - Manejo de ecuaciones de áreas
 */
class EquationManager {
    static equationStates = {};

    /**
     * Toggle visibility of equations for an area
     */
    static toggleEquations(areaId) {
        const equationsContainer = document.getElementById(`equations${areaId}`);
        const button = document.getElementById(`showMore${areaId}`);
        const equations = equationsContainer?.querySelectorAll('.equation') || [];
        
        if (!equationsContainer || !button) return;

        if (!this.equationStates[areaId]) {
            this.equationStates[areaId] = { shown: 0, expanded: false };
        }
        
        const state = this.equationStates[areaId];
        
        if (!state.expanded) {
            // Show equations with animation
            const maxToShow = Math.min(state.shown + 3, equations.length);
            for (let i = state.shown; i < maxToShow; i++) {
                if (equations[i]) {
                    equations[i].style.display = 'block';
                    equations[i].style.animation = 'fadeInUp 0.4s ease-out';
                }
            }
            state.shown = maxToShow;
            
            if (state.shown >= equations.length) {
                button.innerHTML = '<i class="bx bx-hide me-1"></i>Ocultar Ecuaciones';
                state.expanded = true;
            } else {
                button.innerHTML = `<i class="bx bx-show me-1"></i>Ver Más (${equations.length - state.shown} restantes)`;
            }
        } else {
            // Hide all equations with animation
            equations.forEach((eq, index) => {
                if (eq) {
                    setTimeout(() => {
                        eq.style.animation = 'fadeOut 0.3s ease-out';
                        setTimeout(() => {
                            eq.style.display = 'none';
                        }, 300);
                    }, index * 50);
                }
            });
            
            setTimeout(() => {
                button.innerHTML = '<i class="bx bx-show me-1"></i>Ver Ecuaciones';
                state.shown = 0;
                state.expanded = false;
            }, equations.length * 50 + 300);
        }
    }

    /**
     * Initialize equations display for all areas
     */
    static initializeAll() {
        document.querySelectorAll('[id^="equations"]').forEach(container => {
            const areaId = container.id.replace('equations', '');
            const firstEquation = container.querySelector('.equation');
            const button = document.getElementById(`showMore${areaId}`);
            
            if (firstEquation && button) {
                firstEquation.style.display = 'block';
                this.equationStates[areaId] = { shown: 1, expanded: false };
                
                const totalEquations = container.querySelectorAll('.equation').length;
                if (totalEquations > 1) {
                    button.innerHTML = `<i class="bx bx-show me-1"></i>Ver Más (${totalEquations - 1} restantes)`;
                } else {
                    button.style.display = 'none';
                }
            }
        });
    }
}

// Inicializar el sistema cuando se carga el DOM
const simulationCore = new SimulationCore();

// Inicializar equations manager
document.addEventListener('DOMContentLoaded', () => {
    EquationManager.initializeAll();
});

// Exportar para uso global
window.SimulationCore = SimulationCore;
window.EquationManager = EquationManager;
window.simulationCore = simulationCore;