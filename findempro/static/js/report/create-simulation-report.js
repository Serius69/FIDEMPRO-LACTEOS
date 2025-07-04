/**
 * =================================================================
 * CREATE SIMULATION REPORT - JAVASCRIPT LOGIC
 * =================================================================
 */

/**
 * =================================================================
 * GLOBAL VARIABLES AND CONFIGURATION
 * =================================================================
 */

// DOM Elements Cache
let domElements = {};

// Form Configuration
const formConfig = {
    defaultValues: {
        precio_unitario: 100,
        costo_unitario: 60,
        demanda_inicial: 1000,
        gastos_fijos: 5000,
        inversion_inicial: 50000,
        tasa_crecimiento: 5,
        horizonte: 12
    },
    maxUpdateCalls: 4,
    updateCallCount: 0
};

/**
 * =================================================================
 * INITIALIZATION
 * =================================================================
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeDOMElements();
    initializeForm();
    initializeEventListeners();
    initializeTooltips();
    
    // Auto-load saved form data if available
    loadFormData();
    
    // Initialize form with default values
    populateDefaultValues();
    updatePreview();
    updateFormProgress();
});

/**
 * =================================================================
 * DOM ELEMENTS INITIALIZATION
 * =================================================================
 */

function initializeDOMElements() {
    // Form elements
    domElements.form = document.getElementById('simulationForm');
    domElements.loadingOverlay = document.getElementById('loadingOverlay');
    domElements.formProgress = document.getElementById('formProgress');
    
    // Input elements
    domElements.precioInput = document.getElementById('id_precio_unitario');
    domElements.costoInput = document.getElementById('id_costo_unitario');
    domElements.demandaInput = document.getElementById('id_demanda_inicial');
    domElements.gastosFijosInput = document.getElementById('id_gastos_fijos');
    domElements.inversionInput = document.getElementById('id_inversion_inicial');
    domElements.crecimientoInput = document.getElementById('id_tasa_crecimiento');
    domElements.horizonteInput = document.getElementById('id_horizonte');
    domElements.productSelect = document.getElementById('id_product');
    
    // Preview elements
    domElements.previewMargin = document.getElementById('preview-margin');
    domElements.previewBreakEven = document.getElementById('preview-break-even');
    domElements.previewRoi = document.getElementById('preview-roi');
    domElements.previewProfit = document.getElementById('preview-profit');
    domElements.previewPayback = document.getElementById('preview-payback');
    
    // Validation elements
    domElements.marginInfo = document.getElementById('marginInfo');
    domElements.marginValue = document.getElementById('marginValue');
    domElements.marginPercent = document.getElementById('marginPercent');
    
    // Risk assessment elements
    domElements.riskBar = document.getElementById('riskBar');
    domElements.riskLevel = document.getElementById('riskLevel');
    domElements.riskDescription = document.getElementById('riskDescription');
    
    // Button elements
    domElements.submitBtn = document.getElementById('submitBtn');
    domElements.submitText = document.getElementById('submitText');
    domElements.validateBtn = document.getElementById('validateForm');
    domElements.resetBtn = document.getElementById('resetForm');
    domElements.toggleAdvanced = document.getElementById('toggleAdvanced');
    domElements.advancedOptions = document.getElementById('advancedOptions');
    
    // Validation elements
    domElements.validationSuccess = document.getElementById('validationSuccess');
    domElements.validationErrors = document.getElementById('validationErrors');
    domElements.errorList = document.getElementById('errorList');
}

/**
 * =================================================================
 * FORM INITIALIZATION
 * =================================================================
 */

function initializeForm() {
    // Set up input field references for easier access
    const inputFields = [
        domElements.precioInput,
        domElements.costoInput,
        domElements.demandaInput,
        domElements.gastosFijosInput,
        domElements.inversionInput,
        domElements.crecimientoInput,
        domElements.horizonteInput
    ];
    
    // Store for global access
    domElements.inputFields = inputFields.filter(field => field !== null);
}

function populateDefaultValues() {
    Object.keys(formConfig.defaultValues).forEach(key => {
        const input = document.getElementById('id_' + key);
        if (input && !input.value) {
            input.value = formConfig.defaultValues[key];
        }
    });
}

