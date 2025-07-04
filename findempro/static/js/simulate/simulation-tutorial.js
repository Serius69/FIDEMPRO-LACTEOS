/**
 * SIMULATION TUTORIAL - Sistema de tutorial interactivo
 * Guía paso a paso para nuevos usuarios
 */

class SimulationTutorial {
    constructor() {
        this.currentStep = 0;
        this.isActive = false;
        this.steps = [
            {
                element: '#questionaryField',
                title: 'Paso 1: Seleccionar Cuestionario',
                text: 'Seleccione el cuestionario que contiene los datos históricos de demanda de su producto. Estos datos son esenciales para el análisis estadístico y la generación de predicciones precisas.',
                position: 'right',
                highlight: true,
                validation: () => document.getElementById('selected_questionary_result')?.value
            },
            {
                element: '#timeConfigFields',
                title: 'Paso 2: Configurar Período de Tiempo',
                text: 'Defina la duración y unidad de tiempo para su simulación. Puede elegir entre días, semanas o meses según las necesidades de planificación de su negocio.',
                position: 'left',
                highlight: true,
                validation: () => {
                    const quantity = document.getElementById('selected_quantity_time')?.value;
                    const unit = document.getElementById('selected_unit_time')?.value;
                    return quantity && unit && parseInt(quantity) > 0;
                }
            },
            {
                element: '#configureButton',
                title: 'Paso 3: Analizar Datos Estadísticos',
                text: 'Haga clic aquí para analizar los datos históricos. El sistema aplicará pruebas estadísticas (Kolmogorov-Smirnov) para encontrar la mejor distribución de probabilidad que se ajuste a sus datos.',
                position: 'top',
                highlight: true,
                action: 'pulse'
            },
            {
                element: '.model-summary',
                title: 'Paso 4: Revisar Modelo Estadístico',
                text: 'Una vez configurado, aquí verá el resumen del modelo estadístico, incluyendo la distribución seleccionada, parámetros calculados y gráficos de validación.',
                position: 'left',
                highlight: true,
                conditional: () => document.querySelector('.model-summary')
            },
            {
                element: '#startSimulationBtn',
                title: 'Paso 5: Ejecutar Simulación',
                text: 'Finalmente, inicie la simulación para generar predicciones de demanda. El proceso puede tomar varios minutos dependiendo de la complejidad de los cálculos.',
                position: 'top',
                highlight: true,
                action: 'pulse',
                conditional: () => document.getElementById('startSimulationBtn')
            }
        ];
        
        this.config = {
            spotlightPadding: 10,
            animationDuration: 400,
            autoAdvanceDelay: 0, // 0 = manual only
            showProgress: true,
            allowSkip: true,
            storageKey: 'simulationTutorialCompleted'
        };
        
        this.elements = {
            overlay: null,
            spotlight: null,
            tooltip: null,
            progressBar: null
        };
        
        this.init();
    }

    /**
     * Inicializar el sistema de tutorial
     */
    init() {
        this.createTutorialElements();
        this.setupEventListeners();
    }

    /**
     * Crear elementos del tutorial
     */
    createTutorialElements() {
        // Verificar si ya existen los elementos
        if (document.getElementById('tutorialOverlay')) {
            this.elements.overlay = document.getElementById('tutorialOverlay');
            this.elements.spotlight = document.getElementById('tutorialSpotlight');
            this.elements.tooltip = document.getElementById('tutorialTooltip');
            return;
        }

        // Crear overlay principal
        this.elements.overlay = document.createElement('div');
        this.elements.overlay.id = 'tutorialOverlay';
        this.elements.overlay.className = 'tutorial-overlay';
        this.elements.overlay.style.display = 'none';

        // Crear spotlight
        this.elements.spotlight = document.createElement('div');
        this.elements.spotlight.id = 'tutorialSpotlight';
        this.elements.spotlight.className = 'tutorial-spotlight';

        // Crear tooltip
        this.elements.tooltip = document.createElement('div');
        this.elements.tooltip.id = 'tutorialTooltip';
        this.elements.tooltip.className = 'tutorial-tooltip';
        this.elements.tooltip.innerHTML = `
            <div class="tutorial-header">
                <h5 id="tutorialTitle">Título del Tutorial</h5>
                <div class="tutorial-progress" id="tutorialProgress" style="display: ${this.config.showProgress ? 'block' : 'none'}">
                    <div class="progress">
                        <div class="progress-bar" id="tutorialProgressBar" role="progressbar"></div>
                    </div>
                    <small class="text-muted">Paso <span id="tutorialCurrentStep">1</span> de <span id="tutorialTotalSteps">${this.steps.length}</span></small>
                </div>
            </div>
            <p id="tutorialText">Texto del tutorial</p>
            <div class="tutorial-actions">
                <div class="btn-group w-100">
                    <button class="btn btn-outline-secondary" id="tutorialSkipBtn" style="display: ${this.config.allowSkip ? 'block' : 'none'}">
                        <i class="bx bx-x me-1"></i>Omitir Tutorial
                    </button>
                    <button class="btn btn-outline-primary" id="tutorialPrevBtn" style="display: none;">
                        <i class="bx bx-chevron-left me-1"></i>Anterior
                    </button>
                    <button class="btn btn-primary" id="tutorialNextBtn">
                        <i class="bx bx-chevron-right ms-1"></i>Siguiente
                    </button>
                </div>
            </div>
        `;

        // Ensamblar elementos
        this.elements.overlay.appendChild(this.elements.spotlight);
        this.elements.overlay.appendChild(this.elements.tooltip);
        document.body.appendChild(this.elements.overlay);

        // Obtener referencias a elementos internos
        this.elements.progressBar = document.getElementById('tutorialProgressBar');
    }

    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Botón siguiente
        const nextBtn = document.getElementById('tutorialNextBtn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextStep());
        }

