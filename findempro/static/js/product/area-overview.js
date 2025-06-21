/**
 * Area Overview JavaScript Module
 * Handles tutorial system, graph visualization, and user interactions
 */

class AreaOverviewManager {
    constructor() {
        this.tutorialSteps = [
            {
                title: "Bienvenido al Área",
                content: "Esta es la vista detallada del área. Aquí puede gestionar las ecuaciones y ver las relaciones entre variables.",
                element: null
            },
            {
                title: "Estadísticas del Área",
                content: "Estos indicadores muestran el número de ecuaciones, variables y relaciones en el área.",
                element: ".stats-grid"
            },
            {
                title: "Gestión de Ecuaciones",
                content: "En esta sección puede crear, editar y eliminar ecuaciones. Las ecuaciones definen cómo se relacionan las variables.",
                element: "#equationsContainer"
            },
            {
                title: "Gráfico de Variables",
                content: "La pestaña 'Gráfico de Variables' muestra visualmente cómo están conectadas todas las variables a través de las ecuaciones.",
                element: ".nav-tabs-custom"
            }
        ];
        
        this.currentStep = 0;
        this.tutorialActive = false;
        this.graphInitialized = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeGraph();
        this.updateCounts();
        this.checkAutoTutorial();
    }

    setupEventListeners() {
        // Tutorial events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.tutorialActive) {
                this.endTutorial();
            }
        });

        // Tutorial overlay click
        const overlay = document.getElementById('tutorialOverlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.endTutorial();
                }
            });
        }

        // Graph tab activation
        const graphTab = document.querySelector('a[href="#area-variables"]');
        if (graphTab) {
            graphTab.addEventListener('shown.bs.tab', () => {
                if (!this.graphInitialized) {
                    this.initializeGraph();
                }
            });
        }

        // Equation card animations
        this.setupCardAnimations();
    }

    setupCardAnimations() {
        const cards = document.querySelectorAll('.equation-card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('fade-in');
        });
    }

    // Tutorial System
    startTutorial() {
        if (localStorage.getItem('areaOverviewTutorialCompleted') === 'true') {
            if (!confirm('¿Desea ver el tutorial nuevamente?')) {
                return;
            }
        }
        
        this.tutorialActive = true;
        this.currentStep = 0;
        
        const overlay = document.getElementById('tutorialOverlay');
        const popup = document.getElementById('tutorialPopup');
        
        if (overlay && popup) {
            overlay.style.display = 'block';
            popup.style.display = 'block';
            this.showStep(this.currentStep);
        }
    }

    showStep(step) {
        if (step >= this.tutorialSteps.length) {
            this.endTutorial();
            return;
        }

        const popup = document.getElementById('tutorialPopup');
        const title = document.getElementById('tutorialTitle');
        const content = document.getElementById('tutorialContent');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        
        if (!popup || !title || !content || !prevBtn || !nextBtn) {
            console.error('Tutorial elements not found');
            return;
        }

        // Remove previous highlights
        document.querySelectorAll('.highlight-element').forEach(el => {
            el.classList.remove('highlight-element');
        });
        
        const stepData = this.tutorialSteps[step];
        
        // Update content
        title.textContent = stepData.title;
        content.textContent = stepData.content;
        
        // Highlight element if specified
        if (stepData.element) {
            const element = document.querySelector(stepData.element);
            if (element) {
                element.classList.add('highlight-element');
                this.positionTooltip(popup, element);
            }
        } else {
            // Center popup
            this.centerPopup(popup);
        }
        
        // Update buttons
        prevBtn.style.display = step === 0 ? 'none' : 'inline-block';
        nextBtn.textContent = step === this.tutorialSteps.length - 1 ? 'Finalizar' : 'Siguiente';
    }

    positionTooltip(popup, targetElement) {
        const rect = targetElement.getBoundingClientRect();
        
        // Wait for popup to be rendered
        setTimeout(() => {
            const popupRect = popup.getBoundingClientRect();
            
            // Position popup
            if (rect.top > window.innerHeight / 2) {
                popup.style.top = (rect.top + window.scrollY - popupRect.height - 10) + 'px';
            } else {
                popup.style.top = (rect.bottom + window.scrollY + 10) + 'px';
            }
            
            const leftPosition = Math.max(10, Math.min(
                rect.left + (rect.width / 2) - (popupRect.width / 2),
                window.innerWidth - popupRect.width - 10
            ));
            
            popup.style.left = leftPosition + 'px';
            popup.style.transform = 'none';
        }, 10);
    }

    centerPopup(popup) {
        popup.style.top = '50%';
        popup.style.left = '50%';
        popup.style.transform = 'translate(-50%, -50%)';
    }

    nextStep() {
        if (this.currentStep < this.tutorialSteps.length - 1) {
            this.currentStep++;
            this.showStep(this.currentStep);
        } else {
            this.endTutorial();
        }
    }

    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }

    skipTutorial() {
        this.endTutorial();
    }

    endTutorial() {
        this.tutorialActive = false;
        
        const overlay = document.getElementById('tutorialOverlay');
        const popup = document.getElementById('tutorialPopup');
        
        if (overlay) overlay.style.display = 'none';
        if (popup) popup.style.display = 'none';
        
        // Remove highlights
        document.querySelectorAll('.highlight-element').forEach(el => {
            el.classList.remove('highlight-element');
        });
        
        localStorage.setItem('areaOverviewTutorialCompleted', 'true');
    }

    checkAutoTutorial() {
        if (localStorage.getItem('areaOverviewTutorialCompleted') !== 'true') {
            setTimeout(() => {
                this.startTutorial();
            }, 1000);
        }
    }

    // Graph Visualization
    initializeGraph() {
        const graphContainer = document.getElementById('variablesGraph');
        if (!graphContainer || this.graphInitialized) return;

        const data = window.areaOverviewData?.graphData;
        if (!data || (!data.variables.length && !data.equations.length)) {
            this.showEmptyGraphState(graphContainer);
            return;
        }

        this.createVariablesGraph(graphContainer, data);
        this.graphInitialized = true;
    }

    showEmptyGraphState(container) {
        container.innerHTML = `
            <div class="text-center py-5">
                <lord-icon src="https://cdn.lordicon.com/msoeawqm.json" 
                          trigger="loop" 
                          colors="primary:#405189,secondary:#0ab39c" 
                          style="width:100px;height:100px">
                </lord-icon>
                <h5 class="mt-3">No hay variables para mostrar</h5>
                <p class="text-muted">Las variables aparecerán aquí cuando agregues ecuaciones con variables asociadas.</p>
            </div>
        `;
    }

    createVariablesGraph(container, data) {
        // Clear existing content
        d3.select(container).selectAll("*").remove();
        
        const svg = d3.select(container)
            .append("svg")
            .attr("width", "100%")
            .attr("height", "500px");
        
        const width = container.offsetWidth;
        const height = 500;
        
        // Create nodes for variables and equations
        const nodes = [
            ...data.variables.map(variable => ({
                id: `var_${variable.id}`,
                name: variable.name || 'Sin nombre',
                type: 'variable',
                description: variable.description || 'Sin descripción'
            })),
            ...data.equations.map(equation => ({
                id: `eq_${equation.id}`,
                name: equation.name || 'Sin nombre',
                type: 'equation',
                expression: equation.expression || 'Sin expresión'
            }))
        ];
        
        // Create links between variables and equations
        const links = [];
        data.equations.forEach(equation => {
            if (equation.variables && Array.isArray(equation.variables)) {
                equation.variables.forEach(variableId => {
                    links.push({
                        source: `var_${variableId}`,
                        target: `eq_${equation.id}`
                    });
                });
            }
        });
        
        // Setup force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(30));
        
        // Create links
        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .enter()
            .append("line")
            .attr("stroke", "#999")
            .attr("stroke-width", 2)
            .attr("stroke-opacity", 0.6);
        
        // Create nodes
        const node = svg.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter()
            .append("circle")
            .attr("r", d => d.type === 'equation' ? 25 : 20)
            .attr("fill", d => d.type === 'variable' ? "#4facfe" : "#ffd700")
            .attr("stroke", "#fff")
            .attr("stroke-width", 2)
            .style("cursor", "pointer")
            .call(this.createDragBehavior(simulation));
        
        // Add labels
        const labels = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .enter()
            .append("text")
            .text(d => d.name)
            .attr("font-size", "12px")
            .attr("text-anchor", "middle")
            .attr("dy", d => d.type === 'equation' ? 35 : 30)
            .attr("fill", "#374151")
            .style("pointer-events", "none");
        
        // Add tooltips
        node.append("title")
            .text(d => d.type === 'variable' ? d.description : d.expression);
        
        // Update positions on each tick
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => Math.max(20, Math.min(width - 20, d.x)))
                .attr("cy", d => Math.max(20, Math.min(height - 20, d.y)));
            
            labels
                .attr("x", d => Math.max(20, Math.min(width - 20, d.x)))
                .attr("y", d => Math.max(20, Math.min(height - 20, d.y)));
        });

        // Store simulation for reset functionality
        this.simulation = simulation;
    }

    createDragBehavior(simulation) {
        return d3.drag()
            .on("start", (event, d) => {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on("drag", (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on("end", (event, d) => {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    resetGraph() {
        if (this.simulation) {
            this.simulation.alpha(1).restart();
        } else {
            // Reinitialize graph
            this.graphInitialized = false;
            this.initializeGraph();
        }
    }

    downloadGraph() {
        const svg = document.querySelector("#variablesGraph svg");
        if (!svg) {
            console.warn('No graph found to download');
            return;
        }

        try {
            const serializer = new XMLSerializer();
            const svgString = serializer.serializeToString(svg);
            const blob = new Blob([svgString], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = 'area_variables_graph.svg';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error downloading graph:', error);
            alert('Error al descargar el gráfico');
        }
    }

    // Utility Functions
    updateCounts() {
        const data = window.areaOverviewData;
        if (!data) return;

        // Update any dynamic count displays if needed
        const variableCountElements = document.querySelectorAll('[data-count="variables"]');
        const relationCountElements = document.querySelectorAll('[data-count="relations"]');
        
        variableCountElements.forEach(el => {
            el.textContent = data.totalVariables || 0;
        });
        
        relationCountElements.forEach(el => {
            el.textContent = data.totalRelations || 0;
        });
    }

    // Export Functions
    printArea() {
        const printContent = document.querySelector('.main-content');
        if (!printContent) return;

        const printWindow = window.open('', '', 'width=800,height=600');
        if (!printWindow) {
            alert('No se pudo abrir la ventana de impresión');
            return;
        }

        printWindow.document.write(`
            <html>
                <head>
                    <title>Imprimir Área</title>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        .tutorial-overlay, .tutorial-popup, .help-fab, .quick-actions { display: none !important; }
                        .card { border: 1px solid #e5e7eb; margin-bottom: 20px; }
                        .stat-card { background: #f3f4f6 !important; color: #374151 !important; }
                    </style>
                </head>
                <body>
                    ${printContent.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    exportData() {
        const equations = Array.from(document.querySelectorAll('.equation-card')).map(card => {
            const titleEl = card.querySelector('.equation-name');
            const expressionEl = card.querySelector('.equation-expression');
            const variableEls = card.querySelectorAll('.variable-tag');
            
            return {
                title: titleEl ? titleEl.textContent.trim() : 'Sin título',
                expression: expressionEl ? expressionEl.textContent.trim() : 'Sin expresión',
                variables: Array.from(variableEls).map(el => el.textContent.trim())
            };
        });
        
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Título,Ecuación,Variables\n";
        equations.forEach(eq => {
            csvContent += `"${eq.title}","${eq.expression}","${eq.variables.join(';')}"\n`;
        });
        
        try {
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "area_equations.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error exporting data:', error);
            alert('Error al exportar los datos');
        }
    }

    // Equation Management
    loadEquationDetails(equationId) {
        if (!equationId) {
            console.error('No equation ID provided');
            return;
        }

        fetch(`/equation/get_details/${equationId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                this.populateEquationModal(data);
            })
            .catch(error => {
                console.error('Error loading equation details:', error);
                if (window.Swal) {
                    Swal.fire({
                        title: 'Error',
                        text: 'No se pudieron cargar los detalles de la ecuación',
                        icon: 'error',
                        confirmButtonText: 'OK'
                    });
                } else {
                    alert('Error al cargar los detalles de la ecuación');
                }
            });
    }

    populateEquationModal(data) {
        // Fill modal with equation data
        const nameField = document.getElementById('equationName');
        const expressionField = document.getElementById('equationExpression');
        
        if (nameField) nameField.value = data.name || '';
        if (expressionField) expressionField.value = data.expression || '';
        
        // Load associated variables
        if (data.variables) {
            this.loadVariablesIntoModal(data.variables);
        }
    }

    loadVariablesIntoModal(variables) {
        const variableList = document.getElementById('variableList');
        if (!variableList) return;

        variableList.innerHTML = '';
        
        if (!variables || !Array.isArray(variables)) {
            variableList.innerHTML = '<li class="list-group-item text-muted">Sin variables asociadas</li>';
            return;
        }

        variables.forEach(variable => {
            const li = document.createElement('li');
            li.textContent = variable.name || 'Variable sin nombre';
            li.className = 'list-group-item';
            variableList.appendChild(li);
        });
    }

    // Animation and Visual Effects
    animateStatCards() {
        const cards = document.querySelectorAll('.stat-card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('slide-up');
            }, index * 100);
        });
    }

    // Error Handling
    handleError(error, userMessage) {
        console.error('AreaOverviewManager Error:', error);
        
        if (window.Swal) {
            Swal.fire({
                title: 'Error',
                text: userMessage || 'Ha ocurrido un error inesperado',
                icon: 'error',
                confirmButtonText: 'OK'
            });
        } else {
            alert(userMessage || 'Ha ocurrido un error inesperado');
        }
    }

    // Cleanup
    destroy() {
        if (this.simulation) {
            this.simulation.stop();
        }
        
        // Remove event listeners
        document.removeEventListener('keydown', this.handleKeydown);
    }
}

// Global Functions (for backward compatibility and external calls)
let areaOverviewManager;

function startTutorial() {
    if (areaOverviewManager) {
        areaOverviewManager.startTutorial();
    }
}

function nextStep() {
    if (areaOverviewManager) {
        areaOverviewManager.nextStep();
    }
}

function previousStep() {
    if (areaOverviewManager) {
        areaOverviewManager.previousStep();
    }
}

function skipTutorial() {
    if (areaOverviewManager) {
        areaOverviewManager.skipTutorial();
    }
}

function endTutorial() {
    if (areaOverviewManager) {
        areaOverviewManager.endTutorial();
    }
}

function resetGraph() {
    if (areaOverviewManager) {
        areaOverviewManager.resetGraph();
    }
}

function downloadGraph() {
    if (areaOverviewManager) {
        areaOverviewManager.downloadGraph();
    }
}

function printArea() {
    if (areaOverviewManager) {
        areaOverviewManager.printArea();
    }
}

function exportData() {
    if (areaOverviewManager) {
        areaOverviewManager.exportData();
    }
}

function loadEquationDetails(equationId) {
    if (areaOverviewManager) {
        areaOverviewManager.loadEquationDetails(equationId);
    }
}

// Utility Functions
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

function throttle(func, limit) {
    let lastFunc;
    let lastRan;
    return function(...args) {
        if (!lastRan) {
            func(...args);
            lastRan = Date.now();
        } else {
            clearTimeout(lastFunc);
            lastFunc = setTimeout(() => {
                if ((Date.now() - lastRan) >= limit) {
                    func(...args);
                    lastRan = Date.now();
                }
            }, limit - (Date.now() - lastRan));
        }
    };
}

// Performance optimized scroll handler
const handleScroll = throttle(() => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const helpFab = document.querySelector('.help-fab');
    
    if (helpFab) {
        if (scrollTop > 200) {
            helpFab.style.transform = 'scale(0.9)';
        } else {
            helpFab.style.transform = 'scale(1)';
        }
    }
}, 100);

// Intersection Observer for animations
const observeAnimations = () => {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements that should animate on scroll
    document.querySelectorAll('.equation-card, .stat-card').forEach(el => {
        observer.observe(el);
    });
};

// Local Storage Management
const LocalStorageManager = {
    get: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    },

    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error writing to localStorage:', error);
            return false;
        }
    },

    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    }
};

