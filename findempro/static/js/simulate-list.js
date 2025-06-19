// Enhanced Simulation List JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let selectedSimulations = new Set();
    let progressCheckInterval;
    let currentSimulationId = null;
    
    // DOM elements
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
    
    // Initialize components
    initializeCheckboxes();
    initializeFilters();
    initializeSearch();
    initializeTooltips();
    initializeDateValidation();
    
    // Checkbox management
    function initializeCheckboxes() {
        const checkboxes = document.querySelectorAll('.simulation-checkbox');
        const selectAllBtn = document.getElementById('selectAll');
        
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    selectedSimulations.add(this.value);
                } else {
                    selectedSimulations.delete(this.value);
                }
                updateBulkActions();
            });
        });
        
        // Select all functionality
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', function() {
                const allChecked = checkboxes.length === selectedSimulations.size;
                
                checkboxes.forEach(checkbox => {
                    checkbox.checked = !allChecked;
                    if (!allChecked) {
                        selectedSimulations.add(checkbox.value);
                    } else {
                        selectedSimulations.delete(checkbox.value);
                    }
                });
                updateBulkActions();
            });
        }
    }
    
    function updateBulkActions() {
        if (selectedCount) {
            selectedCount.textContent = selectedSimulations.size;
        }
        
        if (bulkActions) {
            if (selectedSimulations.size > 0) {
                bulkActions.classList.add('show');
            } else {
                bulkActions.classList.remove('show');
            }
        }
    }
    
    // Filter management
    function initializeFilters() {
        const filterForm = document.getElementById('filterForm');
        const productFilter = document.getElementById('productFilter');
        const statusFilter = document.getElementById('statusFilter');
        const dateFromFilter = document.getElementById('dateFromFilter');
        const dateToFilter = document.getElementById('dateToFilter');
        
        // Auto-submit on filter change
        [productFilter, statusFilter].forEach(filter => {
            if (filter) {
                filter.addEventListener('change', function() {
                    filterForm.submit();
                });
            }
        });
        
        // Date range validation
        [dateFromFilter, dateToFilter].forEach(filter => {
            if (filter) {
                filter.addEventListener('change', validateDateRange);
            }
        });
    }
    
    function validateDateRange() {
        const dateFrom = document.getElementById('dateFromFilter')?.value;
        const dateTo = document.getElementById('dateToFilter')?.value;
        
        if (dateFrom && dateTo) {
            const fromDate = new Date(dateFrom);
            const toDate = new Date(dateTo);
            
            if (fromDate > toDate) {
                Swal.fire({
                    icon: 'warning',
                    title: 'Rango de fechas inválido',
                    text: 'La fecha "desde" no puede ser mayor que la fecha "hasta"',
                    confirmButtonText: 'Entendido'
                });
                
                // Clear the invalid date
                if (event.target.id === 'dateFromFilter') {
                    event.target.value = '';
                } else {
                    event.target.value = '';
                }
            }
        }
    }
    
    function initializeDateValidation() {
        const today = new Date().toISOString().split('T')[0];
        const dateInputs = document.querySelectorAll('input[type="date"]');
        
        dateInputs.forEach(input => {
            input.setAttribute('max', today);
        });
    }
    
    // Search functionality
    function initializeSearch() {
        const searchInput = document.getElementById('searchFilter');
        const searchSuggestions = document.getElementById('searchSuggestions');
        let searchTimeout;
        
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                const query = this.value.trim();
                
                if (query.length >= 2) {
                    searchTimeout = setTimeout(() => {
                        showSearchSuggestions(query);
                    }, 300);
                } else {
                    hideSearchSuggestions();
                }
            });
            
            searchInput.addEventListener('blur', function() {
                setTimeout(hideSearchSuggestions, 200);
            });
            
            searchInput.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    this.value = '';
                    hideSearchSuggestions();
                }
            });
        }
    }
    
    function showSearchSuggestions(query) {
        // This could be enhanced with AJAX to get real suggestions
        const suggestions = document.getElementById('searchSuggestions');
        if (!suggestions) return;
        
        // Mock suggestions based on visible simulations
        const mockSuggestions = [
            `Simulaciones con "${query}"`,
            `Producto: ${query}`,
            `Negocio: ${query}`,
            `ID: ${query}`
        ];
        
        suggestions.innerHTML = mockSuggestions.map(suggestion => 
            `<div class="search-suggestion" onclick="selectSuggestion('${suggestion}')">${suggestion}</div>`
        ).join('');
        
        suggestions.style.display = 'block';
    }
    
    function hideSearchSuggestions() {
        const suggestions = document.getElementById('searchSuggestions');
        if (suggestions) {
            suggestions.style.display = 'none';
        }
    }
    
    window.selectSuggestion = function(suggestion) {
        const searchInput = document.getElementById('searchFilter');
        if (searchInput) {
            searchInput.value = suggestion;
            hideSearchSuggestions();
            document.getElementById('filterForm').submit();
        }
    };
    
    // Tooltip initialization
    function initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[title]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Simulation actions
    window.startSimulation = function(simulationId) {
        Swal.fire({
            title: '¿Iniciar simulación?',
            text: 'La simulación se ejecutará y generará los resultados',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Iniciar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#28a745'
        }).then((result) => {
            if (result.isConfirmed) {
                showLoading();
                currentSimulationId = simulationId;
                
                fetch(`/simulate/api/start/${simulationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.success) {
                        showNotification('Simulación iniciada correctamente', 'success');
                        checkProgress(simulationId);
                    } else {
                        showNotification(data.error || 'Error al iniciar la simulación', 'error');
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error starting simulation:', error);
                    showNotification('Error de conexión al iniciar la simulación', 'error');
                });
            }
        });
    };
    
    window.checkProgress = function(simulationId) {
        currentSimulationId = simulationId;
        progressModal.show();
        
        const checkInterval = setInterval(() => {
            fetch(`/simulate/api/progress/${simulationId}/`)
                .then(response => response.json())
                .then(data => {
                    updateProgressUI(data);
                    
                    if (data.status === 'completed') {
                        clearInterval(checkInterval);
                        progressCheckInterval = null;
                        
                        setTimeout(() => {
                            progressModal.hide();
                            showNotification('Simulación completada exitosamente', 'success');
                            setTimeout(() => location.reload(), 1000);
                        }, 1000);
                        
                    } else if (data.status === 'failed' || data.status === 'error') {
                        clearInterval(checkInterval);
                        progressCheckInterval = null;
                        
                        progressModal.hide();
                        showNotification(data.message || 'La simulación falló', 'error');
                        setTimeout(() => location.reload(), 1000);
                    }
                })
                .catch(error => {
                    console.error('Error checking progress:', error);
                    clearInterval(checkInterval);
                    progressCheckInterval = null;
                    progressModal.hide();
                    showNotification('Error verificando el progreso', 'error');
                });
        }, 2000);
        
        progressCheckInterval = checkInterval;
    };
    
    function updateProgressUI(data) {
        const progressBar = document.getElementById('simulationProgress');
        const progressStatus = document.getElementById('progressStatus');
        const progressDetails = document.getElementById('progressDetails');
        const progressSpinner = document.getElementById('progressSpinner');
        const progressActions = document.getElementById('progressActions');
        
        if (progressBar) {
            const progress = Math.min(data.progress || 0, 100);
            progressBar.style.width = progress + '%';
            progressBar.textContent = progress.toFixed(1) + '%';
            
            // Change color based on progress
            progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
            if (progress >= 90) {
                progressBar.classList.add('bg-success');
            } else if (progress >= 50) {
                progressBar.classList.add('bg-info');
            } else {
                progressBar.classList.add('bg-warning');
            }
        }
        
        if (progressStatus) {
            progressStatus.textContent = data.message || 'Procesando...';
        }
        
        if (progressDetails) {
            if (data.results_count && data.total_expected) {
                progressDetails.textContent = `${data.results_count}/${data.total_expected} días completados`;
            } else {
                progressDetails.textContent = 'Preparando simulación...';
            }
        }
        
        // Show/hide spinner based on status
        if (progressSpinner) {
            if (data.status === 'completed') {
                progressSpinner.style.display = 'none';
            } else {
                progressSpinner.style.display = 'block';
            }
        }
        
        // Show actions for processing simulations
        if (progressActions) {
            if (data.status === 'processing' && data.progress > 10) {
                progressActions.style.display = 'block';
            } else {
                progressActions.style.display = 'none';
            }
        }
    }
    
    window.retrySimulation = function(simulationId) {
        Swal.fire({
            title: '¿Reintentar simulación?',
            text: 'Se eliminarán los resultados actuales y se volverá a ejecutar',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Reintentar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#ffc107'
        }).then((result) => {
            if (result.isConfirmed) {
                showLoading();
                
                fetch(`/simulate/api/retry/${simulationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.success) {
                        showNotification('Simulación reiniciada correctamente', 'success');
                        checkProgress(simulationId);
                    } else {
                        showNotification(data.error || 'Error al reiniciar la simulación', 'error');
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error retrying simulation:', error);
                    showNotification('Error de conexión', 'error');
                });
            }
        });
    };
    
    window.duplicateSimulation = function(simulationId) {
        Swal.fire({
            title: '¿Duplicar simulación?',
            text: 'Se creará una copia exacta de esta simulación',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Duplicar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#17a2b8'
        }).then((result) => {
            if (result.isConfirmed) {
                showLoading();
                
                fetch(`/simulate/api/duplicate/${simulationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.success) {
                        showNotification('Simulación duplicada exitosamente', 'success');
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        showNotification(data.error || 'Error al duplicar la simulación', 'error');
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error duplicating simulation:', error);
                    showNotification('Error de conexión', 'error');
                });
            }
        });
    };
    
    window.deleteSimulation = function(simulationId) {
        Swal.fire({
            title: '¿Eliminar simulación?',
            text: 'Esta acción no se puede deshacer',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Eliminar',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: '#dc3545',
            dangerMode: true
        }).then((result) => {
            if (result.isConfirmed) {
                showLoading();
                
                fetch(`/simulate/api/delete/${simulationId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.success) {
                        showNotification('Simulación eliminada correctamente', 'success');
                        
                        // Remove from UI
                        const simulationCard = document.querySelector(`[data-simulation-id="${simulationId}"]`);
                        if (simulationCard) {
                            simulationCard.style.opacity = '0.5';
                            simulationCard.style.transition = 'opacity 0.3s ease';
                            setTimeout(() => {
                                simulationCard.remove();
                                
                                // Check if page is empty
                                const remainingCards = document.querySelectorAll('[data-simulation-id]');
                                if (remainingCards.length === 0) {
                                    location.reload();
                                }
                            }, 300);
                        }
                    } else {
                        showNotification(data.error || 'Error al eliminar la simulación', 'error');
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error deleting simulation:', error);
                    showNotification('Error de conexión', 'error');
                });
            }
        });
    };
    
    // Bulk actions
    window.bulkAction = function(action) {
        if (selectedSimulations.size === 0) {
            showNotification('Seleccione al menos una simulación', 'warning');
            return;
        }
        
        const actionTexts = {
            'start': 'iniciar',
            'export': 'exportar',
            'duplicate': 'duplicar',
            'delete': 'eliminar'
        };
        
        const actionText = actionTexts[action] || action;
        const isDestructive = action === 'delete';
        
        Swal.fire({
            title: `¿${actionText.charAt(0).toUpperCase() + actionText.slice(1)} simulaciones seleccionadas?`,
            text: `Se ${actionText}án ${selectedSimulations.size} simulación(es)`,
            icon: isDestructive ? 'warning' : 'question',
            showCancelButton: true,
            confirmButtonText: actionText.charAt(0).toUpperCase() + actionText.slice(1),
            cancelButtonText: 'Cancelar',
            confirmButtonColor: isDestructive ? '#dc3545' : '#28a745'
        }).then((result) => {
            if (result.isConfirmed) {
                executeBulkAction(action, Array.from(selectedSimulations));
            }
        });
    };
    
    function executeBulkAction(action, simulationIds) {
        showLoading();
        
        const promises = simulationIds.map(id => {
            return fetch(`/simulate/api/${action}/${id}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            }).then(response => response.json());
        });
        
        Promise.allSettled(promises)
            .then(results => {
                hideLoading();
                
                const successful = results.filter(result => 
                    result.status === 'fulfilled' && result.value.success
                ).length;
                
                const failed = results.length - successful;
                
                if (successful > 0) {
                    showNotification(
                        `${successful} simulación(es) procesada(s) correctamente${failed > 0 ? `, ${failed} fallaron` : ''}`,
                        failed > 0 ? 'warning' : 'success'
                    );
                    
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showNotification('No se pudo procesar ninguna simulación', 'error');
                }
                
                // Clear selection
                selectedSimulations.clear();
                updateBulkActions();
            })
            .catch(error => {
                hideLoading();
                console.error('Error in bulk action:', error);
                showNotification('Error procesando las simulaciones', 'error');
            });
    }
    
    // Export functionality
    window.exportData = function(format) {
        const url = new URL('/simulate/export/', window.location.origin);
        url.searchParams.set('format', format);
        
        // Add current filters to export
        const currentParams = new URLSearchParams(window.location.search);
        for (const [key, value] of currentParams) {
            if (key !== 'page' && key !== 'page_size') {
                url.searchParams.set(key, value);
            }
        }
        
        showLoading();
        
        // Create temporary link for download
        const link = document.createElement('a');
        link.href = url.toString();
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        setTimeout(() => {
            hideLoading();
            showNotification(`Exportando datos en formato ${format.toUpperCase()}`, 'info');
        }, 1000);
    };
    
    window.exportSelected = function() {
        if (selectedSimulations.size === 0) {
            showNotification('Seleccione al menos una simulación para exportar', 'warning');
            return;
        }
        
        Swal.fire({
            title: 'Seleccionar formato',
            text: '¿En qué formato desea exportar las simulaciones seleccionadas?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'CSV',
            cancelButtonText: 'Cancelar',
            showDenyButton: true,
            denyButtonText: 'Excel'
        }).then((result) => {
            if (result.isConfirmed) {
                exportSelectedData('csv');
            } else if (result.isDenied) {
                exportSelectedData('excel');
            }
        });
    };
    
    function exportSelectedData(format) {
        const url = new URL('/simulate/export/', window.location.origin);
        url.searchParams.set('format', format);
        
        // Add selected IDs
        selectedSimulations.forEach(id => {
            url.searchParams.append('ids', id);
        });
        
        showLoading();
        
        fetch(url.toString())
            .then(response => {
                if (response.ok) {
                    return response.blob();
                }
                throw new Error('Export failed');
            })
            .then(blob => {
                hideLoading();
                
                // Create download link
                const downloadUrl = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = `simulaciones_seleccionadas.${format}`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(downloadUrl);
                
                showNotification(`${selectedSimulations.size} simulaciones exportadas`, 'success');
            })
            .catch(error => {
                hideLoading();
                console.error('Export error:', error);
                showNotification('Error al exportar las simulaciones', 'error');
            });
    }
    
    // Advanced filters toggle
    window.toggleAdvancedFilters = function(event) {
        event.preventDefault();
        
        const advancedFilters = document.getElementById('advancedFilters');
        const toggleIcon = document.getElementById('advancedToggleIcon');
        
        if (advancedFilters.classList.contains('collapsed')) {
            advancedFilters.classList.remove('collapsed');
            toggleIcon.classList.remove('bx-chevron-down');
            toggleIcon.classList.add('bx-chevron-up');
        } else {
            advancedFilters.classList.add('collapsed');
            toggleIcon.classList.remove('bx-chevron-up');
            toggleIcon.classList.add('bx-chevron-down');
        }
    };
    
    // Page size change
    window.changePageSize = function(pageSize) {
        const url = new URL(window.location);
        url.searchParams.set('page_size', pageSize);
        url.searchParams.delete('page'); // Reset to first page
        window.location.href = url.toString();
    };
    
    // Refresh data
    window.refreshData = function() {
        showLoading();
        setTimeout(() => {
            location.reload();
        }, 500);
    };
    
    // Additional simulation actions
    window.downloadReport = function(simulationId) {
        const url = `/simulate/api/download-report/${simulationId}/`;
        
        showLoading();
        
        fetch(url)
            .then(response => {
                if (response.ok) {
                    return response.blob();
                }
                throw new Error('Download failed');
            })
            .then(blob => {
                hideLoading();
                
                const downloadUrl = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = `reporte_simulacion_${simulationId}.pdf`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(downloadUrl);
                
                showNotification('Reporte descargado correctamente', 'success');
            })
            .catch(error => {
                hideLoading();
                console.error('Download error:', error);
                showNotification('Error al descargar el reporte', 'error');
            });
    };
    
    window.shareSimulation = function(simulationId) {
        const shareUrl = `${window.location.origin}/simulate/result/${simulationId}/`;
        
        if (navigator.share) {
            navigator.share({
                title: `Simulación #${simulationId}`,
                text: 'Resultados de simulación de demanda',
                url: shareUrl
            }).catch(err => console.log('Error sharing:', err));
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(shareUrl).then(() => {
                showNotification('Enlace copiado al portapapeles', 'success');
            }).catch(() => {
                showNotification('No se pudo copiar el enlace', 'error');
            });
        }
    };
    
    window.editSimulation = function(simulationId) {
        // This would redirect to an edit page or open a modal
        window.location.href = `/simulate/edit/${simulationId}/`;
    };
    
    window.viewErrorLog = function(simulationId) {
        fetch(`/simulate/api/error-log/${simulationId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.error_log) {
                    Swal.fire({
                        title: 'Log de Errores',
                        html: `<pre style="text-align: left; max-height: 300px; overflow-y: auto;">${data.error_log}</pre>`,
                        icon: 'error',
                        confirmButtonText: 'Cerrar',
                        width: '80%'
                    });
                } else {
                    showNotification('No hay información de error disponible', 'info');
                }
            })
            .catch(error => {
                console.error('Error fetching error log:', error);
                showNotification('Error al obtener el log de errores', 'error');
            });
    };
    
    // Utility functions
    function showLoading() {
        if (loadingOverlay) {
            loadingOverlay.classList.add('show');
        }
    }
    
    function hideLoading() {
        if (loadingOverlay) {
            loadingOverlay.classList.remove('show');
        }
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    function showNotification(message, type = 'info') {
        // Remove existing notifications
        document.querySelectorAll('.toast-notification').forEach(notification => {
            notification.remove();
        });
        
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed toast-notification`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 350px;
            min-width: 300px;
            opacity: 0;
            transition: opacity 0.3s ease, transform 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            border-radius: 8px;
            border: none;
            transform: translateX(100%);
        `;
        
        const iconClass = {
            'success': 'bx-check-circle',
            'error': 'bx-error-circle',
            'warning': 'bx-error',
            'info': 'bx-info-circle'
        };
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bx ${iconClass[type] || iconClass.info} me-2 fs-5"></i>
                <span class="flex-grow-1">${message}</span>
                <button type="button" class="btn-close ms-2" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, type === 'error' ? 7000 : 5000);
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + A to select all
        if ((e.ctrlKey || e.metaKey) && e.key === 'a' && !e.target.matches('input, textarea')) {
            e.preventDefault();
            const checkboxes = document.querySelectorAll('.simulation-checkbox');
            const allChecked = checkboxes.length === selectedSimulations.size;
            
            checkboxes.forEach(checkbox => {
                checkbox.checked = !allChecked;
                if (!allChecked) {
                    selectedSimulations.add(checkbox.value);
                } else {
                    selectedSimulations.delete(checkbox.value);
                }
            });
            updateBulkActions();
        }
        
        // Escape to clear selection
        if (e.key === 'Escape') {
            selectedSimulations.clear();
            document.querySelectorAll('.simulation-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
            updateBulkActions();
        }
        
        // F5 or Ctrl+R to refresh
        if (e.key === 'F5' || ((e.ctrlKey || e.metaKey) && e.key === 'r')) {
            e.preventDefault();
            refreshData();
        }
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        if (progressCheckInterval) {
            clearInterval(progressCheckInterval);
        }
    });
    
    // Auto-refresh for processing simulations (optional)
    const hasProcessingSimulations = document.querySelectorAll('.status-processing').length > 0;
    if (hasProcessingSimulations) {
        setInterval(() => {
            // Only refresh if no modal is open and no selections are made
            if (!document.querySelector('.modal.show') && selectedSimulations.size === 0) {
                location.reload();
            }
        }, 30000); // Every 30 seconds
    }
    
    console.log('Simulation list enhanced JavaScript loaded successfully');
});