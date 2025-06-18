// Table Pagination Component

function initializeTablePagination() {
    // Demand table pagination
    initializeDemandTablePagination();
    
    // Endogenous table pagination
    initializeEndogenousTablePagination();
}

function initializeDemandTablePagination() {
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
    
    function updateTableDisplay() {
        // Hide all rows
        rows.forEach(row => row.style.display = 'none');
        
        // Show current page rows
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, rows.length);
        
        for (let i = startIndex; i < endIndex; i++) {
            if (rows[i]) {
                rows[i].style.display = 'table-row';
                rows[i].style.animation = 'fadeIn 0.2s ease';
            }
        }
        
        // Update page info
        if (pageInfo) pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;
        
        // Update button states
        if (prevBtn) prevBtn.disabled = currentPage === 1;
        if (nextBtn) nextBtn.disabled = currentPage === totalPages;
    }
    
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            if (currentPage > 1) {
                currentPage--;
                updateTableDisplay();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            if (currentPage < totalPages) {
                currentPage++;
                updateTableDisplay();
            }
        });
    }
    
    // Initialize display
    updateTableDisplay();
}

function initializeEndogenousTablePagination() {
    const table = document.getElementById('endogenousTable');
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const itemsPerPage = 15;
    let currentPage = 1;
    const totalPages = Math.ceil(rows.length / itemsPerPage);
    
    window.paginateEndogenousTable = function(direction) {
        if (direction === 'prev' && currentPage > 1) {
            currentPage--;
        } else if (direction === 'next' && currentPage < totalPages) {
            currentPage++;
        }
        
        // Hide all rows
        rows.forEach(row => row.style.display = 'none');
        
        // Show current page rows
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, rows.length);
        
        for (let i = startIndex; i < endIndex; i++) {
            if (rows[i]) {
                rows[i].style.display = 'table-row';
                rows[i].style.animation = 'fadeIn 0.2s ease';
            }
        }
        
        // Update page info
        const pageInfo = document.getElementById('endogenousPageInfo');
        if (pageInfo) pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;
        
        // Update button states
        const prevBtn = document.querySelector('[onclick="paginateEndogenousTable(\'prev\')"]');
        const nextBtn = document.querySelector('[onclick="paginateEndogenousTable(\'next\')"]');
        
        if (prevBtn) {
            prevBtn.parentElement.classList.toggle('disabled', currentPage === 1);
        }
        if (nextBtn) {
            nextBtn.parentElement.classList.toggle('disabled', currentPage === totalPages);
        }
    };
    
    // Initialize first page
    window.paginateEndogenousTable('init');
}

// Highlight validation rows on hover
document.addEventListener('DOMContentLoaded', function() {
    const validationRows = document.querySelectorAll('.validation-row');
    validationRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
            this.style.cursor = 'pointer';
        });
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
        row.addEventListener('click', function() {
            const day = this.dataset.day;
            console.log('Día seleccionado:', day);
        });
    });
});