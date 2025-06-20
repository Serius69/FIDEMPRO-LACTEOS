// Area management functions
function showAreaDetails(areaId) {
    // Implementation for showing area details modal
    console.log('Showing details for area:', areaId);
    
    // Create modal or redirect to details page
    // This can be expanded based on specific requirements
}

function refreshPage() {
    window.location.reload();
}

function showHelp() {
    if (window.SimulationTutorial) {
        SimulationTutorial.start();
    } else {
        alert('Sistema de ayuda no disponible. Por favor contacte al soporte técnico.');
    }
}

// Initialize equations display on page load
document.addEventListener('DOMContentLoaded', function() {
    // This will be handled by EquationManager in simulation-core.js
    if (window.EquationManager) {
        EquationManager.initializeAll();
    }
});