// Report List Enhanced JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let searchTimeout;
    let selectedReports = new Set();
    
    // DOM elements
    const selectAllCheckbox = document.getElementById('selectAll');
    const reportCheckboxes = document.querySelectorAll('.report-checkbox');
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');
    const searchInput = document.getElementById('searchInput');
    const searchForm = document.getElementById('searchForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Filter elements
    const typeFilter = document.getElementById('typeFilter');
    const statusFilter = document.getElementById('statusFilter');
    const sortFilter = document.getElementById('sortFilter');
    
    // View toggle elements
    const viewToggleBtns = document.querySelectorAll('.view-toggle-btn');
    const tableView = document.getElementById('tableView');
    const gridView = document.getElementById('gridView');
    
    // Initialize components
    initializeSelectAll();
    initializeSearch();
    initializeFilters();
    initializeViewToggle();
    initializeSorting();
    initializeTooltips();
    initializeKeyboardShortcuts();
    
    // Select all functionality
    function initializeSelectAll() {
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                const isChecked = this.checked;
                reportCheckboxes.forEach(checkbox => {
                    checkbox.checked = isChecked;
                    updateSelectedReports(checkbox.value, isChecked);
                });
                updateBulkActions();
            });
        }
        
        reportCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateSelectedReports(this.value, this.checked);
                updateSelectAllState();
                updateBulkActions();
            });
        });
    }
    
    function updateSelectedReports(reportId, isSelected) {
        if (isSelected) {
            selectedReports.add(reportId);
        } else {
            selectedReports.delete(reportId);
        }
    }
    
    function updateSelectAllState() {
        if (!selectAllCheckbox) return;
        
        const checkedBoxes = document.querySelectorAll('.report-checkbox:checked').length;
        const totalBoxes = reportCheckboxes.length;
        
        selectAllCheckbox.checked = checkedBoxes === totalBoxes && totalBoxes > 0;
        selectAllCheckbox.indeterminate = checkedBoxes > 0 && checkedBoxes < totalBoxes;
    }
    
    function updateBulkActions() {
        const selectedCountEl = document.getElementById('selectedCount');
        const bulkActionsEl = document.getElementById('bulkActions');
        
        if (selectedCountEl) {
            selectedCountEl.textContent = selectedReports.size;
        }
        
        if (bulkActionsEl) {
            if (selectedReports.size > 0) {
                bulkActionsEl.classList.add('show');
            } else {
                bulkActionsEl.classList.remove('show');
            }
        }
    }
    
    // Search functionality
    function initializeSearch() {
        if (!searchInput) return;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            searchTimeout = setTimeout(() => {
                if (query.length >= 2 || query.length === 0) {
                    submitFilters();
                }
            }, 500);
        });
        
        // Search suggestions functionality
        searchInput.addEventListener('focus', function() {
            showSearchSuggestions();
        });
        
        searchInput.addEventListener('blur', function() {
            setTimeout(() => {
                hideSearchSuggestions();
            }, 200);
        });
        
        // Clear search on Escape
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                submitFilters();
            }
        });
    }
    
    function showSearchSuggestions() {
        // This could be enhanced with AJAX to load recent searches
        const suggestions = document.getElementById('searchSuggestions');
        if (suggestions) {
            // For now, just hide it - could implement recent searches here
            suggestions.style.display = 'none';
        }
    }
    
    function hideSearchSuggestions() {
        const suggestions = document.getElementById('searchSuggestions');
        if (suggestions) {
            suggestions.style.display = 'none';
        }
    }
    
    // Filters functionality
    function initializeFilters() {
        [typeFilter, statusFilter, sortFilter].forEach(filter => {
            if (filter) {
                filter.addEventListener('change', function() {
                    submitFilters();
                });
            }
        });
    }
    
    function submitFilters() {
        const formData = new FormData();
        
        if (searchInput && searchInput.value.trim()) {
            formData.append('search', searchInput.value.trim());
        }
        
        if (typeFilter && typeFilter.value) {
            formData.append('type', typeFilter.value);
        }
        
        if (statusFilter && statusFilter.value) {
            formData.append('status', statusFilter.value);
        }
        
        if (sortFilter && sortFilter.value) {
            formData.append('sort', sortFilter.value);
        }
        
        // Build URL with parameters
        const params = new URLSearchParams(formData);
        const url = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
        
        // Add loading state
        showLoading();
        
        // Navigate to filtered URL
        window.location.href = url;
    }
    
    // View toggle functionality
    function initializeViewToggle() {
        viewToggleBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const viewType = this.getAttribute('data-view');
                
                // Update active button
                viewToggleBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // Show/hide views
                if (viewType === 'grid') {
                    if (tableView) tableView.classList.remove('active');
                    if (gridView) gridView.classList.add('active');
                } else {
                    if (gridView) gridView.classList.remove('active');
                    if (tableView) tableView.classList.add('active');
                }
                
                // Save preference
                localStorage.setItem('reportListView', viewType);
                
                // Update checkboxes in new view
                updateCheckboxesInCurrentView();
            });
        });
        
        // Load saved preference
        const savedView = localStorage.getItem('reportListView');
        if (savedView) {
            const btn = document.querySelector(`[data-view="${savedView}"]`);
            if (btn) btn.click();
        }
    }
    
    function updateCheckboxesInCurrentView() {
        // Re-initialize checkboxes for the current view
        const currentViewCheckboxes = document.querySelectorAll('.report-checkbox:not([disabled])');
        currentViewCheckboxes.forEach(checkbox => {
            if (selectedReports.has(checkbox.value)) {
                checkbox.checked = true;
            }
        });
    }
    
    // Sorting functionality
    function initializeSorting() {
        const sortableHeaders = document.querySelectorAll('.sortable');
        
        sortableHeaders.forEach(header => {
            header.addEventListener('click', function() {
                const sortField = this.getAttribute('data-sort');
                const currentSort = sortFilter ? sortFilter.value : '';
                
                let newSort;
                if (currentSort === sortField) {
                    newSort = '-' + sortField; // Toggle to descending
                } else if (currentSort === '-' + sortField) {
                    newSort = sortField; // Toggle to ascending
                } else {
                    newSort = '-' + sortField; // Default to descending
                }
                
                if (sortFilter) {
                    sortFilter.value = newSort;
                    submitFilters();
                }
            });
        });
        
        // Update header visual state
        updateSortHeaders();
    }
    
    function updateSortHeaders() {
        const currentSort = sortFilter ? sortFilter.value : '';
        const sortableHeaders = document.querySelectorAll('.sortable');
        
        sortableHeaders.forEach(header => {
            const field = header.getAttribute('data-sort');
            header.classList.remove('sorted-asc', 'sorted-desc');
            
            if (currentSort === field) {
                header.classList.add('sorted-asc');
            } else if (currentSort === '-' + field) {
                header.classList.add('sorted-desc');
            }
        });
    }
    
    // Tooltips initialization
    function initializeTooltips() {
        const tooltipElements = document.querySelectorAll('[title]');
        tooltipElements.forEach(element => {
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                new bootstrap.Tooltip(element, {
                    placement: 'top',
                    trigger: 'hover focus'
                });
            }
        });
    }
    
    // Keyboard shortcuts
    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + F for search focus
            if ((e.ctrlKey || e.metaKey) && e.key === 'f' && searchInput) {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }
            
            // Escape to clear selection
            if (e.key === 'Escape') {
                if (selectedReports.size > 0) {
                    reportCheckboxes.forEach(checkbox => checkbox.checked = false);
                    selectedReports.clear();
                    updateSelectAllState();
                    updateBulkActions();
                }
            }
            
            // Ctrl/Cmd + A to select all visible
            if ((e.ctrlKey || e.metaKey) && e.key === 'a' && e.target !== searchInput) {
                e.preventDefault();
                if (selectAllCheckbox) {
                    selectAllCheckbox.checked = true;
                    selectAllCheckbox.dispatchEvent(new Event('change'));
                }
            }
            
            // Arrow keys for navigation in table
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                navigateTable(e.key === 'ArrowDown' ? 1 : -1);
            }
        });
    }
    
    function navigateTable(direction) {
        const rows = document.querySelectorAll('.table-enhanced tbody tr');
        const focusedElement = document.activeElement;
        let currentIndex = -1;
        
        // Find current row
        rows.forEach((row, index) => {
            if (row.contains(focusedElement)) {
                currentIndex = index;
            }
        });
        
        // Navigate to next/previous row
        const nextIndex = currentIndex + direction;
        if (nextIndex >= 0 && nextIndex < rows.length) {
            const nextRow = rows[nextIndex];
            const firstLink = nextRow.querySelector('a');
            if (firstLink) {
                firstLink.focus();
            }
        }
    }
    
    // Global functions for inline event handlers
    window.toggleStatus = function(reportId) {
        showLoading();
        
        fetch(`/reports/toggle-status/${reportId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showNotification(data.message || 'Estado actualizado correctamente', 'success');
                // Reload page to reflect changes
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showNotification(data.error || 'Error al cambiar el estado', 'error');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            showNotification('Error de conexión', 'error');
        });
    };
    
    window.bulkAction = function(action) {
        if (selectedReports.size === 0) {
            showNotification('Seleccione al menos un reporte', 'warning');
            return;
        }
        
        const actionText = {
            'activate': 'activar',
            'deactivate': 'desactivar',
            'delete': 'eliminar'
        };
        
        const confirmMessage = `¿Está seguro de ${actionText[action]} ${selectedReports.size} reporte(s)?`;
        if (!confirm(confirmMessage)) {
            return;
        }
        
        showLoading();
        
        fetch('/reports/bulk-operations/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                operation: action,
                report_ids: Array.from(selectedReports)
            })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.success) {
                showNotification(data.message, 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showNotification(data.error || 'Error en la operación', 'error');
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error:', error);
            showNotification('Error de conexión', 'error');
        });
    };
    
    window.bulkExport = function() {
        if (selectedReports.size === 0) {
            showNotification('Seleccione al menos un reporte para exportar', 'warning');
            return;
        }
        
        // Show export format selection
        const format = showExportFormatDialog();
        if (!format) return;
        
        const ids = Array.from(selectedReports).join(',');
        const exportUrl = `/reports/export/?format=${format}&ids=${ids}`;
        
        // Create temporary link for download
        const link = document.createElement('a');
        link.href = exportUrl;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification(`Exportando ${selectedReports.size} reportes en formato ${format.toUpperCase()}`, 'info');
    };
    
    function showExportFormatDialog() {
        const formats = [
            { value: 'csv', label: 'CSV (Comma Separated Values)' },
            { value: 'excel', label: 'Excel (Microsoft Excel)' },
            { value: 'pdf', label: 'PDF (Portable Document Format)' }
        ];
        
        let formatSelection = '';
        const formatOptions = formats.map(f => `${f.value}: ${f.label}`).join('\n');
        
        do {
            formatSelection = prompt(
                `Seleccione el formato de exportación:\n\n${formatOptions}\n\nIngrese: csv, excel o pdf`, 
                'csv'
            );
            
            if (formatSelection === null) return null; // User cancelled
            
            formatSelection = formatSelection.toLowerCase().trim();
            
        } while (!formats.some(f => f.value === formatSelection));
        
        return formatSelection;
    }
    
    window.toggleExportMenu = function() {
        const menu = document.getElementById('exportMenu');
        if (menu) {
            menu.classList.toggle('show');
        }
    };
    
    window.printReports = function() {
        // Prepare for printing
        const printWindow = window.open('', '_blank');
        const printContent = generatePrintContent();
        
        printWindow.document.write(printContent);
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
        printWindow.close();
    };
    
    function generatePrintContent() {
        const reports = Array.from(document.querySelectorAll('.table-enhanced tbody tr:not(.empty-state)'));
        const reportData = reports.map(row => {
            const cells = row.querySelectorAll('td');
            return {
                title: cells[1]?.querySelector('.report-title')?.textContent?.trim() || '',
                product: cells[2]?.textContent?.trim() || '',
                type: cells[3]?.textContent?.trim() || '',
                date: cells[4]?.textContent?.trim() || '',
                status: cells[5]?.textContent?.trim() || ''
            };
        });
        
        const currentDate = new Date().toLocaleDateString();
        
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Lista de Reportes - ${currentDate}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f5f5f5; font-weight: bold; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                    .footer { margin-top: 20px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <h1>📊 Lista de Reportes</h1>
                <p><strong>Fecha de generación:</strong> ${currentDate}</p>
                <p><strong>Total de reportes:</strong> ${reportData.length}</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Título del Reporte</th>
                            <th>Producto</th>
                            <th>Tipo</th>
                            <th>Fecha</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${reportData.map(report => `
                            <tr>
                                <td>${report.title}</td>
                                <td>${report.product}</td>
                                <td>${report.type}</td>
                                <td>${report.date}</td>
                                <td>${report.status}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                
                <div class="footer">
                    <p>Generado automáticamente por el Sistema de Reportes</p>
                </div>
            </body>
            </html>
        `;
    }
    
    window.changePageSize = function(pageSize) {
        const url = new URL(window.location);
        url.searchParams.set('page_size', pageSize);
        url.searchParams.delete('page'); // Reset to first page
        
        showLoading();
        window.location.href = url.toString();
    };
    
    // Utility functions
    function showLoading() {
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
        
        // Add loading class to body to prevent interactions
        document.body.classList.add('loading');
    }
    
    function hideLoading() {
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
        
        document.body.classList.remove('loading');
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
        const existingNotifications = document.querySelectorAll('.toast-notification');
        existingNotifications.forEach(notification => notification.remove());
        
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
            'success': 'ri-check-circle-line',
            'error': 'ri-error-warning-line',
            'warning': 'ri-alert-line',
            'info': 'ri-information-line'
        };
        
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${iconClass[type] || iconClass.info} me-2 fs-5"></i>
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
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, type === 'error' ? 7000 : 5000);
    }
    
    // Close export menu when clicking outside
    document.addEventListener('click', function(e) {
        const exportDropdown = document.querySelector('.export-dropdown');
        const exportMenu = document.getElementById('exportMenu');
        
        if (exportDropdown && exportMenu && !exportDropdown.contains(e.target)) {
            exportMenu.classList.remove('show');
        }
    });
    
    // Auto-refresh functionality (optional)
    let autoRefreshInterval;
    let isAutoRefreshEnabled = false;
    
    function startAutoRefresh() {
        if (isAutoRefreshEnabled) return;
        
        isAutoRefreshEnabled = true;
        autoRefreshInterval = setInterval(() => {
            // Only refresh if no reports are selected and user is not actively searching
            if (selectedReports.size === 0 && !document.activeElement.matches('input, select, textarea')) {
                refreshReportList();
            }
        }, 30000); // Every 30 seconds
        
        console.log('Auto-refresh started');
    }
    
    function stopAutoRefresh() {
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
            isAutoRefreshEnabled = false;
            console.log('Auto-refresh stopped');
        }
    }
    
    function refreshReportList() {
        const url = new URL(window.location);
        url.searchParams.set('auto_refresh', '1');
        
        fetch(url.toString(), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Update stats
            const newStats = doc.querySelectorAll('.stat-value');
            const currentStats = document.querySelectorAll('.stat-value');
            newStats.forEach((stat, index) => {
                if (currentStats[index]) {
                    animateValueChange(currentStats[index], stat.textContent);
                }
            });
            
            // Update table content if needed
            const newTableBody = doc.querySelector('.table-enhanced tbody');
            const currentTableBody = document.querySelector('.table-enhanced tbody');
            
            if (newTableBody && currentTableBody && 
                newTableBody.innerHTML !== currentTableBody.innerHTML) {
                
                currentTableBody.innerHTML = newTableBody.innerHTML;
                initializeSelectAll(); // Re-initialize event listeners
                showNotification('Lista actualizada', 'info');
            }
        })
        .catch(error => {
            console.warn('Auto-refresh failed:', error);
        });
    }
    
    function animateValueChange(element, newValue) {
        if (element.textContent !== newValue) {
            element.style.transform = 'scale(1.1)';
            element.style.color = '#007bff';
            
            setTimeout(() => {
                element.textContent = newValue;
                element.style.transform = 'scale(1)';
                element.style.color = '';
            }, 200);
        }
    }
    
    // Page visibility change handling
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopAutoRefresh();
        } else {
            // Optionally restart auto-refresh when page becomes visible
            // startAutoRefresh();
        }
    });
    
    // Initialize auto-refresh (uncomment to enable)
    // startAutoRefresh();
    
    // Performance monitoring
    if (window.performance && window.performance.mark) {
        window.performance.mark('report-list-js-loaded');
        
        // Measure time to interactive
        setTimeout(() => {
            window.performance.mark('report-list-interactive');
            try {
                window.performance.measure(
                    'report-list-load-time',
                    'report-list-js-loaded',
                    'report-list-interactive'
                );
            } catch (e) {
                console.warn('Performance measurement failed:', e);
            }
        }, 100);
    }
    
    // Debug information (only in development)
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('Report List Debug Info:', {
            totalReports: reportCheckboxes.length,
            filtersApplied: {
                search: searchInput?.value || 'none',
                type: typeFilter?.value || 'none',
                status: statusFilter?.value || 'none',
                sort: sortFilter?.value || 'none'
            },
            selectedReports: selectedReports.size,
            autoRefresh: isAutoRefreshEnabled
        });
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        stopAutoRefresh();
        
        // Save current state
        const currentState = {
            selectedReports: Array.from(selectedReports),
            viewType: localStorage.getItem('reportListView'),
            lastUpdate: Date.now()
        };
        
        try {
            sessionStorage.setItem('reportListState', JSON.stringify(currentState));
        } catch (e) {
            console.warn('Could not save report list state:', e);
        }
    });
    
    // Restore state on page load
    function restoreState() {
        try {
            const savedState = sessionStorage.getItem('reportListState');
            if (savedState) {
                const state = JSON.parse(savedState);
                
                // Only restore if less than 5 minutes old
                if (Date.now() - state.lastUpdate < 5 * 60 * 1000) {
                    // Restore selected reports
                    if (state.selectedReports && state.selectedReports.length > 0) {
                        reportCheckboxes.forEach(checkbox => {
                            if (state.selectedReports.includes(checkbox.value)) {
                                checkbox.checked = true;
                                selectedReports.add(checkbox.value);
                            }
                        });
                        updateSelectAllState();
                        updateBulkActions();
                    }
                }
                
                // Clear old state
                sessionStorage.removeItem('reportListState');
            }
        } catch (e) {
            console.warn('Could not restore report list state:', e);
        }
    }
    
    // Initialize state restoration
    restoreState();
    
    console.log('Report list initialized successfully');
});