        // Botón anterior
        const prevBtn = document.getElementById('tutorialPrevBtn');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousStep());
        }

        // Botón omitir
        const skipBtn = document.getElementById('tutorialSkipBtn');
        if (skipBtn) {
            skipBtn.addEventListener('click', () => this.end());
        }

        // Click en overlay para cerrar
        if (this.elements.overlay) {
            this.elements.overlay.addEventListener('click', (e) => {
                if (e.target === this.elements.overlay) {
                    this.end();
                }
            });
        }

        // Tecla Escape para cerrar
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isActive) {
                this.end();
            }
        });

        // Resize window
        window.addEventListener('resize', () => {
            if (this.isActive) {
                this.updateSpotlight();
            }
        });
    }

    /**
     * Iniciar el tutorial
     */
    start() {
        if (this.isActive) return;

        this.isActive = true;
        this.currentStep = 0;
        
        // Mostrar overlay
        if (this.elements.overlay) {
            this.elements.overlay.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }

        // Iniciar primer paso
        this.showStep(this.currentStep);
        
        // Analytics (opcional)
        this.trackEvent('tutorial_started');
    }

    /**
     * Finalizar el tutorial
     */
    end() {
        if (!this.isActive) return;

        this.isActive = false;
        
        // Ocultar overlay
        if (this.elements.overlay) {
            this.elements.overlay.style.display = 'none';
            document.body.style.overflow = '';
        }

        // Marcar como completado
        this.markAsCompleted();
        
        // Analytics
        this.trackEvent('tutorial_completed', { steps_completed: this.currentStep + 1 });
    }

    /**
     * Siguiente paso
     */
    nextStep() {
        // Validar paso actual si tiene validación
        const currentStepData = this.steps[this.currentStep];
        if (currentStepData?.validation && !currentStepData.validation()) {
            this.showValidationMessage();
            return;
        }

        this.currentStep++;
        
        if (this.currentStep >= this.steps.length) {
            this.end();
            return;
        }

        this.showStep(this.currentStep);
    }

    /**
     * Paso anterior
     */
    previousStep() {
        if (this.currentStep <= 0) return;

        this.currentStep--;
        this.showStep(this.currentStep);
    }

    /**
     * Mostrar paso específico
     */
    showStep(stepIndex) {
        const step = this.steps[stepIndex];
        if (!step) return;

        // Verificar condición si existe
        if (step.conditional && !step.conditional()) {
            // Saltar este paso
            if (stepIndex < this.steps.length - 1) {
                this.currentStep = stepIndex + 1;
                this.showStep(this.currentStep);
            } else {
                this.end();
            }
            return;
        }

        const element = document.querySelector(step.element);
        if (!element) {
            console.warn(`Tutorial: Element not found: ${step.element}`);
            // Intentar siguiente paso
            if (stepIndex < this.steps.length - 1) {
                this.currentStep = stepIndex + 1;
                this.showStep(this.currentStep);
            } else {
                this.end();
            }
            return;
        }

        // Scroll al elemento si es necesario
        this.scrollToElement(element);

        // Actualizar spotlight
        this.updateSpotlight(element, step);

        // Actualizar tooltip
        this.updateTooltip(step, element);

        // Actualizar controles
        this.updateControls();

        // Actualizar progreso
        this.updateProgress();

        // Aplicar acción especial si existe
        if (step.action) {
            this.applyStepAction(element, step.action);
        }

        // Analytics
        this.trackEvent('tutorial_step_viewed', { 
            step: stepIndex + 1, 
            element: step.element 
        });
    }

    /**
     * Scroll al elemento
     */
    scrollToElement(element) {
        const rect = element.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        
        // Solo hacer scroll si el elemento no está completamente visible
        if (rect.top < 100 || rect.bottom > viewportHeight - 100) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'center'
            });
        }
    }

    /**
     * Actualizar spotlight
     */
    updateSpotlight(element, step) {
        if (!element || !this.elements.spotlight) return;

        // Esperar un poco para que el scroll termine
        setTimeout(() => {
            const rect = element.getBoundingClientRect();
            const padding = step?.highlight ? this.config.spotlightPadding : 0;

            this.elements.spotlight.style.top = (rect.top - padding) + 'px';
            this.elements.spotlight.style.left = (rect.left - padding) + 'px';
            this.elements.spotlight.style.width = (rect.width + padding * 2) + 'px';
            this.elements.spotlight.style.height = (rect.height + padding * 2) + 'px';
            this.elements.spotlight.style.transition = `all ${this.config.animationDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        }, 100);
    }

    /**
     * Actualizar tooltip
     */
    updateTooltip(step, element) {
        if (!this.elements.tooltip) return;

        // Actualizar contenido
        const titleElement = document.getElementById('tutorialTitle');
        const textElement = document.getElementById('tutorialText');

        if (titleElement) titleElement.textContent = step.title;
        if (textElement) textElement.innerHTML = step.text;

        // Posicionar tooltip
        setTimeout(() => {
            this.positionTooltip(step, element);
        }, 150);
    }

    /**
     * Posicionar tooltip
     */
    positionTooltip(step, element) {
        if (!element || !this.elements.tooltip) return;

        const rect = element.getBoundingClientRect();
        const tooltipRect = this.elements.tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let top = rect.top;
        let left = rect.right + 20;

        // Ajustar según posición preferida
        switch (step.position) {
            case 'left':
                left = rect.left - tooltipRect.width - 20;
                break;
            case 'top':
                top = rect.top - tooltipRect.height - 20;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'bottom':
                top = rect.bottom + 20;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'right':
            default:
                // Ya está configurado arriba
                break;
        }

        // Asegurar que esté dentro del viewport
        if (left < 20) {
            left = 20;
        } else if (left + tooltipRect.width > viewportWidth - 20) {
            left = viewportWidth - tooltipRect.width - 20;
        }

        if (top < 20) {
            top = 20;
        } else if (top + tooltipRect.height > viewportHeight - 20) {
            top = viewportHeight - tooltipRect.height - 20;
        }

        this.elements.tooltip.style.top = top + 'px';
        this.elements.tooltip.style.left = left + 'px';
        this.elements.tooltip.style.transition = `all ${this.config.animationDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
    }

    /**
     * Actualizar controles
     */
    updateControls() {
        const prevBtn = document.getElementById('tutorialPrevBtn');
        const nextBtn = document.getElementById('tutorialNextBtn');

        if (prevBtn) {
            prevBtn.style.display = this.currentStep > 0 ? 'block' : 'none';
        }

        if (nextBtn) {
            const isLastStep = this.currentStep >= this.steps.length - 1;
            nextBtn.innerHTML = isLastStep 
                ? '<i class="bx bx-check me-1"></i>Finalizar'
                : '<i class="bx bx-chevron-right ms-1"></i>Siguiente';
        }
    }

    /**
     * Actualizar progreso
     */
    updateProgress() {
        if (!this.config.showProgress) return;

        const currentStepSpan = document.getElementById('tutorialCurrentStep');
        const progressBar = this.elements.progressBar;

        if (currentStepSpan) {
            currentStepSpan.textContent = this.currentStep + 1;
        }

        if (progressBar) {
            const progress = ((this.currentStep + 1) / this.steps.length) * 100;
            progressBar.style.width = progress + '%';
            progressBar.setAttribute('aria-valuenow', progress);
        }
    }

    /**
     * Aplicar acción especial al paso
     */
    applyStepAction(element, action) {
        switch (action) {
            case 'pulse':
                element.classList.add('pulse-animation');
                setTimeout(() => {
                    element.classList.remove('pulse-animation');
                }, 3000);
                break;
            case 'highlight':
                element.style.boxShadow = '0 0 20px rgba(33, 150, 243, 0.6)';
                setTimeout(() => {
                    element.style.boxShadow = '';
                }, 2000);
                break;
            case 'bounce':
                element.style.animation = 'bounceIn 0.8s ease-out';
                setTimeout(() => {
                    element.style.animation = '';
                }, 800);
                break;
        }
    }

    /**
     * Mostrar mensaje de validación
     */
    showValidationMessage() {
        const step = this.steps[this.currentStep];
        const element = document.querySelector(step.element);
        
        if (element) {
            // Crear mensaje temporal
            const message = document.createElement('div');
            message.className = 'tutorial-validation-message';
            message.innerHTML = `
                <i class="bx bx-info-circle me-2"></i>
                Complete este paso antes de continuar
            `;
            message.style.cssText = `
                position: absolute;
                top: -40px;
                left: 50%;
                transform: translateX(-50%);
                background: #fff3cd;
                color: #856404;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 0.875rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                z-index: 10002;
                animation: fadeInUp 0.3s ease-out;
            `;

            // Posicionar relativo al elemento
            const rect = element.getBoundingClientRect();
            message.style.position = 'fixed';
            message.style.top = (rect.top - 50) + 'px';
            message.style.left = (rect.left + rect.width / 2) + 'px';

            document.body.appendChild(message);

            // Remover después de 3 segundos
            setTimeout(() => {
                if (message.parentNode) {
                    message.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => {
                        message.remove();
                    }, 300);
                }
            }, 3000);

            // Enfocar elemento si es posible
            if (element.focus) {
                element.focus();
            }
        }
    }

    /**
     * Marcar tutorial como completado
     */
    markAsCompleted() {
        try {
            localStorage.setItem(this.config.storageKey, 'true');
            localStorage.setItem(this.config.storageKey + '_date', new Date().toISOString());
        } catch (error) {
            console.warn('Could not save tutorial completion status:', error);
        }
    }

    /**
     * Verificar si el tutorial fue completado
     */
    isCompleted() {
        try {
            return localStorage.getItem(this.config.storageKey) === 'true';
        } catch (error) {
            return false;
        }
    }

    /**
     * Resetear estado del tutorial
     */
    reset() {
        try {
            localStorage.removeItem(this.config.storageKey);
            localStorage.removeItem(this.config.storageKey + '_date');
        } catch (error) {
            console.warn('Could not reset tutorial status:', error);
        }
    }

    /**
     * Tracking de eventos (para analytics)
     */
    trackEvent(eventName, properties = {}) {
        // Implementar según el sistema de analytics utilizado
        // Por ejemplo: Google Analytics, Mixpanel, etc.
        
        if (window.gtag) {
            gtag('event', eventName, {
                event_category: 'tutorial',
                ...properties
            });
        }
        
        if (window.dataLayer) {
            window.dataLayer.push({
                event: eventName,
                category: 'tutorial',
                ...properties
            });
        }

        console.log('Tutorial Event:', eventName, properties);
    }

    /**
     * Obtener estadísticas del tutorial
     */
    getStats() {
        return {
            totalSteps: this.steps.length,
            currentStep: this.currentStep + 1,
            isActive: this.isActive,
            isCompleted: this.isCompleted(),
            completionDate: localStorage.getItem(this.config.storageKey + '_date')
        };
    }

    /**
     * Actualizar configuración
     */
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }

    /**
     * Destruir instancia del tutorial
     */
    destroy() {
        this.end();
        
        if (this.elements.overlay && this.elements.overlay.parentNode) {
            this.elements.overlay.parentNode.removeChild(this.elements.overlay);
        }

        // Limpiar referencias
        this.elements = {};
        this.isActive = false;
        this.currentStep = 0;
    }
}

// Crear instancia global
const tutorialInstance = new SimulationTutorial();

// Funciones globales para compatibilidad con el template existente
window.startTutorial = () => tutorialInstance.start();
window.nextTutorialStep = () => tutorialInstance.nextStep();
window.skipTutorial = () => tutorialInstance.end();

// Exportar clase para uso avanzado
window.SimulationTutorial = {
    start: () => tutorialInstance.start(),
    end: () => tutorialInstance.end(),
    nextStep: () => tutorialInstance.nextStep(),
    previousStep: () => tutorialInstance.previousStep(),
    reset: () => tutorialInstance.reset(),
    isCompleted: () => tutorialInstance.isCompleted(),
    getStats: () => tutorialInstance.getStats(),
    instance: tutorialInstance
};