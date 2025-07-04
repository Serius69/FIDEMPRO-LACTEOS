/**
 * Pagination Manager - Manejo de paginación para diferentes secciones
 */
class PaginationManager {
    constructor() {
        this.currentPages = new Map();
        this.init();
    }

    init() {
        this.initializeDailyResultsPagination();
        this.initializeTablePagination();
        this.initializeEndogenousTablePagination();
        this.setupKeyboardNavigation();
    }

    initializeDailyResultsPagination() {
        const totalDays = parseInt(document.querySelector('[data-total-days]')?.dataset.totalDays) || 
                          document.querySelectorAll('.daily-result-item').length;
        
        if (totalDays === 0) return;

        let currentDay = 1;
        this.currentPages.set('dailyResults', currentDay);
        
        const prevBtn = document.getElementById('prevDayBtn');
        const nextBtn = document.getElementById('nextDayBtn');
        const dayCounter = document.getElementById('dayCounter');
        const currentDayIndicator = document.getElementById('currentDayIndicator');
        
        const updateDayDisplay = () => {
            // Ocultar todos los items
            document.querySelectorAll('.daily-result-item').forEach(item => {
                item.style.display = 'none';
            });
            
            // Mostrar el item del día actual con animación
            const currentItem = document.querySelector(`[data-day="${currentDay}"]`);
            if (currentItem) {
                currentItem.style.display = 'block';
                currentItem.style.animation = 'fadeIn 0.3s ease';
            }
            
            // Actualizar indicadores
            if (currentDayIndicator) {
                currentDayIndicator.textContent = `Día ${currentDay}`;
            }
            if (dayCounter) {
                dayCounter.textContent = `Día ${currentDay} de ${totalDays}`;
            }
            
            // Actualizar estado de botones
            if (prevBtn) {
                prevBtn.disabled = currentDay <= 1;
                prevBtn.classList.toggle('btn-outline-secondary', currentDay === 1);
                prevBtn.classList.toggle('btn-outline-primary', currentDay > 1);
            }
            if (nextBtn) {
                nextBtn.disabled = currentDay >= totalDays;
                nextBtn.classList.toggle('btn-outline-secondary', currentDay === totalDays);
                nextBtn.classList.toggle('btn-outline-primary', currentDay < totalDays);
            }
            
            // Scroll to top
            const cardBody = document.querySelector('.card-body');
            if (cardBody) {
                cardBody.scrollTop = 0;
            }
            
            this.currentPages.set('dailyResults', currentDay);
        };
        
        // Event listeners
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (currentDay > 1) {
                    currentDay--;
                    updateDayDisplay();
                }
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (currentDay < totalDays) {
                    currentDay++;
                    updateDayDisplay();
                }
            });
        }
        
        // Inicializar vista
        updateDayDisplay();
    }

    initializeTablePagination() {
        const table = document.getElementById('demandTable');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const itemsPerPage = 10;
        const totalPages = Math.ceil(rows.length / itemsPerPage);
        let currentPage = 1;
        
        const prevBtn = document.getElementById('prevTablePage');
        const nextBtn = document.getElementById('nextTablePage');
        const pageInfo = document.getElementById('tablePageInfo');
        
        const updateTableDisplay = () => {
            // Ocultar todas las filas
            rows.forEach(row => row.style.display = 'none');
            
            // Mostrar filas de la página actual
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = Math.min(startIndex + itemsPerPage, rows.length);
            
            for (let i = startIndex; i < endIndex; i++) {
                if (rows[i]) {
                    rows[i].style.display = 'table-row';
                    rows[i].style.animation = 'fadeIn 0.2s ease';
                }
            }
            
            // Actualizar información de página
            if (pageInfo) {
                pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;
            }
            
            // Actualizar estado de botones
            if (prevBtn) {
                prevBtn.disabled = currentPage === 1;
            }
            if (nextBtn) {
                nextBtn.disabled = currentPage === totalPages;
            }
            
            this.currentPages.set('demandTable', currentPage);
        };
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (currentPage > 1) {
                    currentPage--;
                    updateTableDisplay();
                }
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (currentPage < totalPages) {
                    currentPage++;
                    updateTableDisplay();
                }
            });
        }
        
        // Inicializar vista
        updateTableDisplay();
    }

    initializeEndogenousTablePagination() {
        const table = document.getElementById('endogenousTable');
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr[data-variable]'));
        const itemsPerPage = 15;
        const totalPages = Math.ceil(rows.length / itemsPerPage);
        let currentPage = 1;
        
        // Crear función global para compatibilidad
        window.paginateEndogenousTable = (direction) => {
            if (direction === 'prev' && currentPage > 1) {
                currentPage--;
            } else if (direction === 'next' && currentPage < totalPages) {
                currentPage++;
            }
            
            // Ocultar todas las filas
            rows.forEach(row => row.style.display = 'none');
            
            // Mostrar filas de la página actual
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = Math.min(startIndex + itemsPerPage, rows.length);
            
            for (let i = startIndex; i < endIndex; i++) {
                if (rows[i]) {
                    rows[i].style.display = 'table-row';
                    rows[i].style.animation = 'fadeIn 0.2s ease';
                }
            }
            
            // Actualizar información de página
            const pageInfo = document.getElementById('endogenousPageInfo');
            if (pageInfo) {
                pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;
            }
            
            // Actualizar estado de botones
            const prevBtn = document.querySelector('[onclick="paginateEndogenousTable(\'prev\')"]');
            const nextBtn = document.querySelector('[onclick="paginateEndogenousTable(\'next\')"]');
            
            if (prevBtn) {
                prevBtn.parentElement.classList.toggle('disabled', currentPage === 1);
            }
            if (nextBtn) {
                nextBtn.parentElement.classList.toggle('disabled', currentPage === totalPages);
            }
            
            this.currentPages.set('endogenousTable', currentPage);
        };
        
        // Inicializar primera página
        window.paginateEndogenousTable('init');
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Solo procesar si no estamos en un input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            if (e.ctrlKey || e.metaKey) {
                const currentDay = this.currentPages.get('dailyResults') || 1;
                const totalDays = document.querySelectorAll('.daily-result-item').length;
                
                if (e.key === 'ArrowLeft' && currentDay > 1) {
                    e.preventDefault();
                    document.getElementById('prevDayBtn')?.click();
                } else if (e.key === 'ArrowRight' && currentDay < totalDays) {
                    e.preventDefault();
                    document.getElementById('nextDayBtn')?.click();
                }
            }
        });
    }

    // Función para filtrar tablas
    filterTable(tableId, searchValue, filters = {}) {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        const tbody = table.querySelector('tbody');
        const rows = tbody.querySelectorAll('tr[data-variable], tr[data-category]');
        
        rows.forEach(row => {
            let shouldShow = true;
            
            // Filtro de búsqueda
            if (searchValue) {
                const searchText = row.textContent.toLowerCase();
                shouldShow = shouldShow && searchText.includes(searchValue.toLowerCase());
            }
            
            // Filtros adicionales
            Object.entries(filters).forEach(([filterKey, filterValue]) => {
                if (filterValue && row.dataset[filterKey]) {
                    shouldShow = shouldShow && row.dataset[filterKey] === filterValue;
                }
            });
            
            row.style.display = shouldShow ? '' : 'none';
        });
        
        // Actualizar contadores si es necesario
        this.updateFilteredCounts(tableId);
    }

    updateFilteredCounts(tableId) {
        if (tableId === 'endogenousTable') {
            const visibleRows = document.querySelectorAll('#endogenousTableBody tr[data-category]:not([style*="display: none"])');
            let financial = 0, operational = 0, quality = 0;
            
            visibleRows.forEach(row => {
                const category = row.dataset.category;
                if (category === 'financial') financial++;
                else if (category === 'operational') operational++;
                else if (category === 'quality') quality++;
            });
            
            // Actualizar contadores en UI
            const financialCount = document.getElementById('financialVarsCount');
            const operationalCount = document.getElementById('operationalVarsCount');
            const qualityCount = document.getElementById('qualityVarsCount');
            
            if (financialCount) financialCount.textContent = financial;
            if (operationalCount) operationalCount.textContent = operational;
            if (qualityCount) qualityCount.textContent = quality;
        }
    }

    // Función para obtener página actual
    getCurrentPage(section) {
        return this.currentPages.get(section) || 1;
    }

    // Función para ir a página específica
    goToPage(section, pageNumber) {
        // Implementar navegación directa a página
        console.log(`Navigating to page ${pageNumber} in section ${section}`);
    }
}

// Exportar instancia global
window.paginationManager = new PaginationManager();