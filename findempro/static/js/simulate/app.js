/**
 * Main Application Controller
 * Punto de entrada principal que coordina todos los módulos
 */
class SimulationResultsApp {
    constructor() {
        this.modules = new Map();
        this.isInitialized = false;
        this.config = {
            tutorialEnabled: true,
            autoSave: true,
            animationsEnabled: true,
            notificationsEnabled: true
        };
        this.init();
    }

    async init() {
        try {
            console.log('🚀 Inicializando aplicación de resultados de simulación...');
            
            // Verificar dependencias
            await this.checkDependencies();
            
            // Inicializar módulos principales
            this.initializeModules();
            
            // Configurar la aplicación
            this.setupApplication();
            
            // Configurar eventos globales
            this.setupGlobalEvents();
            
            // Inicializar componentes UI
            this.initializeUI();
            
            // Marcar como inicializada
            this.isInitialized = true;
            
            console.log('✅ Aplicación inicializada correctamente');
            this.showWelcomeMessage();
            
        } catch (error) {
            console.error('❌ Error al inicializar la aplicación:', error);
            this.showErrorMessage('Error al cargar la aplicación. Por favor, recarga la página.');
        }
    }

    async checkDependencies() {
        const dependencies = [
            { name: 'jQuery', check: () => typeof $ !== 'undefined' },
            { name: 'Bootstrap', check: () => typeof bootstrap !== 'undefined' },
            { name: 'Chart.js', check: () => typeof Chart !== 'undefined' }
        ];

        const missing = dependencies.filter(dep => !dep.check());
        
        if (missing.length > 0) {
            throw new Error(`Dependencias faltantes: ${missing.map(d => d.name).join(', ')}`);
        }
        
        console.log('✅ Todas las dependencias están disponibles');
    }

    initializeModules() {
        // Registrar módulos principales
        this.modules.set('chartManager', window.chartManager);
        this.modules.set('paginationManager', window.paginationManager);
        this.modules.set('exportManager', window.exportManager);
        this.modules.set('validationCharts', window.validationCharts);
        this.modules.set('endogenousVariables', window.endogenousVariables);
        this.modules.set('statisticalAnalysis', window.statisticalAnalysis);
        
        console.log(`📦 ${this.modules.size} módulos registrados`);
    }

    setupApplication() {
        // Configurar configuraciones de usuario
        this.loadUserPreferences();
        
        // Configurar tutorial inicial
        this.setupTutorial();
        
        // Configurar auto-guardado
        if (this.config.autoSave) {
            this.setupAutoSave();
        }
        
        // Configurar tema
        this.setupTheme();
    }