// Enhanced Error Handling
class ErrorHandler {
    static handle(error, context = 'Unknown') {
        console.error(`[${context}] Error:`, error);
        
        // Log to external service if available
        if (window.errorReportingService) {
            window.errorReportingService.log(error, context);
        }
        
        // Show user-friendly message
        const userMessage = this.getUserFriendlyMessage(error);
        this.showUserNotification(userMessage);
    }

    static getUserFriendlyMessage(error) {
        if (error.name === 'NetworkError' || error.message.includes('fetch')) {
            return 'Error de conexión. Por favor, verifique su conexión a internet.';
        }
        
        if (error.status === 404) {
            return 'El recurso solicitado no fue encontrado.';
        }
        
        if (error.status >= 500) {
            return 'Error del servidor. Por favor, intente nuevamente más tarde.';
        }
        
        return 'Ha ocurrido un error inesperado. Por favor, intente nuevamente.';
    }

    static showUserNotification(message) {
        if (window.Swal) {
            Swal.fire({
                title: 'Error',
                text: message,
                icon: 'error',
                confirmButtonText: 'OK',
                toast: true,
                position: 'top-end',
                timer: 5000,
                timerProgressBar: true
            });
        } else {
            // Fallback notification
            const notification = document.createElement('div');
            notification.className = 'alert alert-danger alert-dismissible fade show position-fixed';
            notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }
    }
}