/**
 * =================================================================
 * EVENT LISTENERS SETUP
 * =================================================================
 */

function initializeEventListeners() {
    setupFormEventListeners();
    setupGeneralEventListeners();
}

function setupFormEventListeners() {
    // Input field event listeners
    domElements.inputFields.forEach(input => {
        if (input) {
            input.addEventListener('input', handleInputChange);
            input.addEventListener('blur', handleInputBlur);
        }
    });
    
    // Product selection
    if (domElements.productSelect) {
        domElements.productSelect.addEventListener('change', handleProductChange);
    }
    
    // Button event listeners
    if (domElements.validateBtn) {
        domElements.validateBtn.addEventListener('click', handleValidateForm);
    }
    
    if (domElements.resetBtn) {
        domElements.resetBtn.addEventListener('click', handleResetForm);
    }
    
    if (domElements.toggleAdvanced) {
        domElements.toggleAdvanced.addEventListener('click', handleToggleAdvanced);
    }
    
    // Form submission
    if (domElements.form) {
        domElements.form.addEventListener('submit', handleFormSubmission);
    }
    
    // Auto-save interval
    setInterval(saveFormData, 30000); // Save every 30 seconds
}

function setupGeneralEventListeners() {
    // Window events
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

/**
 * =================================================================
 * INPUT HANDLING
 * =================================================================
 */

function handleInputChange(event) {
    updatePreview();
    updateFormProgress();
    
    // Clear individual field errors
    const fieldName = event.target.id.replace('id_', '');
    const errorDiv = document.getElementById(fieldName + 'Error');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

function handleInputBlur(event) {
    // Validate individual field
    const errors = validateForm();
    const fieldName = event.target.id.replace('id_', '');
    const fieldErrors = errors.filter(error => 
        error.toLowerCase().includes(fieldName) || 
        (fieldName === 'precio_unitario' && error.includes('precio')) ||
        (fieldName === 'costo_unitario' && error.includes('costo')) ||
        (fieldName === 'demanda_inicial' && error.includes('demanda'))
    );
    
    const errorDiv = document.getElementById(fieldName + 'Error');
    if (errorDiv) {
        if (fieldErrors.length > 0) {
            errorDiv.textContent = fieldErrors[0];
            errorDiv.style.display = 'block';
        } else {
            errorDiv.style.display = 'none';
        }
    }
}

function handleProductChange(event) {
    updateFormProgress();
    selectProduct(event.target.value);
}

/**
 * =================================================================
 * PRODUCT SELECTION
 * =================================================================
 */

function selectProduct(productId) {
    if (domElements.productSelect) {
        domElements.productSelect.value = productId;
        
        // Update visual selection
        document.querySelectorAll('.product-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        const selectedCard = document.querySelector(`[data-product-id="${productId}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }
        
        updateFormProgress();
    }
}

// Make selectProduct globally available
window.selectProduct = selectProduct;

/**
 * =================================================================
 * PREVIEW CALCULATIONS
 * =================================================================
 */

function updatePreview() {
    try {
        const values = getFormValues();
        const calculations = performCalculations(values);
        
        updatePreviewDisplay(calculations);
        updateMarginInfo(calculations);
        updateMetricColors(calculations);
        updateRiskAssessment(calculations);
        
    } catch (error) {
        console.error('Error updating preview:', error);
        displayPreviewError();
    }
}

function getFormValues() {
    return {
        precio: parseFloat(domElements.precioInput?.value) || 0,
        costo: parseFloat(domElements.costoInput?.value) || 0,
        demanda: parseFloat(domElements.demandaInput?.value) || 0,
        gastosFijos: parseFloat(domElements.gastosFijosInput?.value) || 0,
        inversion: parseFloat(domElements.inversionInput?.value) || 0,
        crecimiento: parseFloat(domElements.crecimientoInput?.value) || 0,
        horizonte: parseInt(domElements.horizonteInput?.value) || 0
    };
}

function performCalculations(values) {
    const margen = values.precio - values.costo;
    const marginPercentage = values.precio > 0 ? (margen / values.precio) * 100 : 0;
    const utilidadBruta = margen * values.demanda;
    const utilidadNeta = utilidadBruta - values.gastosFijos;
    const puntoEquilibrio = margen > 0 ? Math.ceil(values.gastosFijos / margen) : Infinity;
    const roi = values.inversion > 0 ? (utilidadNeta / values.inversion) * 100 : 0;
    const payback = utilidadNeta > 0 ? values.inversion / utilidadNeta : Infinity;
    
    return {
        margen,
        marginPercentage,
        utilidadBruta,
        utilidadNeta,
        puntoEquilibrio,
        roi,
        payback,
        values
    };
}

function updatePreviewDisplay(calc) {
    if (domElements.previewMargin) {
        domElements.previewMargin.textContent = `${calc.margen.toFixed(2)}`;
    }
    
    if (domElements.previewBreakEven) {
        domElements.previewBreakEven.textContent = isFinite(calc.puntoEquilibrio) 
            ? `${calc.puntoEquilibrio.toLocaleString()} unidades` 
            : '∞ unidades';
    }
    
    if (domElements.previewRoi) {
        domElements.previewRoi.textContent = `${calc.roi.toFixed(2)}%`;
    }
    
    if (domElements.previewProfit) {
        domElements.previewProfit.textContent = `${calc.utilidadNeta.toFixed(2)}`;
    }
    
    if (domElements.previewPayback) {
        domElements.previewPayback.textContent = isFinite(calc.payback) 
            ? `${calc.payback.toFixed(1)} meses` 
            : '∞ meses';
    }
}

function updateMarginInfo(calc) {
    if (domElements.marginInfo && domElements.marginValue && domElements.marginPercent) {
        domElements.marginValue.textContent = `${calc.margen.toFixed(2)}`;
        domElements.marginPercent.textContent = `${calc.marginPercentage.toFixed(1)}%`;
        domElements.marginInfo.style.display = 'block';
    }
}

function updateMetricColors(calc) {
    // Margin color
    const marginMetric = document.getElementById('marginMetric');
    if (marginMetric) {
        marginMetric.className = `preview-metric ${getMetricClass(calc.margen, 'margin')}`;
    }
    
    // Profit color
    const profitMetric = document.getElementById('profitMetric');
    if (profitMetric) {
        profitMetric.className = `preview-metric ${getMetricClass(calc.utilidadNeta, 'profit')}`;
    }
    
    // ROI color
    const roiMetric = document.getElementById('roiMetric');
    if (roiMetric) {
        roiMetric.className = `preview-metric ${getMetricClass(calc.roi, 'roi')}`;
    }
    
    // Break-even color
    const breakEvenMetric = document.getElementById('breakEvenMetric');
    if (breakEvenMetric) {
        const demanda = calc.values.demanda;
        breakEvenMetric.className = `preview-metric ${getMetricClass(calc.puntoEquilibrio, 'breakeven', demanda)}`;
    }
    
    // Payback color
    const paybackMetric = document.getElementById('paybackMetric');
    if (paybackMetric) {
        paybackMetric.className = `preview-metric ${getMetricClass(calc.payback, 'payback')}`;
    }
}

function getMetricClass(value, type, reference = null) {
    switch (type) {
        case 'margin':
            return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
        case 'profit':
            return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
        case 'roi':
            return value > 15 ? 'positive' : value > 5 ? 'neutral' : 'negative';
        case 'breakeven':
            if (!isFinite(value)) return 'negative';
            return value < reference ? 'positive' : value < reference * 2 ? 'neutral' : 'negative';
        case 'payback':
            if (!isFinite(value)) return 'negative';
            return value < 12 ? 'positive' : value < 24 ? 'neutral' : 'negative';
        default:
            return 'neutral';
    }
}

function displayPreviewError() {
    const errorText = 'Error en cálculos';
    
    if (domElements.previewMargin) domElements.previewMargin.textContent = errorText;
    if (domElements.previewBreakEven) domElements.previewBreakEven.textContent = errorText;
    if (domElements.previewRoi) domElements.previewRoi.textContent = errorText;
    if (domElements.previewProfit) domElements.previewProfit.textContent = errorText;
    if (domElements.previewPayback) domElements.previewPayback.textContent = errorText;
}

/**
 * =================================================================
 * RISK ASSESSMENT
 * =================================================================
 */

function updateRiskAssessment(calc) {
    let riskScore = 0;
    let riskFactors = [];
    
    // Margin risk
    if (calc.margen <= 0) {
        riskScore += 30;
        riskFactors.push('Sin margen de beneficio');
    } else if (calc.margen < 20) {
        riskScore += 15;
        riskFactors.push('Margen bajo');
    }
    
    // Profitability risk
    if (calc.utilidadNeta <= 0) {
        riskScore += 25;
        riskFactors.push('Sin utilidad neta');
    }
    
    // ROI risk
    if (calc.roi < 5) {
        riskScore += 20;
        riskFactors.push('ROI bajo');
    }
    
    // Growth risk
    if (calc.values.crecimiento < 0) {
        riskScore += 15;
        riskFactors.push('Crecimiento negativo');
    } else if (calc.values.crecimiento > 50) {
        riskScore += 10;
        riskFactors.push('Crecimiento muy optimista');
    }
    
    // Payback risk
    if (calc.payback > 36) {
        riskScore += 10;
        riskFactors.push('Recuperación lenta');
    }
    
    updateRiskDisplay(riskScore, riskFactors);
}

function updateRiskDisplay(riskScore, riskFactors) {
    let riskClass, riskText, riskDesc;
    
    if (riskScore >= 50) {
        riskClass = 'bg-danger';
        riskText = 'Alto';
        riskDesc = 'Proyecto de alto riesgo';
    } else if (riskScore >= 25) {
        riskClass = 'bg-warning';
        riskText = 'Medio';
        riskDesc = 'Requiere análisis adicional';
    } else {
        riskClass = 'bg-success';
        riskText = 'Bajo';
        riskDesc = 'Proyecto prometedor';
    }
    
    if (domElements.riskBar) {
        domElements.riskBar.className = `risk-progress-bar ${riskClass}`;
        domElements.riskBar.style.width = `${Math.min(riskScore, 100)}%`;
    }
    
    if (domElements.riskLevel) domElements.riskLevel.textContent = riskText;
    if (domElements.riskDescription) {
        domElements.riskDescription.textContent = riskFactors.length > 0 ? riskFactors.join(', ') : riskDesc;
    }
}

/**
 * =================================================================
 * FORM PROGRESS
 * =================================================================
 */

function updateFormProgress() {
    const requiredFields = [domElements.productSelect, domElements.precioInput, domElements.costoInput, domElements.demandaInput, domElements.horizonteInput];
    const filledFields = requiredFields.filter(field => field && field.value && field.value.trim() !== '');
    const progress = (filledFields.length / requiredFields.length) * 100;
    
    if (domElements.formProgress) {
        domElements.formProgress.style.width = `${progress}%`;
    }
    
    // Update section validations
    updateSectionValidation('product', domElements.productSelect?.value);
    updateSectionValidation('market', domElements.demandaInput?.value && domElements.horizonteInput?.value);
    updateSectionValidation('financial', domElements.precioInput?.value && domElements.costoInput?.value);
}

function updateSectionValidation(section, isValid) {
    const indicator = document.getElementById(`${section}Validation`);
    if (indicator) {
        if (isValid) {
            indicator.className = 'validation-indicator valid';
            indicator.textContent = '✓';
            indicator.title = 'Sección válida';
        } else {
            indicator.className = 'validation-indicator invalid';
            indicator.textContent = '!';
            indicator.title = 'Faltan datos requeridos';
        }
    }
}

/**
 * =================================================================
 * ADVANCED OPTIONS TOGGLE
 * =================================================================
 */

function handleToggleAdvanced() {
    if (domElements.toggleAdvanced && domElements.advancedOptions) {
        const isShown = domElements.advancedOptions.classList.contains('show');
        
        if (isShown) {
            domElements.advancedOptions.classList.remove('show');
            domElements.toggleAdvanced.innerHTML = '<i class="ri-arrow-down-s-line me-1"></i>Mostrar';
        } else {
            domElements.advancedOptions.classList.add('show');
            domElements.toggleAdvanced.innerHTML = '<i class="ri-arrow-up-s-line me-1"></i>Ocultar';
        }
    }
}

/**
 * =================================================================
 * FORM VALIDATION
 * =================================================================
 */

function validateForm() {
    const errors = [];
    const precio = parseFloat(domElements.precioInput?.value) || 0;
    const costo = parseFloat(domElements.costoInput?.value) || 0;
    const demanda = parseFloat(domElements.demandaInput?.value) || 0;
    const horizonte = parseInt(domElements.horizonteInput?.value) || 0;
    
    // Required field validations
    if (!domElements.productSelect?.value) errors.push('Debe seleccionar un producto');
    if (precio <= 0) errors.push('El precio debe ser mayor a 0');
    if (costo < 0) errors.push('El costo no puede ser negativo');
    if (demanda <= 0) errors.push('La demanda debe ser mayor a 0');
    if (horizonte <= 0) errors.push('El horizonte debe ser mayor a 0');
    
    // Business logic validations
    if (precio <= costo) errors.push('El precio debe ser mayor al costo para tener margen');
    if (horizonte > 120) errors.push('El horizonte no puede ser mayor a 120 meses');
    
    const crecimiento = parseFloat(domElements.crecimientoInput?.value) || 0;
    if (crecimiento < -100 || crecimiento > 1000) {
        errors.push('La tasa de crecimiento debe estar entre -100% y 1000%');
    }
    
    return errors;
}

function showValidationResults(errors) {
    if (errors.length === 0) {
        if (domElements.validationSuccess) {
            domElements.validationSuccess.style.display = 'block';
            setTimeout(() => {
                domElements.validationSuccess.style.display = 'none';
            }, 3000);
        }
        if (domElements.validationErrors) domElements.validationErrors.style.display = 'none';
    } else {
        if (domElements.validationErrors && domElements.errorList) {
            domElements.errorList.innerHTML = errors.map(error => `<div>• ${error}</div>`).join('');
            domElements.validationErrors.style.display = 'block';
        }
        if (domElements.validationSuccess) domElements.validationSuccess.style.display = 'none';
    }
}

/**
 * =================================================================
 * BUTTON EVENT HANDLERS
 * =================================================================
 */

function handleValidateForm() {
    const errors = validateForm();
    showValidationResults(errors);
    
    if (errors.length === 0 && domElements.validateBtn) {
        domElements.validateBtn.classList.add('btn-success');
        domElements.validateBtn.innerHTML = '<i class="ri-check-line me-2"></i>Parámetros Válidos';
        setTimeout(() => {
            domElements.validateBtn.classList.remove('btn-success');
            domElements.validateBtn.innerHTML = '<i class="ri-check-line me-2"></i>Validar Parámetros';
        }, 2000);
    }
}

function handleResetForm() {
    if (confirm('¿Está seguro de que desea restaurar todos los valores por defecto?')) {
        Object.keys(formConfig.defaultValues).forEach(key => {
            const input = document.getElementById('id_' + key);
            if (input) input.value = formConfig.defaultValues[key];
        });
        
        if (domElements.productSelect) domElements.productSelect.value = '';
        
        // Clear product selection
        document.querySelectorAll('.product-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        updatePreview();
        updateFormProgress();
        
        // Hide error messages
        document.querySelectorAll('.error-message').forEach(div => {
            div.style.display = 'none';
        });
    }
}

function handleFormSubmission(e) {
    const errors = validateForm();
    
    if (errors.length > 0) {
        e.preventDefault();
        showValidationResults(errors);
        
        // Scroll to first error
        const firstErrorField = domElements.form.querySelector('.error-message[style*="block"]');
        if (firstErrorField) {
            firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        return false;
    }
    
    // Show loading overlay
    if (domElements.loadingOverlay) {
        domElements.loadingOverlay.style.display = 'flex';
    }
    
    // Update submit button
    if (domElements.submitBtn && domElements.submitText) {
        domElements.submitBtn.disabled = true;
        domElements.submitText.textContent = 'Procesando...';
        domElements.submitBtn.innerHTML = '<div class="spinner-border spinner-border-sm me-2"></div>Procesando Simulación...';
    }
}

/**
 * =================================================================
 * TOOLTIPS INITIALIZATION
 * =================================================================
 */

function initializeTooltips() {
    const tooltips = document.querySelectorAll('.help-tooltip');
    tooltips.forEach(tooltip => {
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            new bootstrap.Tooltip(tooltip, {
                placement: 'top',
                trigger: 'hover focus'
            });
        }
    });
}

/**
 * =================================================================
 * LOCAL STORAGE FUNCTIONS
 * =================================================================
 */

function saveFormData() {
    const formData = {};
    domElements.inputFields.forEach(input => {
        if (input && input.value) {
            formData[input.id] = input.value;
        }
    });
    
    if (domElements.productSelect && domElements.productSelect.value) {
        formData[domElements.productSelect.id] = domElements.productSelect.value;
    }
    
    try {
        localStorage.setItem('simulationFormData', JSON.stringify(formData));
    } catch (e) {
        console.warn('Could not save form data:', e);
    }
}

function loadFormData() {
    try {
        const savedData = localStorage.getItem('simulationFormData');
        if (savedData) {
            const formData = JSON.parse(savedData);
            
            Object.keys(formData).forEach(fieldId => {
                const field = document.getElementById(fieldId);
                if (field && !field.value) {
                    field.value = formData[fieldId];
                }
            });
        }
    } catch (e) {
        console.warn('Could not load form data:', e);
    }
}

/**
 * =================================================================
 * KEYBOARD SHORTCUTS
 * =================================================================
 */

function handleKeyboardShortcuts(event) {
    // Ctrl/Cmd + S to validate form
    if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        handleValidateForm();
    }
    
    // Ctrl/Cmd + Enter to submit form
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        if (domElements.form) {
            domElements.form.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape to close advanced options
    if (event.key === 'Escape') {
        if (domElements.advancedOptions && domElements.advancedOptions.classList.contains('show')) {
            handleToggleAdvanced();
        }
    }
}

/**
 * =================================================================
 * WINDOW EVENT HANDLERS
 * =================================================================
 */

function handleBeforeUnload() {
    if (domElements.form && domElements.form.querySelector('[type="submit"]:disabled')) {
        localStorage.removeItem('simulationFormData');
    }
}

/**
 * =================================================================
 * UTILITY FUNCTIONS
 * =================================================================
 */

function formatCurrency(value) {
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(value);
}

function formatNumber(value, decimals = 0) {
    return new Intl.NumberFormat('es-ES', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

function formatPercentage(value, decimals = 2) {
    return new Intl.NumberFormat('es-ES', {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value / 100);
}

/**
 * =================================================================
 * ACCESSIBILITY ENHANCEMENTS
 * =================================================================
 */

function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.classList.add('sr-only');
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

/**
 * =================================================================
 * ERROR HANDLING
 * =================================================================
 */

window.addEventListener('error', function(event) {
    console.error('JavaScript Error:', event.error);
    
    // Show user-friendly error message
    if (domElements.validationErrors && domElements.errorList) {
        domElements.errorList.innerHTML = '<div>• Ha ocurrido un error inesperado. Por favor, recargue la página.</div>';
        domElements.validationErrors.style.display = 'block';
    }
});

/**
 * =================================================================
 * PERFORMANCE OPTIMIZATION
 * =================================================================
 */

// Debounce function for performance optimization
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Debounced version of updatePreview for better performance
const debouncedUpdatePreview = debounce(updatePreview, 300);

// Replace direct updatePreview calls with debounced version in input handlers
function handleInputChangeDebounced(event) {
    debouncedUpdatePreview();
    updateFormProgress();
    
    // Clear individual field errors
    const fieldName = event.target.id.replace('id_', '');
    const errorDiv = document.getElementById(fieldName + 'Error');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}