    setupGlobalEvents() {
        // Evento de cambio de pestaña
        document.addEventListener('shown.bs.tab', (event) => {
            const tabId = event.target.getAttribute('aria-controls');
            this.onTabChanged(tabId);
        });

        // Evento de redimensionamiento de ventana
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.onWindowResize();
            }, 250);
        });

        // Evento de visibilidad de página
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.onPageHidden();
            } else {
                this.onPageVisible();
            }
        });

        // Eventos de teclado globales
        document.addEventListener('keydown', (e) => {
            this.handleGlobalKeydown(e);
        });

        // Evento antes de cerrar página
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = '¿Estás seguro de que quieres salir? Los cambios no guardados se perderán.';
            }
        });
    }

    initializeUI() {
        // Inicializar tooltips
        this.initializeTooltips();
        
        // Inicializar modales
        this.initializeModals();
        
        // Inicializar contadores animados
        this.initializeCounters();
        
        // Configurar navegación lateral
        this.setupSideNavigation();
        
        // Configurar búsqueda global
        this.setupGlobalSearch();
    }

    onTabChanged(tabId) {
        console.log(`🔄 Pestaña cambiada a: ${tabId}`);
        
        // Acciones específicas por pestaña
        switch(tabId) {
            case 'validation':
                this.modules.get('validationCharts')?.refreshCharts();
                break;
            case 'endogenous':
                this.modules.get('endogenousVariables')?.updateVariableCounts();
                break;
            case 'analysis':
                this.modules.get('statisticalAnalysis')?.refreshAnalysis();
                break;
        }
        
        // Tracking de analytics (si está configurado)
        this.trackTabView(tabId);
    }

    onWindowResize() {
        // Redimensionar gráficos
        const chartManager = this.modules.get('chartManager');
        if (chartManager && chartManager.charts) {
            chartManager.charts.forEach(chart => {
                if (chart && typeof chart.resize === 'function') {
                    chart.resize();
                }
            });
        }
        
        // Ajustar layout responsive
        this.adjustResponsiveLayout();
    }

    onPageHidden() {
        // Pausar animaciones y timers cuando la página no es visible
        this.pauseAnimations();
        this.pauseAutoRefresh();
    }

    onPageVisible() {
        // Reanudar cuando la página es visible
        this.resumeAnimations();
        this.resumeAutoRefresh();
    }

    handleGlobalKeydown(e) {
        // Atajos de teclado globales
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 's':
                    e.preventDefault();
                    this.quickSave();
                    break;
                case 'p':
                    e.preventDefault();
                    window.print();
                    break;
                case 'f':
                    e.preventDefault();
                    this.focusGlobalSearch();
                    break;
            }
        }
        
        // Navegación con teclas
        if (e.key === 'Escape') {
            this.closeAllModals();
        }
    }

    setupTutorial() {
        const tutorial = document.getElementById('resultsTutorial');
        
        if (tutorial && this.config.tutorialEnabled) {
            // Mostrar tutorial si es la primera visita
            if (!localStorage.getItem('tutorialCompleted')) {
                tutorial.style.display = 'block';
                this.highlightTutorialSteps();
            }
        }
        
        // Función global para cerrar tutorial
        window.hideTutorial = () => {
            if (tutorial) {
                tutorial.style.animation = 'fadeOut 0.5s ease-out';
                setTimeout(() => {
                    tutorial.style.display = 'none';
                    localStorage.setItem('tutorialCompleted', 'true');
                }, 500);
            }
        };
    }

    setupAutoSave() {
        // Configurar auto-guardado cada 5 minutos
        setInterval(() => {
            this.autoSave();
        }, 5 * 60 * 1000);
    }

    setupTheme() {
        // Cargar tema guardado o detectar preferencia del sistema
        const savedTheme = localStorage.getItem('theme');
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        const theme = savedTheme || systemTheme;
        
        this.applyTheme(theme);
        
        // Escuchar cambios en la preferencia del sistema
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                this.applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
    }

    initializeTooltips() {
        // Inicializar tooltips de Bootstrap si está disponible
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(tooltipTriggerEl => {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    initializeModals() {
        // Configurar comportamiento global de modales
        document.addEventListener('hidden.bs.modal', (event) => {
            // Limpiar backdrop si queda colgado
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => {
                if (backdrop.parentNode) {
                    backdrop.parentNode.removeChild(backdrop);
                }
            });
        });
    }

    initializeCounters() {
        // Inicializar contadores animados con Intersection Observer
        const counters = document.querySelectorAll('.counter');
        
        if (counters.length > 0) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !entry.target.classList.contains('animated')) {
                        this.animateCounter(entry.target);
                        entry.target.classList.add('animated');
                    }
                });
            });
            
            counters.forEach(counter => observer.observe(counter));
        }
    }

    animateCounter(element) {
        const target = parseFloat(element.getAttribute('data-target')) || 0;
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            
            // Formatear según el tipo de dato
            if (Number.isInteger(target)) {
                element.textContent = Math.floor(current).toLocaleString('es-ES');
            } else {
                element.textContent = current.toFixed(2);
            }
        }, 16);
    }

    setupSideNavigation() {
        // Configurar navegación lateral si existe
        const sideNav = document.getElementById('sideNavigation');
        if (sideNav) {
            // Hacer que la navegación sea sticky
            this.makeStickyNavigation(sideNav);
            
            // Resaltar sección activa
            this.setupActiveNavigation(sideNav);
        }
    }

    setupGlobalSearch() {
        // Configurar búsqueda global
        const searchInput = document.getElementById('globalSearch');
        if (searchInput) {
            let searchTimeout;
            
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performGlobalSearch(e.target.value);
                }, 300);
            });
        }
    }

    performGlobalSearch(query) {
        if (!query.trim()) {
            this.clearSearchResults();
            return;
        }
        
        const results = [];
        
        // Buscar en variables endógenas
        const endogenousRows = document.querySelectorAll('#endogenousTableBody tr[data-variable]');
        endogenousRows.forEach(row => {
            const variable = row.dataset.variable;
            const description = row.querySelector('small')?.textContent || '';
            
            if (variable.toLowerCase().includes(query.toLowerCase()) || 
                description.toLowerCase().includes(query.toLowerCase())) {
                results.push({
                    type: 'variable',
                    title: variable,
                    description: description,
                    element: row
                });
            }
        });
        
        // Buscar en resultados de validación
        const validationRows = document.querySelectorAll('#validationDetailTable tr');
        validationRows.forEach(row => {
            const day = row.querySelector('td:first-child')?.textContent;
            if (day && day.includes(query)) {
                results.push({
                    type: 'validation',
                    title: `Día ${day}`,
                    description: 'Resultado de validación',
                    element: row
                });
            }
        });
        
        this.displaySearchResults(results);
    }

    displaySearchResults(results) {
        let searchResults = document.getElementById('searchResults');
        
        if (!searchResults) {
            searchResults = document.createElement('div');
            searchResults.id = 'searchResults';
            searchResults.className = 'search-results-container';
            document.body.appendChild(searchResults);
        }
        
        if (results.length === 0) {
            searchResults.innerHTML = '<p class="no-results">No se encontraron resultados</p>';
            return;
        }
        
        const resultsHTML = results.map(result => `
            <div class="search-result-item" data-type="${result.type}">
                <h6>${result.title}</h6>
                <p>${result.description}</p>
            </div>
        `).join('');
        
        searchResults.innerHTML = resultsHTML;
        
        // Configurar clicks en resultados
        searchResults.querySelectorAll('.search-result-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.navigateToSearchResult(results[index]);
                this.clearSearchResults();
            });
        });
    }

    navigateToSearchResult(result) {
        if (result.type === 'variable') {
            // Cambiar a pestaña de variables endógenas y resaltar
            const tab = document.querySelector('[data-bs-target="#endogenous"]');
            if (tab) {
                tab.click();
                setTimeout(() => {
                    result.element.scrollIntoView({ behavior: 'smooth' });
                    result.element.classList.add('highlight');
                    setTimeout(() => result.element.classList.remove('highlight'), 2000);
                }, 300);
            }
        } else if (result.type === 'validation') {
            // Cambiar a pestaña de validación
            const tab = document.querySelector('[data-bs-target="#validation"]');
            if (tab) {
                tab.click();
                setTimeout(() => {
                    result.element.scrollIntoView({ behavior: 'smooth' });
                    result.element.classList.add('highlight');
                    setTimeout(() => result.element.classList.remove('highlight'), 2000);
                }, 300);
            }
        }
    }

    clearSearchResults() {
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.remove();
        }
    }

    // Utilidades
    loadUserPreferences() {
        const preferences = localStorage.getItem('userPreferences');
        if (preferences) {
            this.config = { ...this.config, ...JSON.parse(preferences) };
        }
    }

    saveUserPreferences() {
        localStorage.setItem('userPreferences', JSON.stringify(this.config));
    }

    quickSave() {
        // Implementar guardado rápido
        const data = this.collectCurrentState();
        localStorage.setItem('quickSave', JSON.stringify({
            timestamp: new Date().toISOString(),
            data: data
        }));
        
        this.showNotification('Estado guardado', 'success');
    }

    autoSave() {
        if (!document.hidden) {
            this.quickSave();
            console.log('🔄 Auto-guardado realizado');
        }
    }

    collectCurrentState() {
        return {
            activeTab: document.querySelector('.nav-link.active')?.getAttribute('aria-controls'),
            filters: this.collectAllFilters(),
            scroll: {
                x: window.scrollX,
                y: window.scrollY
            }
        };
    }

    collectAllFilters() {
        const filters = {};
        
        // Recopilar filtros de variables endógenas
        const endogenousSearch = document.getElementById('endogenousSearch');
        if (endogenousSearch) {
            filters.endogenousSearch = endogenousSearch.value;
        }
        
        return filters;
    }

    hasUnsavedChanges() {
        // Verificar si hay cambios no guardados
        return false; // Implementar según necesidades
    }

    trackTabView(tabId) {
        // Implementar tracking de analytics si es necesario
        console.log(`📊 Tab view: ${tabId}`);
    }

    adjustResponsiveLayout() {
        // Ajustar layout para diferentes tamaños de pantalla
        const isMobile = window.innerWidth < 768;
        document.body.classList.toggle('mobile-layout', isMobile);
    }

    pauseAnimations() {
        document.body.classList.add('animations-paused');
    }

    resumeAnimations() {
        document.body.classList.remove('animations-paused');
    }

    pauseAutoRefresh() {
        // Pausar actualizaciones automáticas
    }

    resumeAutoRefresh() {
        // Reanudar actualizaciones automáticas
    }

    focusGlobalSearch() {
        const searchInput = document.getElementById('globalSearch');
        if (searchInput) {
            searchInput.focus();
        }
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }

    showWelcomeMessage() {
        if (this.config.notificationsEnabled) {
            setTimeout(() => {
                this.showNotification('¡Bienvenido a los resultados de simulación!', 'info');
            }, 1000);
        }
    }

    showErrorMessage(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        if (this.modules.get('chartManager')) {
            this.modules.get('chartManager').showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    // Método para limpiar recursos al cerrar
    destroy() {
        console.log('🧹 Limpiando recursos de la aplicación...');
        
        this.modules.forEach((module, name) => {
            if (module && typeof module.destroy === 'function') {
                module.destroy();
                console.log(`✅ Módulo ${name} limpiado`);
            }
        });
        
        this.modules.clear();
        this.isInitialized = false;
    }
}

// Inicializar aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.simulationApp = new SimulationResultsApp();
});

// Limpiar recursos al cerrar la página
window.addEventListener('beforeunload', () => {
    if (window.simulationApp) {
        window.simulationApp.destroy();
    }
});