// Accessibility Enhancements
const AccessibilityManager = {
    init() {
        this.setupKeyboardNavigation();
        this.setupAriaLabels();
        this.setupFocusManagement();
    },

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Escape key handling
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.show');
                if (activeModal) {
                    const closeBtn = activeModal.querySelector('.btn-close');
                    if (closeBtn) closeBtn.click();
                }
            }
            
            // Tab navigation enhancements
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
        });
    },

    setupAriaLabels() {
        // Add missing aria-labels
        const buttons = document.querySelectorAll('button:not([aria-label])');
        buttons.forEach(button => {
            const icon = button.querySelector('i[class*="ri-"]');
            if (icon) {
                const action = this.getActionFromIcon(icon.className);
                if (action) {
                    button.setAttribute('aria-label', action);
                }
            }
        });
    },

    getActionFromIcon(iconClass) {
        const iconMap = {
            'ri-add': 'Agregar',
            'ri-edit': 'Editar',
            'ri-delete': 'Eliminar',
            'ri-eye': 'Ver',
            'ri-download': 'Descargar',
            'ri-print': 'Imprimir',
            'ri-question': 'Ayuda',
            'ri-close': 'Cerrar'
        };
        
        for (const [key, value] of Object.entries(iconMap)) {
            if (iconClass.includes(key)) {
                return value;
            }
        }
        return null;
    },

    setupFocusManagement() {
        // Ensure proper focus management for modals
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('shown.bs.modal', () => {
                const firstInput = modal.querySelector('input, select, textarea, button');
                if (firstInput) {
                    firstInput.focus();
                }
            });
        });
    },

    handleTabNavigation(e) {
        // Enhanced tab navigation for complex components
        const activeElement = document.activeElement;
        const tutorialActive = document.getElementById('tutorialOverlay').style.display !== 'none';
        
        if (tutorialActive) {
            // Restrict tab navigation to tutorial elements
            const tutorialElements = document.querySelectorAll('#tutorialPopup button, #tutorialPopup a');
            const currentIndex = Array.from(tutorialElements).indexOf(activeElement);
            
            if (e.shiftKey) {
                // Shift+Tab (backward)
                if (currentIndex <= 0) {
                    e.preventDefault();
                    tutorialElements[tutorialElements.length - 1].focus();
                }
            } else {
                // Tab (forward)
                if (currentIndex >= tutorialElements.length - 1) {
                    e.preventDefault();
                    tutorialElements[0].focus();
                }
            }
        }
    }
};

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    try {
        // Initialize main manager
        areaOverviewManager = new AreaOverviewManager();
        
        // Initialize accessibility features
        AccessibilityManager.init();
        
        // Setup scroll handler
        window.addEventListener('scroll', handleScroll, { passive: true });
        
        // Setup intersection observer for animations
        if ('IntersectionObserver' in window) {
            observeAnimations();
        }
        
        // Initialize tooltips if Bootstrap is available
        if (window.bootstrap && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
        
        console.log('Area Overview initialized successfully');
        
    } catch (error) {
        ErrorHandler.handle(error, 'Initialization');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (areaOverviewManager) {
        areaOverviewManager.destroy();
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, pause animations or heavy operations
        if (areaOverviewManager && areaOverviewManager.simulation) {
            areaOverviewManager.simulation.stop();
        }
    } else {
        // Page is visible, resume operations
        if (areaOverviewManager && areaOverviewManager.simulation) {
            areaOverviewManager.simulation.restart();
        }
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AreaOverviewManager,
        ErrorHandler,
        AccessibilityManager,
        LocalStorageManager
    };
}