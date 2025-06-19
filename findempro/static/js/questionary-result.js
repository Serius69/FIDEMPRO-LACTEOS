/**
 * Questionary Result Management
 * Enhanced JavaScript functionality for questionary result page
 */

class QuestionaryResultManager {
    constructor() {
        this.resultId = null;
        this.isEditing = false;
        this.originalValues = {};
        this.init();
    }

    /**
     * Initialize the questionary result functionality
     */
    init() {
        this.extractResultId();
        this.setupEventListeners();
        this.initializeTooltips();
        this.setupKeyboardShortcuts();
        this.loadOriginalValues();
    }

    /**
     * Extract result ID from URL
     */
    extractResultId() {
        const pathParts = window.location.pathname.split('/').filter(Boolean);
        this.resultId = pathParts[pathParts.length - 1];
        console.log('Result ID:', this.resultId);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Edit button
        const editBtn = document.getElementById('editarRespuestasBtn');
        if (editBtn) {
            editBtn.addEventListener('click', () => this.startEditing());
        }

        // Save button
        const saveBtn = document.getElementById('guardarRespuestasBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveChanges());
        }

        // Cancel button
        const cancelBtn = document.getElementById('cancelarEdicionBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancelEditing());
        }

        // Export buttons
        this.setupExportButtons();

        // Print button enhancement
        const printButtons = document.querySelectorAll('[onclick*="print"]');
        printButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.printQuestionary();
            });
        });
    }

    /**
     * Setup export button functionality
     */
    setupExportButtons() {
        const exportPDFBtn = document.querySelector('[onclick*="exportToPDF"]');
        if (exportPDFBtn) {
            exportPDFBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.exportToPDF();
            });
        }

        const exportExcelBtn = document.querySelector('[onclick*="exportToExcel"]');
        if (exportExcelBtn) {
            exportExcelBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.exportToExcel();
            });
        }

        const generateReportBtn = document.querySelector('[onclick*="generateReport"]');
        if (generateReportBtn) {
            generateReportBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.generateReport();
            });
        }
    }

    /**
     * Initialize Bootstrap tooltips
     */
    initializeTooltips() {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
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
     * Load original values for comparison
     */
    loadOriginalValues() {
        const respuestas = document.querySelectorAll('.respuesta');
        respuestas.forEach(respuesta => {
            const answerId = respuesta.dataset.answerId;
            const originalValue = respuesta.dataset.originalValue || respuesta.textContent.trim();
            this.originalValues[answerId] = originalValue;
        });
    }

    /**
     * Start editing mode
     */
    startEditing() {
        this.isEditing = true;
        this.showLoading();

        const respuestas = document.querySelectorAll('.respuesta');
        let processedCount = 0;

        respuestas.forEach(respuesta => {
            const valorActual = respuesta.dataset.originalValue || respuesta.textContent.trim();
            const questionType = respuesta.dataset.questionType;
            const answerId = respuesta.dataset.answerId;

            // Create appropriate input based on question type
            let inputHtml = '';
            
            if (questionType === '3') {
                // Historical data - use textarea
                inputHtml = `
                    <div class="form-group">
                        <label class="form-label small">Datos históricos (separados por comas):</label>
                        <textarea class="form-control editable-input" rows="4" 
                                  data-answer-id="${answerId}"
                                  placeholder="Ingrese valores separados por comas">${this.formatHistoricalData(valorActual)}</textarea>
                        <small class="text-muted">Separe los valores con comas. Mínimo 30 valores requeridos.</small>
                        <div class="mt-2">
                            <button type="button" class="btn btn-sm btn-info" onclick="questionaryResult.validateHistoricalData('${answerId}')">
                                <i class="fa fa-check"></i> Validar
                            </button>
                        </div>
                    </div>
                `;
            } else if (questionType === '2') {
                // Selection type - would need the options from backend
                inputHtml = `
                    <div class="form-group">
                        <label class="form-label small">Respuesta seleccionada:</label>
                        <input type="text" class="form-control editable-input" 
                               data-answer-id="${answerId}"
                               value="${this.escapeHtml(valorActual)}"
                               placeholder="Ingrese la respuesta">
                        <small class="text-muted">Modifique la respuesta según sea necesario.</small>
                    </div>
                `;
            } else {
                // Numeric or text
                inputHtml = `
                    <div class="form-group">
                        <label class="form-label small">Valor de respuesta:</label>
                        <input type="text" class="form-control editable-input" 
                               data-answer-id="${answerId}"
                               value="${this.escapeHtml(valorActual)}"
                               placeholder="Ingrese el valor">
                        <small class="text-muted">Ingrese el nuevo valor para esta pregunta.</small>
                    </div>
                `;
            }

            respuesta.innerHTML = inputHtml;
            processedCount++;
        });

        // Show editing controls
        this.toggleEditingControls(true);
        this.hideLoading();
        
        this.showSuccessMessage(`Modo de edición activado. ${processedCount} campos editables.`);
    }

    /**
     * Save changes
     */
    async saveChanges() {
        this.showLoading();
        
        const editableInputs = document.querySelectorAll('.editable-input');
        const promises = [];
        let updatedCount = 0;

        for (const input of editableInputs) {
            const newValue = input.value.trim();
            const answerId = input.dataset.answerId;
            const originalValue = this.originalValues[answerId];

            // Only update if value changed
            if (newValue !== originalValue && newValue !== '') {
                const promise = this.updateAnswer(answerId, newValue)
                    .then(response => {
                        if (response.success) {
                            updatedCount++;
                            // Update the stored original value
                            this.originalValues[answerId] = newValue;
                            return { success: true, answerId, newValue };
                        } else {
                            throw new Error(response.message || 'Error updating answer');
                        }
                    })
                    .catch(error => {
                        console.error(`Error updating answer ${answerId}:`, error);
                        return { success: false, answerId, error: error.message };
                    });
                
                promises.push(promise);
            }
        }

        try {
            const results = await Promise.all(promises);
            const failures = results.filter(r => !r.success);
            
            if (failures.length > 0) {
                this.showErrorMessage(`Se actualizaron ${updatedCount} respuestas, pero ${failures.length} fallaron.`);
                console.error('Failed updates:', failures);
            } else {
                this.showSuccessMessage(`Se actualizaron ${updatedCount} respuestas exitosamente.`);
            }

            // Exit editing mode and refresh display
            this.exitEditingMode();
            
        } catch (error) {
            console.error('Error in saveChanges:', error);
            this.showErrorMessage('Error al guardar los cambios: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Update individual answer via AJAX
     */
    async updateAnswer(answerId, newValue) {
        const url = `/questionary/result/${this.resultId}/questionary/update_question_view/${answerId}/`;
        
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    new_answer: newValue,
                    answerId: answerId,
                    resultId: this.resultId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Network error:', error);
            throw error;
        }
    }

    /**
     * Cancel editing
     */
    cancelEditing() {
        if (confirm('¿Está seguro de que desea cancelar? Se perderán todos los cambios no guardados.')) {
            this.exitEditingMode();
            this.showSuccessMessage('Edición cancelada.');
        }
    }

    /**
     * Exit editing mode and restore original display
     */
    exitEditingMode() {
        this.isEditing = false;
        
        // Reload the page to restore original state
        // In a more sophisticated implementation, you could restore the original HTML
        window.location.reload();
    }

    /**
     * Toggle editing controls visibility
     */
    toggleEditingControls(isEditing) {
        const editContainer = document.querySelector('.edit-btn-container');
        const saveCancelContainer = document.querySelector('.save-cancel-btns-container');

        if (editContainer && saveCancelContainer) {
            editContainer.style.display = isEditing ? 'none' : 'block';
            saveCancelContainer.style.display = isEditing ? 'block' : 'none';
        }
    }

    /**
     * Format historical data for editing
     */
    formatHistoricalData(data) {
        if (!data) return '';
        
        // Try to extract numbers from the data
        const numbers = data.match(/[\d.,]+/g);
        if (numbers) {
            return numbers.join(', ');
        }
        
        return data;
    }

    /**
     * Validate historical data
     */
    validateHistoricalData(answerId) {
        const textarea = document.querySelector(`textarea[data-answer-id="${answerId}"]`);
        if (!textarea) return;

        const data = textarea.value.trim();
        const values = data.split(',').map(v => v.trim()).filter(v => v !== '');
        const numericValues = values.map(v => parseFloat(v)).filter(v => !isNaN(v));

        if (numericValues.length < 30) {
            this.showErrorMessage(`Se requieren al menos 30 valores. Actualmente: ${numericValues.length}`);
            textarea.classList.add('is-invalid');
            return false;
        }

        if (numericValues.length !== values.length) {
            this.showErrorMessage('Algunos valores no son numéricos válidos.');
            textarea.classList.add('is-invalid');
            return false;
        }

        // Show statistics
        const stats = this.calculateStatistics(numericValues);
        this.showDataStatistics(answerId, numericValues.length, stats);
        
        textarea.classList.remove('is-invalid');
        textarea.classList.add('is-valid');
        this.showSuccessMessage(`Datos válidos: ${numericValues.length} valores`);
        return true;
    }

    /**
     * Calculate statistics for historical data
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
    showDataStatistics(answerId, count, stats) {
        const textarea = document.querySelector(`textarea[data-answer-id="${answerId}"]`);
        if (!textarea) return;

        let statsDiv = textarea.parentElement.querySelector('.data-statistics');
        
        if (!statsDiv) {
            statsDiv = document.createElement('div');
            statsDiv.className = 'data-statistics mt-2 p-2 bg-light border rounded small';
            textarea.parentElement.appendChild(statsDiv);
        }

        statsDiv.innerHTML = `
            <strong>Estadísticas:</strong>
            Total: ${count} | 
            Promedio: ${stats.mean.toFixed(2)} | 
            Mediana: ${stats.median.toFixed(2)} | 
            Min: ${stats.min.toFixed(2)} | 
            Max: ${stats.max.toFixed(2)}
        `;
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + E for edit
            if ((e.ctrlKey || e.metaKey) && e.key === 'e' && !this.isEditing) {
                e.preventDefault();
                this.startEditing();
            }

            // Ctrl/Cmd + S for save (when editing)
            if ((e.ctrlKey || e.metaKey) && e.key === 's' && this.isEditing) {
                e.preventDefault();
                this.saveChanges();
            }

            // Escape to cancel editing
            if (e.key === 'Escape' && this.isEditing) {
                e.preventDefault();
                this.cancelEditing();
            }

            // Ctrl/Cmd + P for print
            if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
                e.preventDefault();
                this.printQuestionary();
            }
        });
    }

    /**
     * Enhanced print functionality
     */
    printQuestionary() {
        this.showLoading();

        // Hide non-printable elements
        const nonPrintable = document.querySelectorAll(
            '.action-buttons, .edit-btn-container, .save-cancel-btns-container, .export-buttons, .pagination, .btn'
        );
        nonPrintable.forEach(el => el.style.display = 'none');

        // Add print styles
        const printStyles = `
            <style media="print">
                @page { margin: 1in; }
                body { font-size: 12pt; line-height: 1.4; }
                .result-header { background: #667eea !important; color: white !important; }
                .card { page-break-inside: avoid; }
                .table { font-size: 10pt; }
                .historical-data-view { max-height: none; }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', printStyles);

        setTimeout(() => {
            window.print();
            this.hideLoading();
            
            // Restore elements after print
            nonPrintable.forEach(el => el.style.display = '');
        }, 500);
    }

    /**
     * Export to PDF functionality
     */
    exportToPDF() {
        this.showLoading();
        
        // Simulate PDF generation
        setTimeout(() => {
            this.hideLoading();
            this.showSuccessMessage('Función de exportación PDF en desarrollo. Use Ctrl+P para imprimir.');
        }, 1000);
    }

    /**
     * Export to Excel functionality
     */
    exportToExcel() {
        this.showLoading();
        
        try {
            const data = this.collectTableData();
            this.downloadExcel(data);
            this.showSuccessMessage('Datos exportados a Excel exitosamente.');
        } catch (error) {
            this.showErrorMessage('Error al exportar a Excel: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Collect table data for export
     */
    collectTableData() {
        const rows = document.querySelectorAll('#resultsTable tbody tr');
        const data = [];
        
        rows.forEach(row => {
            const cells = row.cells;
            if (cells.length >= 5) {
                data.push({
                    'Número': cells[0].textContent.trim(),
                    'Pregunta': cells[1].textContent.trim(),
                    'Variable': cells[2].textContent.trim(),
                    'Respuesta': cells[3].textContent.trim(),
                    'Unidad': cells[4].textContent.trim()
                });
            }
        });
        
        return data;
    }

    /**
     * Download Excel file
     */
    downloadExcel(data) {
        // Convert to CSV format
        const headers = Object.keys(data[0] || {});
        let csv = headers.join(',') + '\n';
        
        data.forEach(row => {
            const values = headers.map(header => `"${(row[header] || '').toString().replace(/"/g, '""')}"`);
            csv += values.join(',') + '\n';
        });

        // Create and download file
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `cuestionario_resultado_${this.resultId}_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(link.href);
    }

    /**
     * Generate report functionality
     */
    generateReport() {
        this.showLoading();
        
        setTimeout(() => {
            this.hideLoading();
            this.showSuccessMessage('Función de generación de reportes en desarrollo.');
        }, 1000);
    }

    /**
     * Utility functions
     */
    getCSRFToken() {
        const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) return csrfInput.value;
        
        const csrfCookie = document.cookie.split(';')
            .find(cookie => cookie.trim().startsWith('csrftoken='));
        return csrfCookie ? csrfCookie.split('=')[1] : '';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showLoading() {
        const spinner = document.querySelector('.loading-spinner');
        if (spinner) {
            spinner.style.display = 'flex';
        }
    }

    hideLoading() {
        const spinner = document.querySelector('.loading-spinner');
        if (spinner) {
            spinner.style.display = 'none';
        }
    }

    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }

    showErrorMessage(message) {
        this.showMessage(message, 'danger');
    }

    showMessage(message, type) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed success-animation`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            <i class="fa fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'}"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);

        // Auto-remove after 4 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 4000);
    }

    /**
     * Cleanup method
     */
    destroy() {
        // Remove event listeners
        document.removeEventListener('keydown', this.setupKeyboardShortcuts);
        
        // Dispose tooltips
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            if (el._tooltip && el._tooltip.dispose) {
                el._tooltip.dispose();
            }
        });
    }
}

// Global instance
let questionaryResult;

// Global functions for backward compatibility
function showLoading() {
    if (questionaryResult) {
        questionaryResult.showLoading();
    }
}

function hideLoading() {
    if (questionaryResult) {
        questionaryResult.hideLoading();
    }
}

function showSuccessMessage(message) {
    if (questionaryResult) {
        questionaryResult.showSuccessMessage(message);
    }
}

function exportToPDF() {
    if (questionaryResult) {
        questionaryResult.exportToPDF();
    }
}

function exportToExcel() {
    if (questionaryResult) {
        questionaryResult.exportToExcel();
    }
}

function generateReport() {
    if (questionaryResult) {
        questionaryResult.generateReport();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    questionaryResult = new QuestionaryResultManager();
});

// Cleanup on page unload
window.addEventListener('unload', function() {
    if (questionaryResult) {
        questionaryResult.destroy();
    }
});

// Export for potential use in other scripts
window.QuestionaryResultManager = QuestionaryResultManager;