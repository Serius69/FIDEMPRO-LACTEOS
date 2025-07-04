/**
 * Questionary Main Management
 * Enhanced JavaScript functionality for questionary main page
 */

class QuestionaryMainManager {
    constructor() {
        this.historicalData = {};
        this.autoSaveInterval = null;
        this.validationRules = {};
        this.init();
    }

    /**
     * Initialize the questionary main functionality
     */
    init() {
        this.setupEventListeners();
        this.initializeExistingData();
        this.setupValidation();
        this.startAutoSave();
        this.setupKeyboardShortcuts();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Form validation
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });

        // Historical data inputs
        document.addEventListener('change', (e) => {
            if (e.target.matches('[id^="data_"]')) {
                const questionId = this.extractQuestionId(e.target.id);
                this.updateCounter(questionId);
            }
        });

        // Auto-resize textareas
        document.addEventListener('input', (e) => {
            if (e.target.matches('textarea')) {
                this.autoResizeTextarea(e.target);
            }
        });

        // Progress tracking
        this.setupProgressTracking();
    }

    /**
     * Validate form before submission
     */
    validateForm() {
        const selectedQuestionary = document.getElementById('inputGroupSelect01');
        if (selectedQuestionary && selectedQuestionary.value === '') {
            this.showAlert('Por favor seleccione un cuestionario.', 'warning');
            selectedQuestionary.focus();
            selectedQuestionary.classList.add('is-invalid');
            return false;
        }
        return true;
    }

    /**
     * Validate answers before submission
     */
    validateAnswers() {
        const form = document.getElementById('questionForm');
        if (!form) return true;

        let isValid = true;
        const errors = [];

        // Validate required fields
        const requiredInputs = form.querySelectorAll('[required]');
        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
                errors.push(`Campo requerido: ${this.getFieldLabel(input)}`);
            } else {
                input.classList.remove('is-invalid');
            }
        });

        // Validate historical data
        const historicalInputs = form.querySelectorAll('[id^="historicalData_"]');
        historicalInputs.forEach(input => {
            if (input.value) {
                const values = this.parseHistoricalData(input.value);
                const questionId = input.id.replace('historicalData_', '');
                
                if (values.length < 30) {
                    input.classList.add('is-invalid');
                    isValid = false;
                    errors.push(`Los datos históricos deben contener al menos 30 valores. Actualmente: ${values.length}`);
                    
                    // Scroll to the problematic field
                    const tbody = document.getElementById('tbody_' + questionId);
                    if (tbody) {
                        tbody.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                } else {
                    input.classList.remove('is-invalid');
                }
            }
        });

        // Validate numeric ranges
        this.validateNumericRanges(form, errors);

        if (!isValid) {
            this.showValidationErrors(errors);
        }

        return isValid;
    }

    /**
     * Validate numeric ranges
     */
    validateNumericRanges(form, errors) {
        const numericInputs = form.querySelectorAll('input[type="number"]');
        numericInputs.forEach(input => {
            if (input.value) {
                const value = parseFloat(input.value);
                const min = input.getAttribute('min');
                const max = input.getAttribute('max');

                if (min !== null && value < parseFloat(min)) {
                    input.classList.add('is-invalid');
                    errors.push(`${this.getFieldLabel(input)} debe ser mayor o igual a ${min}`);
                }

                if (max !== null && value > parseFloat(max)) {
                    input.classList.add('is-invalid');
                    errors.push(`${this.getFieldLabel(input)} debe ser menor o igual a ${max}`);
                }
            }
        });
    }

    /**
     * Show validation errors
     */
    showValidationErrors(errors) {
        const errorHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <h6><i class="fa fa-exclamation-triangle"></i> Se encontraron errores:</h6>
                <ul class="mb-0">
                    ${errors.map(error => `<li>${error}</li>`).join('')}
                </ul>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        // Remove existing error alerts
        document.querySelectorAll('.alert-danger').forEach(alert => {
            if (alert.textContent.includes('Se encontraron errores:')) {
                alert.remove();
            }
        });

        // Add new error alert at the top of the form
        const form = document.getElementById('questionForm') || document.querySelector('form');
        if (form) {
            form.insertAdjacentHTML('beforebegin', errorHtml);
            form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    /**
     * Get field label for error messages
     */
    getFieldLabel(input) {
        const label = input.closest('.form-group')?.querySelector('label');
        if (label) return label.textContent.trim();
        
        const questionCard = input.closest('.question-card');
        if (questionCard) {
            const questionText = questionCard.querySelector('.card-text');
            if (questionText) return questionText.textContent.trim().substring(0, 50) + '...';
        }
        
        return input.placeholder || input.name || 'Campo';
    }

    /**
     * Handle form submission
     */
    handleFormSubmit(event) {
        const form = event.target;
        
        if (form.id === 'questionForm') {
            if (!this.validateAnswers()) {
                event.preventDefault();
                return false;
            }
        } else {
            if (!this.validateForm()) {
                event.preventDefault();
                return false;
            }
        }

        this.showLoadingState(form);
        return true;
    }

    /**
     * Show loading state on form submission
     */
    showLoadingState(form) {
        const submitButtons = form.querySelectorAll('button[type="submit"]');
        submitButtons.forEach(button => {
            button.disabled = true;
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Procesando...';
            
            setTimeout(() => {
                button.disabled = false;
                button.innerHTML = originalText;
            }, 3000);
        });
    }

    /**
     * Show alert messages
     */
    showAlert(message, type = 'success') {
        const alertDiv = document.querySelector('.success-message');
        if (alertDiv) {
            alertDiv.className = `alert alert-${type} success-message`;
            const textElement = document.getElementById('success-text');
            if (textElement) {
                textElement.textContent = message;
            }
            alertDiv.style.display = 'block';
            
            setTimeout(() => {
                alertDiv.style.display = 'none';
            }, 4000);
        } else {
            // Fallback: create temporary alert
            this.createTemporaryAlert(message, type);
        }
    }

    /**
     * Create temporary alert
     */
    createTemporaryAlert(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            <i class="fa fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 4000);
    }

    /**
     * Parse historical data from string
     */
    parseHistoricalData(dataString) {
        try {
            return dataString.split(',')
                .map(value => value.trim())
                .filter(value => value !== '')
                .map(value => parseFloat(value))
                .filter(value => !isNaN(value));
        } catch (error) {
            console.error('Error parsing historical data:', error);
            return [];
        }
    }

    /**
     * Historical data management
     */
    agregarFila(questionId) {
        const tbody = document.getElementById('tbody_' + questionId);
        if (!tbody) return;

        const rowCount = tbody.rows.length + 1;
        const unitText = this.getQuestionUnit(questionId) || 'unidades';
        
        const newRow = tbody.insertRow(-1);
        newRow.className = 'data-input-row';
        newRow.innerHTML = `
            <td class="text-center">${rowCount}</td>
            <td>
                <input type="number" 
                       class="form-control form-control-sm" 
                       step="0.01" 
                       placeholder="Valor ${rowCount}" 
                       onchange="questionaryMain.updateCounter(${questionId})"
                       onblur="questionaryMain.validateHistoricalValue(this)"
                       id="data_${questionId}_${rowCount}"
                       min="0">
            </td>
            <td class="text-center text-muted">${unitText}</td>
            <td class="text-center">
                <button type="button" 
                        onclick="questionaryMain.eliminarFila(this, ${questionId})" 
                        class="btn btn-sm btn-danger"
                        data-bs-toggle="tooltip"
                        title="Eliminar fila">
                    <i class="fa fa-trash"></i>
                </button>
            </td>
        `;
        
        this.updateRowNumbers(questionId);
        this.updateCounter(questionId);
        
        // Focus on the new input
        const newInput = newRow.querySelector('input');
        if (newInput) {
            newInput.focus();
        }

        // Initialize tooltip for the new button
        this.initializeTooltips(newRow);
    }

    /**
     * Add multiple rows for historical data
     */
    agregarMultiplesFila(questionId, cantidad) {
        for (let i = 0; i < cantidad; i++) {
            this.agregarFila(questionId);
        }
        this.showAlert(`Se agregaron ${cantidad} filas`, 'info');
    }

    /**
     * Remove historical data row
     */
    eliminarFila(button, questionId) {
        const row = button.closest('tr');
        if (row && confirm('¿Está seguro de que desea eliminar esta fila?')) {
            row.remove();
            this.updateRowNumbers(questionId);
            this.updateCounter(questionId);
            this.showAlert('Fila eliminada', 'info');
        }
    }

    /**
     * Update row numbers after add/remove
     */
    updateRowNumbers(questionId) {
        const tbody = document.getElementById('tbody_' + questionId);
        if (!tbody) return;

        const rows = tbody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            const numberCell = row.cells[0];
            const input = row.cells[1]?.querySelector('input');
            
            if (numberCell) {
                numberCell.textContent = index + 1;
            }
            
            if (input) {
                input.id = `data_${questionId}_${index + 1}`;
                input.placeholder = `Valor ${index + 1}`;
            }
        });
    }

    /**
     * Update data counter
     */
    updateCounter(questionId) {
        const tbody = document.getElementById('tbody_' + questionId);
        if (!tbody) return;

        const inputs = tbody.querySelectorAll('input[type="number"]');
        let count = 0;
        let validCount = 0;

        inputs.forEach(input => {
            if (input.value && input.value.trim() !== '') {
                count++;
                if (!isNaN(parseFloat(input.value)) && parseFloat(input.value) >= 0) {
                    validCount++;
                }
            }
        });

        const badge = document.getElementById('contador_' + questionId);
        if (badge) {
            badge.textContent = `${validCount} datos válidos de ${count} ingresados`;
            
            // Update badge color based on count
            badge.className = 'badge ' + (validCount >= 30 ? 'bg-success' : 
                                         validCount >= 15 ? 'bg-warning' : 'bg-secondary');
        }

        // Update progress if exists
        this.updateProgress(questionId, validCount);
    }

    /**
     * Update progress indicator
     */
    updateProgress(questionId, count) {
        const progressContainer = document.querySelector(`#question-${questionId} .progress`);
        if (progressContainer) {
            const progressBar = progressContainer.querySelector('.progress-bar');
            const percentage = Math.min((count / 30) * 100, 100);
            
            if (progressBar) {
                progressBar.style.width = percentage + '%';
                progressBar.setAttribute('aria-valuenow', percentage);
                progressBar.textContent = Math.round(percentage) + '%';
            }
        }
    }

    /**
     * Validate individual historical value
     */
    validateHistoricalValue(input) {
        const value = parseFloat(input.value);
        
        if (input.value && (isNaN(value) || value < 0)) {
            input.classList.add('is-invalid');
            this.showAlert('Por favor ingrese un valor numérico válido mayor o igual a 0', 'warning');
            input.focus();
        } else {
            input.classList.remove('is-invalid');
        }
    }

    /**
     * Save historical data
     */
    guardarDatosHistoricos(questionId) {
        const tbody = document.getElementById('tbody_' + questionId);
        if (!tbody) return;

        const rows = tbody.querySelectorAll('tr');
        const data = [];
        let invalidCount = 0;

        rows.forEach(row => {
            const input = row.cells[1]?.querySelector('input');
            if (input && input.value && input.value.trim() !== '') {
                const value = parseFloat(input.value);
                if (!isNaN(value) && value >= 0) {
                    data.push(value);
                } else {
                    invalidCount++;
                    input.classList.add('is-invalid');
                }
            }
        });

        if (invalidCount > 0) {
            this.showAlert(`Se encontraron ${invalidCount} valores inválidos. Por favor corrija antes de continuar.`, 'danger');
            return;
        }

        if (data.length < 30) {
            this.showAlert(`Debe ingresar al menos 30 datos históricos. Actualmente tiene: ${data.length}`, 'danger');
            return;
        }

        // Save to hidden field
        const hiddenField = document.getElementById('historicalData_' + questionId);
        if (hiddenField) {
            hiddenField.value = data.join(',');
        }

        // Calculate and show statistics
        const stats = this.calculateStatistics(data);
        this.showDataStatistics(questionId, data.length, stats);
        
        this.showAlert(`Datos validados correctamente. Total: ${data.length} valores`, 'success');
    }

    /**
     * Calculate basic statistics
     */
    calculateStatistics(data) {
        const sum = data.reduce((a, b) => a + b, 0);
        const mean = sum / data.length;
        const sortedData = [...data].sort((a, b) => a - b);
        const min = sortedData[0];
        const max = sortedData[sortedData.length - 1];
        const median = sortedData.length % 2 === 0 
            ? (sortedData[sortedData.length / 2 - 1] + sortedData[sortedData.length / 2]) / 2
            : sortedData[Math.floor(sortedData.length / 2)];

        return { mean, median, min, max, sum };
    }

    /**
     * Show data statistics
     */
    showDataStatistics(questionId, count, stats) {
        const container = document.getElementById(`tbody_${questionId}`).closest('.form-group');
        let statsDiv = container.querySelector('.data-statistics');
        
        if (!statsDiv) {
            statsDiv = document.createElement('div');
            statsDiv.className = 'data-statistics mt-3 p-3 bg-light border rounded';
            container.appendChild(statsDiv);
        }

        statsDiv.innerHTML = `
            <h6><i class="fa fa-chart-bar"></i> Estadísticas de los datos</h6>
            <div class="row">
                <div class="col-md-3">
                    <strong>Total:</strong> ${count}<br>
                    <strong>Promedio:</strong> ${stats.mean.toFixed(2)}
                </div>
                <div class="col-md-3">
                    <strong>Mediana:</strong> ${stats.median.toFixed(2)}<br>
                    <strong>Suma:</strong> ${stats.sum.toFixed(2)}
                </div>
                <div class="col-md-3">
                    <strong>Mínimo:</strong> ${stats.min.toFixed(2)}<br>
                    <strong>Máximo:</strong> ${stats.max.toFixed(2)}
                </div>
                <div class="col-md-3">
                    <strong>Rango:</strong> ${(stats.max - stats.min).toFixed(2)}
                </div>
            </div>
        `;
    }

    /**
     * Get question unit
     */
    getQuestionUnit(questionId) {
        const questionCard = document.querySelector(`[data-question-id="${questionId}"]`);
        if (questionCard) {
            const unitText = questionCard.querySelector('.unit-text');
            return unitText ? unitText.textContent : null;
        }
        return null;
    }

    /**
     * Extract question ID from element ID
     */
    extractQuestionId(elementId) {
        const match = elementId.match(/(\d+)/);
        return match ? parseInt(match[0]) : null;
    }

    /**
     * Initialize existing data on page load
     */
    initializeExistingData() {
        // Load existing historical data
        const historicalFields = document.querySelectorAll('[id^="historicalData_"]');
        
        historicalFields.forEach(field => {
            if (field.value && field.value.trim()) {
                const questionId = field.id.replace('historicalData_', '');
                const data = this.parseHistoricalData(field.value);
                
                if (data.length > 0) {
                    this.loadHistoricalDataToTable(questionId, data);
                }
            }
        });

        // Initialize tooltips
        this.initializeTooltips();
    }

    /**
     * Load historical data into table
     */
    loadHistoricalDataToTable(questionId, data) {
        data.forEach((value, index) => {
            this.agregarFila(questionId);
            const tbody = document.getElementById('tbody_' + questionId);
            if (tbody) {
                const lastRow = tbody.rows[tbody.rows.length - 1];
                const input = lastRow.cells[1]?.querySelector('input');
                if (input) {
                    input.value = value;
                }
            }
        });
        
        this.updateCounter(questionId);
    }

    /**
     * Initialize tooltips
     */
    initializeTooltips(container = document) {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = container.querySelectorAll('[data-bs-toggle="tooltip"]');
            tooltipTriggerList.forEach(tooltipTriggerEl => {
                if (!tooltipTriggerEl._tooltip) {
                    tooltipTriggerEl._tooltip = new bootstrap.Tooltip(tooltipTriggerEl, {
                        delay: { show: 500, hide: 100 }
                    });
                }
            });
        }
    }

    /**
     * Setup form validation rules
     */
    setupValidation() {
        // Add real-time validation
        document.addEventListener('blur', (e) => {
            if (e.target.matches('input[required], select[required], textarea[required]')) {
                this.validateField(e.target);
            }
        }, true);

        // Add input formatting
        document.addEventListener('input', (e) => {
            if (e.target.matches('input[type="number"]')) {
                this.formatNumericInput(e.target);
            }
        });
    }

    /**
     * Validate individual field
     */
    validateField(field) {
        let isValid = true;
        const value = field.value.trim();

        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');

        // Check required fields
        if (field.hasAttribute('required') && !value) {
            field.classList.add('is-invalid');
            isValid = false;
        }

        // Check numeric fields
        if (field.type === 'number' && value) {
            const numValue = parseFloat(value);
            const min = field.getAttribute('min');
            const max = field.getAttribute('max');

            if (isNaN(numValue)) {
                field.classList.add('is-invalid');
                isValid = false;
            } else if (min !== null && numValue < parseFloat(min)) {
                field.classList.add('is-invalid');
                isValid = false;
            } else if (max !== null && numValue > parseFloat(max)) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        }

        if (isValid && value) {
            field.classList.add('is-valid');
        }

        return isValid;
    }

    /**
     * Format numeric input
     */
    formatNumericInput(input) {
        const value = input.value;
        
        // Remove invalid characters for numbers
        const cleanValue = value.replace(/[^0-9.-]/g, '');
        
        if (cleanValue !== value) {
            input.value = cleanValue;
        }
    }

    /**
     * Auto-resize textarea
     */
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    }

    /**
     * Setup progress tracking
     */
    setupProgressTracking() {
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            this.updateOverallProgress();
        }
    }

    /**
     * Update overall progress
     */
    updateOverallProgress() {
        const form = document.getElementById('questionForm');
        if (!form) return;

        const totalQuestions = form.querySelectorAll('.question-card').length;
        const answeredQuestions = form.querySelectorAll('.question-card input:not([value=""]), .question-card select:not([value=""]), .question-card textarea:not([value=""])').length;
        
        const percentage = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;
        
        const progressBar = document.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = percentage + '%';
            progressBar.textContent = Math.round(percentage) + '%';
        }
    }

    /**
     * Start auto-save functionality
     */
    startAutoSave() {
        // Auto-save every 2 minutes
        this.autoSaveInterval = setInterval(() => {
            this.autoSave();
        }, 120000);
    }

    /**
     * Auto-save form data
     */
    autoSave() {
        const form = document.getElementById('questionForm');
        if (!form) return;

        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        // Save to localStorage as backup
        try {
            localStorage.setItem('questionary_autosave', JSON.stringify({
                data: data,
                timestamp: Date.now(),
                questionaryId: document.querySelector('[name="selected_questionary_id"]')?.value
            }));
            
            this.showAutoSaveIndicator();
        } catch (error) {
            console.warn('Auto-save to localStorage failed:', error);
        }
    }

    /**
     * Show auto-save indicator
     */
    showAutoSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'auto-save-indicator position-fixed';
        indicator.style.cssText = 'bottom: 80px; right: 20px; z-index: 1000; opacity: 0.8;';
        indicator.innerHTML = `
            <div class="badge bg-success">
                <i class="fa fa-save"></i> Auto-guardado
            </div>
        `;
        
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.remove();
            }
        }, 2000);
    }

    /**
     * Load auto-saved data
     */
    loadAutoSavedData() {
        try {
            const saved = localStorage.getItem('questionary_autosave');
            if (saved) {
                const parsed = JSON.parse(saved);
                const currentQuestionaryId = document.querySelector('[name="selected_questionary_id"]')?.value;
                
                // Check if auto-saved data is for current questionary and not too old (24 hours)
                if (parsed.questionaryId === currentQuestionaryId && 
                    (Date.now() - parsed.timestamp) < 24 * 60 * 60 * 1000) {
                    
                    if (confirm('Se encontraron datos guardados automáticamente. ¿Desea restaurarlos?')) {
                        this.restoreFormData(parsed.data);
                        this.showAlert('Datos restaurados desde auto-guardado', 'info');
                    }
                }
            }
        } catch (error) {
            console.warn('Failed to load auto-saved data:', error);
        }
    }

    /**
     * Restore form data
     */
    restoreFormData(data) {
        Object.entries(data).forEach(([key, value]) => {
            const field = document.querySelector(`[name="${key}"]`);
            if (field) {
                field.value = value;
                
                // Trigger change event for dynamic updates
                field.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + S for save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                const saveButton = document.querySelector('button[name="save"]');
                if (saveButton) {
                    saveButton.click();
                }
            }

            // Ctrl/Cmd + Enter for finish
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                const finishButton = document.querySelector('button[name="finish"]');
                if (finishButton) {
                    finishButton.click();
                }
            }

            // Escape to cancel
            if (e.key === 'Escape') {
                const cancelButton = document.querySelector('button[name="cancel"]');
                if (cancelButton && confirm('¿Está seguro de que desea cancelar el cuestionario?')) {
                    cancelButton.click();
                }
            }
        });
    }

    /**
     * Export questionary data
     */
    exportQuestionaryData() {
        const form = document.getElementById('questionForm');
        if (!form) return;

        const data = {
            questionary: document.querySelector('.show-questionary')?.textContent || 'Cuestionario',
            questions: [],
            timestamp: new Date().toISOString()
        };

        // Collect question data
        form.querySelectorAll('.question-card').forEach(card => {
            const questionText = card.querySelector('.card-text')?.textContent.trim();
            const variable = card.querySelector('.variable-badge')?.textContent.trim();
            const answer = card.querySelector('input, select, textarea')?.value;

            if (questionText) {
                data.questions.push({
                    question: questionText,
                    variable: variable,
                    answer: answer || ''
                });
            }
        });

        // Download as JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cuestionario_${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);

        this.showAlert('Datos exportados exitosamente', 'success');
    }

    /**
     * Print questionary
     */
    printQuestionary() {
        const printContent = document.querySelector('.card-body').cloneNode(true);
        
        // Remove buttons and interactive elements
        printContent.querySelectorAll('button, .btn-group, .action-buttons').forEach(el => el.remove());
        
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Cuestionario</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .question-card { margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; }
                        .variable-badge { background: #f0f0f0; padding: 5px 10px; border-radius: 15px; }
                        input, select, textarea { border: none; border-bottom: 1px solid #333; background: none; }
                        @media print { body { margin: 0; } }
                    </style>
                </head>
                <body>
                    <h1>Cuestionario</h1>
                    <p>Fecha: ${new Date().toLocaleDateString()}</p>
                    ${printContent.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    /**
     * Handle page navigation with unsaved changes
     */
    setupUnloadProtection() {
        window.addEventListener('beforeunload', (e) => {
            const form = document.getElementById('questionForm');
            if (form && this.hasUnsavedChanges()) {
                const confirmationMessage = '¿Está seguro de que desea salir? Los cambios no guardados se perderán.';
                e.preventDefault();
                e.returnValue = confirmationMessage;
                return confirmationMessage;
            }
        });
    }

    /**
     * Check for unsaved changes
     */
    hasUnsavedChanges() {
        const form = document.getElementById('questionForm');
        if (!form) return false;

        const inputs = form.querySelectorAll('input, select, textarea');
        return Array.from(inputs).some(input => input.value && input.value.trim() !== '');
    }

    /**
     * Cleanup and destroy
     */
    destroy() {
        // Clear intervals
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
        }

        // Remove event listeners
        document.removeEventListener('keydown', this.setupKeyboardShortcuts);
        document.removeEventListener('beforeunload', this.setupUnloadProtection);

        // Dispose tooltips
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            if (el._tooltip && el._tooltip.dispose) {
                el._tooltip.dispose();
            }
        });
    }

    /**
     * Advanced validation for complex rules
     */
    validateComplexRules() {
        const form = document.getElementById('questionForm');
        if (!form) return true;

        let isValid = true;
        const errors = [];

        // Check for dependent questions
        this.validateDependentQuestions(form, errors);
        
        // Check for business logic rules
        this.validateBusinessRules(form, errors);

        if (!isValid && errors.length > 0) {
            this.showValidationErrors(errors);
        }

        return isValid && errors.length === 0;
    }

    /**
     * Validate dependent questions
     */
    validateDependentQuestions(form, errors) {
        // Example: If question A is answered with "Yes", question B becomes required
        // This would be configured based on your specific business rules
    }

    /**
     * Validate business rules
     */
    validateBusinessRules(form, errors) {
        // Example: Inventory levels must be positive
        // Revenue must be greater than costs, etc.
        const numericInputs = form.querySelectorAll('input[type="number"]');
        
        numericInputs.forEach(input => {
            if (input.value && input.dataset.businessRule) {
                // Implement specific business rule validation
                this.validateBusinessRule(input, input.dataset.businessRule, errors);
            }
        });
    }

    /**
     * Validate specific business rule
     */
    validateBusinessRule(input, rule, errors) {
        const value = parseFloat(input.value);
        
        switch (rule) {
            case 'positive':
                if (value <= 0) {
                    errors.push(`${this.getFieldLabel(input)} debe ser un valor positivo`);
                    input.classList.add('is-invalid');
                }
                break;
            case 'percentage':
                if (value < 0 || value > 100) {
                    errors.push(`${this.getFieldLabel(input)} debe estar entre 0 y 100`);
                    input.classList.add('is-invalid');
                }
                break;
            // Add more business rules as needed
        }
    }
}

