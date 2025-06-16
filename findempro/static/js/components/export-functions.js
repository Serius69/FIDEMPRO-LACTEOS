// Export Functions Component
function initializeExportFunctions() {
    window.exportToPDF = async function() {
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="bx bx-loader-alt bx-spin me-2"></i>Generando PDF...';
        btn.disabled = true;
        
        try {
            // Wait for html2canvas to be ready
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Capture the main content
            const element = document.querySelector('.page-content');
            const canvas = await html2canvas(element, {
                scale: 2,
                logging: false,
                useCORS: true,
                allowTaint: true
            });
            
            // Convert to PDF
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jspdf.jsPDF({
                orientation: 'landscape',
                unit: 'px',
                format: [canvas.width, canvas.height]
            });
            
            pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
            pdf.save(`simulacion_${new Date().getTime()}_resultados.pdf`);
            
            showNotification('PDF generado exitosamente', 'success');
        } catch (error) {
            console.error('Error generating PDF:', error);
            showNotification('Error al generar PDF', 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    };
    
    window.exportToExcel = function() {
        const btn = event.target;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="bx bx-loader-alt bx-spin me-2"></i>Generando Excel...';
        btn.disabled = true;
        
        // Create CSV content from Django template variables
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Variable,Valor Total,Unidad\n";
        
        // This would be populated dynamically from the template
        // For now, we'll get data from the DOM
        const rows = document.querySelectorAll('#endogenousTable tbody tr');
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 3) {
                const variable = cells[0].querySelector('strong').textContent;
                const value = cells[1].textContent.trim().replace(/[^\d.-]/g, '');
                const unit = cells[2].textContent.trim();
                csvContent += `"${variable}","${value}","${unit}"\n`;
            }
        });
        
        // Create download link
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `simulacion_${new Date().getTime()}_resultados.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showNotification('Archivo CSV generado exitosamente', 'success');
        
        btn.innerHTML = originalText;
        btn.disabled = false;
    };
    
    window.exportValidationResults = function() {
        let csv = 'Día,Fecha,Producto,Empresa,Demanda Simulada (L),Demanda Real (L),Diferencia (L),Error %,Veredicto\n';
        
        const tableRows = document.querySelectorAll('#validationDetailTable tbody tr.validation-row');
        
        tableRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            const day = cells[0].textContent.trim();
            const date = cells[1].textContent.trim();
            const productInfo = cells[2].textContent.trim().split('\n');
            const product = productInfo[0].trim();
            const business = productInfo[1] ? productInfo[1].trim() : '';
            const simulated = cells[3].textContent.replace(' L', '').trim();
            const real = cells[4].textContent.replace(' L', '').trim();
            const difference = cells[5].textContent.replace(' L', '').replace('+', '').trim();
            const error = cells[6].querySelector('span').textContent.replace('%', '').trim();
            const verdict = cells[7].textContent.trim();
            
            csv += `${day},"${date}","${product}","${business}",${simulated},${real},${difference},${error},"${verdict}"\n`;
        });
        
        // Add totals
        const footerCells = document.querySelectorAll('#validationDetailTable tfoot td');
        if (footerCells.length > 0) {
            csv += '\nTotales/Promedios,,,,' + 
                   footerCells[3].textContent.replace(' L', '').trim() + ',' +
                   footerCells[4].textContent.replace(' L', '').trim() + ',' +
                   footerCells[5].textContent.replace(' L', '').replace('+', '').trim() + ',' +
                   footerCells[6].querySelector('span').textContent.replace('%', '').trim() + ',';
        }
        
        // Download file
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'validacion_modelo_' + new Date().getTime() + '.csv';
        link.click();
        
        showNotification('Resultados exportados exitosamente', 'success');
    };
}