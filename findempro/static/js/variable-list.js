// Variable List JavaScript - Archivo separado

document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    const loadingOverlay = document.getElementById('loadingOverlay');
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmationModal'));
    const advancedModal = new bootstrap.Modal(document.getElementById('advancedFiltersModal'));
    
    // Función para mostrar/ocultar loading
    function showLoading(show = true) {
        if (loadingOverlay) {
            loadingOverlay.style.display = show ? 'flex' : 'none';
        }
    }
    
    // Funcionalidad de eliminación mejorada
    const deleteButtons = document.querySelectorAll('.delete-variable');
    const deleteForm = document.getElementById('deleteVariableForm');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const variableId = this.dataset.variableId;
            const variableName = this.dataset.variableName;
            const equationCount = parseInt(this.dataset.equationCount) || 0;
            
            // Configurar modal
            const deleteVariableNameEl = document.getElementById('deleteVariableName');
            if (deleteVariableNameEl) {
                deleteVariableNameEl.textContent = variableName;
            }
            
            if (deleteForm) {
                deleteForm.action = `/variable/delete/${variableId}/`;
            }
            
            // Análisis de impacto mejorado
            const impactDetails = document.getElementById('impactDetails');
            if (impactDetails) {
                let impactHtml = '';
                
                if (equationCount > 0) {
                    const riskLevel = equationCount > 5 ? 'alto' : equationCount > 2 ? 'medio' : 'bajo';
                    const riskClass = equationCount > 5 ? 'danger' : equationCount > 2 ? 'warning' : 'info';
                    
                    impactHtml = `
                        <div class="row g-3">
                            <div class="col-md-6">
                                <div class="d-flex align-items-center">
                                    <div class="avatar-sm bg-${riskClass}-subtle text-${riskClass} rounded me-3">
                                        <i class="ri-links-line fs-5"></i>
                                    </div>
                                    <div>
                                        <h6 class="mb-0">${equationCount}</h6>
                                        <small class="text-muted">Ecuaciones afectadas</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="d-flex align-items-center">
                                    <div class="avatar-sm bg-${riskClass}-subtle text-${riskClass} rounded me-3">
                                        <i class="ri-alert-triangle-line fs-5"></i>
                                    </div>
                                    <div>
                                        <h6 class="mb-0 text-capitalize">Riesgo ${riskLevel}</h6>
                                        <small class="text-muted">Nivel de impacto</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="mt-3 p-3 bg-${riskClass}-subtle rounded">
                            <p class="mb-0 small">
                                <strong>Consecuencias:</strong> La eliminación de esta variable afectará ${equationCount} ecuación(es) 
                                y puede causar errores en el modelo de simulación.
                            </p>
                        </div>
                    `;
                } else {
                    impactHtml = `
                        <div class="d-flex align-items-center">
                            <div class="avatar-sm bg-success-subtle text-success rounded me-3">
                                <i class="ri-check-line fs-5"></i>
                            </div>
                            <div>
                                <h6 class="mb-1">Sin dependencias directas</h6>
                                <p class="mb-0 small text-muted">
                                    Esta variable no tiene ecuaciones dependientes conocidas, pero puede estar 
                                    relacionada con otros elementos del sistema.
                                </p>
                            </div>
                        </div>
                    `;
                }
                
                impactDetails.innerHTML = impactHtml;
            }
            
            deleteModal.show();
        });
    });
    
    // Filtros inteligentes con debounce
    const filterInputs = document.querySelectorAll('#filterForm select, #filterForm input');
    let filterTimeout;
    
    filterInputs.forEach(input => {
        if (input.type === 'text') {
            input.addEventListener('input', function() {
                clearTimeout(filterTimeout);
                filterTimeout = setTimeout(() => {
                    showLoading();
                    document.getElementById('filterForm').submit();
                }, 800); // Aumentado para mejor UX
            });
        } else {
            input.addEventListener('change', function() {
                showLoading();
                document.getElementById('filterForm').submit();
            });
        }
    });
    
    // Limpiar búsqueda
    const clearSearchBtn = document.getElementById('clearSearch');
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.value = '';
                showLoading();
                document.getElementById('filterForm').submit();
            }
        });
    }
    
    // Funcionalidad de exportación mejorada
    const exportCSV = document.getElementById('exportCSV');
    const exportExcel = document.getElementById('exportExcel');
    const exportPDF = document.getElementById('exportPDF');
    
    if (exportCSV) {
        exportCSV.addEventListener('click', function(e) {
            e.preventDefault();
            exportData('csv');
        });
    }
    
    if (exportExcel) {
        exportExcel.addEventListener('click', function(e) {
            e.preventDefault();
            exportData('excel');
        });
    }
    
    if (exportPDF) {
        exportPDF.addEventListener('click', function(e) {
            e.preventDefault();
            exportData('pdf');
        });
    }
    
    function exportData(format) {
        showLoading();
        const params = new URLSearchParams(window.location.search);
        params.append('export', format);
        
        // Crear enlace temporal para descarga
        const link = document.createElement('a');
        link.href = `${window.location.pathname}?${params.toString()}`;
        link.download = `variables_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        setTimeout(() => showLoading(false), 1000);
    }
    
    // Filtros avanzados
    const btnAdvancedFilters = document.getElementById('btnAdvancedFilters');
    if (btnAdvancedFilters) {
        btnAdvancedFilters.addEventListener('click', function() {
            advancedModal.show();
        });
    }
    
    window.applyAdvancedFilters = function() {
        const form = document.getElementById('advancedFilterForm');
        if (form) {
            const formData = new FormData(form);
            const params = new URLSearchParams(window.location.search);
            
            for (let [key, value] of formData.entries()) {
                if (value) {
                    params.set(key, value);
                }
            }
            
            showLoading();
            window.location.href = `${window.location.pathname}?${params.toString()}`;
        }
    };
    
    // Duplicar variable
    window.duplicateVariable = function(variableId) {
        if (confirm('¿Desea duplicar esta variable?')) {
            showLoading();
            fetch(`/variable/duplicate/${variableId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Variable duplicada exitosamente', 'success');
                    setTimeout(() => {
                        window.location.href = `/variable/overview/${data.new_variable_id}/`;
                    }, 1500);
                } else {
                    throw new Error(data.error || 'Error al duplicar la variable');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('Error al duplicar: ' + error.message, 'error');
                showLoading(false);
            });
        }
    };
    
    // Función para obtener CSRF token
    function getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenElement ? tokenElement.value : '';
    }
    
    // Animaciones y efectos visuales
    const variableCards = document.querySelectorAll('.variable-card');
    
    // Intersection Observer para animaciones de entrada
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 100);
            }
        });
    }, { threshold: 0.1 });
    
    variableCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
    
    // Efecto de resaltado en búsqueda
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        const searchTerm = searchInput.value.toLowerCase();
        if (searchTerm) {
            variableCards.forEach(card => {
                const content = card.textContent.toLowerCase();
                if (content.includes(searchTerm)) {
                    const title = card.querySelector('.card-title a');
                    if (title && title.textContent) {
                        title.innerHTML = title.textContent.replace(
                            new RegExp(searchTerm, 'gi'),
                            '<span class="search-highlight">$&</span>'
                        );
                    }
                }
            });
        }
    }
    
    // Loading overlay en envío de formularios
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            showLoading();
        });
    });
    
    // Ocultar loading si la página se carga completamente
    window.addEventListener('load', function() {
        showLoading(false);
    });
    
    // Tooltips mejorados
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            animation: true,
            delay: { show: 300, hide: 100 }
        });
    });
    
    // Filtros responsivos
    const filterToggle = document.querySelector('.filter-toggle');
    if (filterToggle) {
        filterToggle.addEventListener('click', function() {
            const icon = this.querySelector('i');
            if (icon) {
                if (icon.classList.contains('ri-arrow-down-s-line')) {
                    icon.classList.replace('ri-arrow-down-s-line', 'ri-arrow-up-s-line');
                } else {
                    icon.classList.replace('ri-arrow-up-s-line', 'ri-arrow-down-s-line');
                }
            }
        });
    }
    
    // Función para mostrar notificaciones
    function showNotification(message, type = 'info') {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'info': 'alert-info',
            'warning': 'alert-warning'
        };
        
        const iconClass = {
            'success': 'ri-check-line',
            'error': 'ri-error-warning-line',
            'info': 'ri-information-line',
            'warning': 'ri-alert-line'
        };
        
        const notification = document.createElement('div');
        notification.className = `alert ${alertClass[type]} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 500px;';
        notification.innerHTML = `
            <i class="${iconClass[type]} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Función global para cargar detalles de variable (para edición)
    window.loadVariableDetails = function(variableId) {
        showLoading();
        
        fetch(`/variable/details/${variableId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Llenar campos del formulario si existe el modal
                const variableIdField = document.getElementById('variable-id-field');
                const nameField = document.getElementById('name');
                const productField = document.getElementById('fk_product');
                const typeField = document.getElementById('type');
                const unitField = document.getElementById('unit');
                const initialsField = document.getElementById('initials');
                const descriptionField = document.getElementById('description');
                const logoImg = document.getElementById('logo-img');
                
                if (variableIdField) variableIdField.value = variableId;
                if (nameField) nameField.value = data.name || '';
                if (productField) productField.value = data.fk_product || '';
                if (typeField) typeField.value = data.type || '';
                if (unitField) unitField.value = data.unit || '';
                if (initialsField) initialsField.value = data.initials || '';
                if (descriptionField) descriptionField.value = data.description || '';
                
                // Actualizar imagen si existe
                if (data.image_src && logoImg) {
                    logoImg.src = data.image_src;
                }
                
                // Actualizar título del modal
                const modalTitle = document.getElementById('addOrUpdateVariablelabel');
                const submitBtnText = document.getElementById('submit-btn-text');
                
                if (modalTitle) modalTitle.textContent = 'Editar Variable';
                if (submitBtnText) submitBtnText.textContent = 'Actualizar Variable';
                
                // Trigger eventos para actualizar UI si los campos existen
                if (typeField) typeField.dispatchEvent(new Event('change'));
                if (unitField) unitField.dispatchEvent(new Event('change'));
                if (nameField) nameField.dispatchEvent(new Event('input'));
                if (descriptionField) descriptionField.dispatchEvent(new Event('input'));
                
                showLoading(false);
            })
            .catch(error => {
                console.error('Error loading variable details:', error);
                showNotification('Error al cargar los detalles: ' + error.message, 'error');
                showLoading(false);
            });
    };
    
    // Funcionalidad de búsqueda en tiempo real mejorada
    const searchInputField = document.getElementById('search-input');
    if (searchInputField) {
        let searchTimeout;
        
        searchInputField.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            
            // Limpiar timeout anterior
            clearTimeout(searchTimeout);
            
            // Si hay término de búsqueda, filtrar en tiempo real
            if (searchTerm.length >= 2) {
                searchTimeout = setTimeout(() => {
                    filterCardsInRealTime(searchTerm);
                }, 300);
            } else if (searchTerm.length === 0) {
                // Mostrar todas las cards si no hay búsqueda
                showAllCards();
            }
        });
    }
    
    function filterCardsInRealTime(searchTerm) {
        const cards = document.querySelectorAll('.variable-card');
        let visibleCount = 0;
        
        cards.forEach(card => {
            const cardText = card.textContent.toLowerCase();
            const isMatch = cardText.includes(searchTerm);
            
            if (isMatch) {
                card.style.display = 'block';
                card.style.animation = 'fadeInUp 0.3s ease forwards';
                visibleCount++;
                
                // Resaltar términos encontrados
                highlightSearchTerms(card, searchTerm);
            } else {
                card.style.display = 'none';
            }
        });
        
        // Mostrar mensaje si no hay resultados
        updateSearchResults(visibleCount, searchTerm);
    }
    
    function showAllCards() {
        const cards = document.querySelectorAll('.variable-card');
        cards.forEach(card => {
            card.style.display = 'block';
            // Remover resaltados
            removeHighlights(card);
        });
        
        // Ocultar mensaje de "no resultados"
        const noResultsMsg = document.getElementById('noSearchResults');
        if (noResultsMsg) {
            noResultsMsg.remove();
        }
    }
    
    function highlightSearchTerms(card, searchTerm) {
        // Remover resaltados anteriores
        removeHighlights(card);
        
        const textElements = card.querySelectorAll('h5, p, span');
        textElements.forEach(element => {
            if (element.textContent.toLowerCase().includes(searchTerm)) {
                const regex = new RegExp(`(${searchTerm})`, 'gi');
                element.innerHTML = element.textContent.replace(regex, '<mark class="search-highlight">$1</mark>');
            }
        });
    }
    
    function removeHighlights(card) {
        const highlights = card.querySelectorAll('.search-highlight');
        highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });
    }
    
    function updateSearchResults(count, searchTerm) {
        const gridContainer = document.querySelector('.variable-grid');
        let noResultsMsg = document.getElementById('noSearchResults');
        
        if (count === 0) {
            if (!noResultsMsg) {
                noResultsMsg = document.createElement('div');
                noResultsMsg.id = 'noSearchResults';
                noResultsMsg.className = 'col-12';
                noResultsMsg.innerHTML = `
                    <div class="empty-state">
                        <lord-icon
                            src="https://cdn.lordicon.com/msoeawqm.json"
                            trigger="loop"
                            colors="primary:#ffffff,secondary:#ffffff"
                            style="width: 100px; height: 100px">
                        </lord-icon>
                        <h4 class="mt-3">No se encontraron resultados</h4>
                        <p class="mb-3">
                            No hay variables que coincidan con "<strong>${searchTerm}</strong>"
                            <br>Intente con otros términos de búsqueda.
                        </p>
                        <button class="btn btn-light" onclick="clearSearchAndShow()">
                            <i class="ri-refresh-line me-1"></i>
                            Limpiar búsqueda
                        </button>
                    </div>
                `;
                gridContainer.appendChild(noResultsMsg);
            }
        } else {
            if (noResultsMsg) {
                noResultsMsg.remove();
            }
        }
    }
    
    // Función global para limpiar búsqueda
    window.clearSearchAndShow = function() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.value = '';
            showAllCards();
        }
    };
    
    // Funcionalidad de ordenamiento en tiempo real
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const sortValue = this.value;
            sortCardsInRealTime(sortValue);
        });
    }
    
    function sortCardsInRealTime(sortValue) {
        const gridContainer = document.querySelector('.variable-grid');
        const cards = Array.from(document.querySelectorAll('.variable-card'));
        
        cards.sort((a, b) => {
            let aValue, bValue;
            
            switch(sortValue) {
                case 'name':
                    aValue = a.querySelector('.card-title a').textContent.toLowerCase();
                    bValue = b.querySelector('.card-title a').textContent.toLowerCase();
                    return aValue.localeCompare(bValue);
                    
                case '-name':
                    aValue = a.querySelector('.card-title a').textContent.toLowerCase();
                    bValue = b.querySelector('.card-title a').textContent.toLowerCase();
                    return bValue.localeCompare(aValue);
                    
                case 'type':
                    aValue = a.querySelector('.variable-type-icon').className;
                    bValue = b.querySelector('.variable-type-icon').className;
                    return aValue.localeCompare(bValue);
                    
                case '-type':
                    aValue = a.querySelector('.variable-type-icon').className;
                    bValue = b.querySelector('.variable-type-icon').className;
                    return bValue.localeCompare(aValue);
                    
                default: // Por fecha
                    aValue = a.dataset.variableId;
                    bValue = b.dataset.variableId;
                    if (sortValue === 'date_created') {
                        return parseInt(aValue) - parseInt(bValue);
                    } else {
                        return parseInt(bValue) - parseInt(aValue);
                    }
            }
        });
        
        // Remover todas las cards y volver a insertarlas ordenadas
        cards.forEach(card => card.remove());
        cards.forEach(card => gridContainer.appendChild(card));
        
        // Re-aplicar animaciones
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            setTimeout(() => {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 50);
        });
    }
    
    // Funcionalidad de filtro por tipo visual
    const typeButtons = document.querySelectorAll('[data-type-filter]');
    typeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const typeFilter = this.dataset.typeFilter;
            filterByType(typeFilter);
            
            // Actualizar botones activos
            typeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    function filterByType(typeFilter) {
        const cards = document.querySelectorAll('.variable-card');
        
        cards.forEach(card => {
            if (typeFilter === 'all') {
                card.style.display = 'block';
            } else {
                const cardType = card.querySelector('.variable-type-icon').classList;
                const hasType = cardType.contains(typeFilter);
                card.style.display = hasType ? 'block' : 'none';
            }
        });
    }
    
    // Funcionalidad de vista en lista vs grid
    const viewToggleButtons = document.querySelectorAll('[data-view-mode]');
    viewToggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const viewMode = this.dataset.viewMode;
            toggleViewMode(viewMode);
            
            // Actualizar botones activos
            viewToggleButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    function toggleViewMode(mode) {
        const gridContainer = document.querySelector('.variable-grid');
        
        if (mode === 'list') {
            gridContainer.classList.add('list-view');
            gridContainer.style.gridTemplateColumns = '1fr';
        } else {
            gridContainer.classList.remove('list-view');
            gridContainer.style.gridTemplateColumns = 'repeat(auto-fill, minmax(350px, 1fr))';
        }
    }
    
    // Funcionalidad de selección múltiple
    let selectedCards = new Set();
    
    const selectAllBtn = document.getElementById('selectAll');
    const bulkActionsBtn = document.getElementById('bulkActions');
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            const cards = document.querySelectorAll('.variable-card');
            const isSelectingAll = selectedCards.size === 0;
            
            cards.forEach(card => {
                if (isSelectingAll) {
                    selectCard(card);
                } else {
                    deselectCard(card);
                }
            });
            
            updateBulkActionsVisibility();
        });
    }
    
    function selectCard(card) {
        const variableId = card.dataset.variableId;
        selectedCards.add(variableId);
        card.classList.add('selected');
        
        // Agregar checkbox visual
        if (!card.querySelector('.selection-checkbox')) {
            const checkbox = document.createElement('div');
            checkbox.className = 'selection-checkbox position-absolute top-0 start-0 m-2';
            checkbox.innerHTML = '<i class="ri-check-line text-white bg-primary rounded-circle p-1"></i>';
            card.appendChild(checkbox);
        }
    }
    
    function deselectCard(card) {
        const variableId = card.dataset.variableId;
        selectedCards.delete(variableId);
        card.classList.remove('selected');
        
        // Remover checkbox visual
        const checkbox = card.querySelector('.selection-checkbox');
        if (checkbox) {
            checkbox.remove();
        }
    }
    
    function updateBulkActionsVisibility() {
        if (bulkActionsBtn) {
            bulkActionsBtn.style.display = selectedCards.size > 0 ? 'block' : 'none';
        }
    }
    
    // Funcionalidad de acciones masivas
    window.bulkDelete = function() {
        if (selectedCards.size === 0) return;
        
        if (confirm(`¿Está seguro de eliminar ${selectedCards.size} variable(s) seleccionada(s)?`)) {
            showLoading();
            
            const promises = Array.from(selectedCards).map(variableId => {
                return fetch(`/variable/delete/${variableId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFToken(),
                        'Content-Type': 'application/json',
                    }
                });
            });
            
            Promise.all(promises)
                .then(() => {
                    showNotification(`${selectedCards.size} variable(s) eliminada(s) exitosamente`, 'success');
                    setTimeout(() => location.reload(), 1000);
                })
                .catch(error => {
                    showNotification('Error en la eliminación masiva', 'error');
                    showLoading(false);
                });
        }
    };
    
    window.bulkExport = function() {
        if (selectedCards.size === 0) return;
        
        const variableIds = Array.from(selectedCards).join(',');
        const link = document.createElement('a');
        link.href = `/variable/export/?ids=${variableIds}&format=csv`;
        link.download = `variables_selected_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification(`Exportando ${selectedCards.size} variable(s)`, 'info');
    };
    
    // Funcionalidad de teclado
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + F para enfocar búsqueda
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape para limpiar búsqueda
        if (e.key === 'Escape') {
            const searchInput = document.getElementById('search-input');
            if (searchInput && searchInput.value) {
                searchInput.value = '';
                showAllCards();
            }
        }
    });
    
    // Inicialización final
    console.log('Variable List JavaScript loaded successfully');
    
    // Verificar si hay elementos necesarios
    if (!loadingOverlay) {
        console.warn('Loading overlay not found');
    }
    
    if (variableCards.length === 0) {
        console.info('No variable cards found on page');
    }
    
    // Ocultar loading inicial
    showLoading(false);
});