// Global instance
let questionaryMain;

// Global functions for backward compatibility
function validateForm() {
    return questionaryMain ? questionaryMain.validateForm() : true;
}

function validateAnswers() {
    return questionaryMain ? questionaryMain.validateAnswers() : true;
}

function showAlert(message, type = 'success') {
    if (questionaryMain) {
        questionaryMain.showAlert(message, type);
    }
}

function agregarFila(questionId) {
    if (questionaryMain) {
        questionaryMain.agregarFila(questionId);
    }
}

function agregarMultiplesFila(questionId, cantidad) {
    if (questionaryMain) {
        questionaryMain.agregarMultiplesFila(questionId, cantidad);
    }
}

function eliminarFila(button, questionId) {
    if (questionaryMain) {
        questionaryMain.eliminarFila(button, questionId);
    }
}

function actualizarContador(questionId) {
    if (questionaryMain) {
        questionaryMain.updateCounter(questionId);
    }
}

function guardarDatosHistoricos(questionId) {
    if (questionaryMain) {
        questionaryMain.guardarDatosHistoricos(questionId);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    questionaryMain = new QuestionaryMainManager();
    
    // Load auto-saved data if available
    setTimeout(() => {
        questionaryMain.loadAutoSavedData();
    }, 1000);
    
    // Setup unload protection
    questionaryMain.setupUnloadProtection();
});

// Cleanup on page unload
window.addEventListener('unload', function() {
    if (questionaryMain) {
        questionaryMain.destroy();
    }
});

// Export for potential use in other scripts
window.QuestionaryMainManager = QuestionaryMainManager;