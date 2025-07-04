/**
 * Export Manager - Manejo de exportaciones (PDF, Excel, CSV)
 */
class ExportManager {
    constructor() {
        this.isExporting = false;
        this.init();
    }

    init() {
        this.setupExportFunctions();
        this.setupPrintHandler();
    }

    setupExportFunctions() {
        // Función global para exportar a PDF
        window.exportToPDF = async () => {
            if (this.isExporting) return;
            
            const btn = event?.target;
            const originalText = btn?.innerHTML;
            
            try {
                this.isExporting = true;
                
                if (btn) {
                    btn.innerHTML = '<i class="bx bx-loader-alt bx-spin me-2"></i>Generando PDF...';
                    btn.disabled = true;
                }
                
                await this.generatePDF();
                
                this.showNotification('PDF generado exitosamente', 'success');
            } catch (error) {
                console.error('Error generating PDF:', error);
                this.showNotification('Error al generar PDF', 'error');
            } finally {
                this.isExporting = false;
                if (btn) {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
            }
        };

        // Función global para exportar a Excel
        window.exportToExcel = () => {
            if (this.isExporting) return;
            
            const btn = event?.target;
            const originalText = btn?.innerHTML;
            
            try {
                this.isExporting = true;
                
                if (btn) {
                    btn.innerHTML = '<i class="bx bx-loader-alt bx-spin me-2"></i>Generando Excel...';
                    btn.disabled = true;
                }
                
                this.generateExcel();
                
                this.showNotification('Archivo Excel generado exitosamente', 'success');
            } catch (error) {
                console.error('Error generating Excel:', error);
                this.showNotification('Error al generar Excel', 'error');
            } finally {
                this.isExporting = false;
                if (btn) {
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
            }
        };

        // Función para compartir resultados
        window.shareResults = () => {
            this.shareResults();
        };
    }

    async generatePDF() {
        // Verificar que html2canvas y jsPDF estén disponibles
        if (typeof html2canvas === 'undefined') {
            throw new Error('html2canvas no está disponible');
        }
        if (typeof jspdf === 'undefined') {
            throw new Error('jsPDF no está disponible');
        }

        // Preparar el elemento para captura
        const element = document.querySelector('.page-content');
        if (!element) {
            throw new Error('Elemento para exportar no encontrado');
        }

        // Configurar opciones de captura
        const captureOptions = {
            scale: 2,
            logging: false,
            useCORS: true,
            allowTaint: true,
            backgroundColor: '#ffffff',
            width: element.scrollWidth,
            height: element.scrollHeight
        };

        // Capturar elemento como canvas
        const canvas = await html2canvas(element, captureOptions);
        
        // Configurar PDF
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jspdf.jsPDF({
            orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
            unit: 'px',
            format: [canvas.width, canvas.height]
        });
        
        // Agregar imagen al PDF
        pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
        
        // Generar nombre de archivo
        const timestamp = new Date().getTime();
        const filename = `simulacion_resultados_${timestamp}.pdf`;
        
        // Descargar PDF
        pdf.save(filename);
    }

    generateExcel() {
        // Recopilar datos de todas las secciones
        const data = this.collectExportData();
        
        // Generar CSV (como alternativa simple a Excel)
        let csvContent = "data:text/csv;charset=utf-8,";
        
        // Headers principales
        csvContent += "Seccion,Variable,Valor,Unidad,Descripcion\n";
        
        // Datos de variables endógenas
        data.endogenousVariables.forEach(item => {
            csvContent += `"Variables Endogenas","${item.variable}","${item.value}","${item.unit}","${item.description}"\n`;
        });
        
        // Datos de validación
        data.validationData.forEach(item => {
            csvContent += `"Validacion","${item.day}","${item.error}","%","Error del dia ${item.day}"\n`;
        });
        
        // Datos estadísticos
        data.statisticalData.forEach(item => {
            csvContent += `"Estadisticas","${item.metric}","${item.value}","${item.unit}","${item.description}"\n`;
        });
        
        // Crear y descargar archivo
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `simulacion_resultados_${new Date().getTime()}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    collectExportData() {
        const data = {
            endogenousVariables: [],
            validationData: [],
            statisticalData: []
        };

        // Recopilar variables endógenas
        const endogenousRows = document.querySelectorAll('#endogenousTableBody tr[data-variable]');
        endogenousRows.forEach(row => {
            const variable = row.dataset.variable;
            const cells = row.querySelectorAll('td');
            if (cells.length >= 3) {
                data.endogenousVariables.push({
                    variable: variable,
                    value: cells[1].textContent.trim(),
                    unit: cells[2].textContent.trim(),
                    description: cells[0].querySelector('small')?.textContent.trim() || ''
                });
            }
        });

        // Recopilar datos de validación
        const validationRows = document.querySelectorAll('#validationDetailTable tbody tr');
        validationRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 7) {
                data.validationData.push({
                    day: cells[0].textContent.trim(),
                    error: cells[6].querySelector('span')?.textContent.replace('%', '').trim() || '0'
                });
            }
        });

        // Recopilar datos estadísticos
        const statsElements = document.querySelectorAll('.stat-value .counter');
        statsElements.forEach((element, index) => {
            const label = element.closest('.stat-item')?.querySelector('.stat-label')?.textContent || `Metric ${index + 1}`;
            data.statisticalData.push({
                metric: label,
                value: element.textContent.trim(),
                unit: this.extractUnit(element.closest('.stat-item')),
                description: label
            });
        });

        return data;
    }

    extractUnit(container) {
        const text = container?.textContent || '';
        if (text.includes('Bs.')) return 'Bs.';
        if (text.includes('L')) return 'L';
        if (text.includes('%')) return '%';
        return 'Unidad';
    }

    shareResults() {
        if (navigator.share) {
            navigator.share({
                title: 'Resultados de Simulación',
                text: 'Mira los resultados de mi simulación de negocio',
                url: window.location.href
            }).then(() => {
                this.showNotification('Compartido exitosamente', 'success');
            }).catch((error) => {
                console.log('Error sharing:', error);
                this.fallbackShare();
            });
        } else {
            this.fallbackShare();
        }
    }

    fallbackShare() {
        // Copiar URL al portapapeles como alternativa
        if (navigator.clipboard) {
            navigator.clipboard.writeText(window.location.href).then(() => {
                this.showNotification('Enlace copiado al portapapeles', 'success');
            }).catch(() => {
                this.showNotification('No se pudo compartir automáticamente', 'warning');
            });
        } else {
            // Crear un input temporal para copiar
            const input = document.createElement('input');
            input.value = window.location.href;
            document.body.appendChild(input);
            input.select();
            
            try {
                document.execCommand('copy');
                this.showNotification('Enlace copiado al portapapeles', 'success');
            } catch (err) {
                this.showNotification('No se pudo copiar el enlace', 'error');
            }
            
            document.body.removeChild(input);
        }
    }

    setupPrintHandler() {
        // Preparar impresión
        window.addEventListener('beforeprint', () => {
            // Expandir secciones colapsadas para impresión
            document.querySelectorAll('.collapse').forEach(el => {
                el.classList.add('show');
            });
            
            // Mostrar todos los días en resultados diarios
            document.querySelectorAll('.daily-result-item').forEach(item => {
                item.style.display = 'block';
            });
        });

        window.addEventListener('afterprint', () => {
            // Restaurar estado después de imprimir
            document.querySelectorAll('.collapse').forEach(el => {
                if (!el.classList.contains('show')) {
                    el.classList.remove('show');
                }
            });
            
            // Restaurar paginación de resultados diarios
            if (window.paginationManager) {
                const currentDay = window.paginationManager.getCurrentPage('dailyResults');
                document.querySelectorAll('.daily-result-item').forEach((item, index) => {
                    item.style.display = (index + 1) === currentDay ? 'block' : 'none';
                });
            }
        });
    }

    // Exportar datos específicos de validación
    exportValidationResults() {
        let csv = 'Día,Fecha,Producto,Empresa,Demanda Simulada (L),Demanda Real (L),Diferencia (L),Error %,Veredicto\n';
        
        const tableRows = document.querySelectorAll('#validationDetailTable tbody tr.validation-row');
        
        tableRows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 8) {
                const day = cells[0].textContent.trim();
                const date = cells[1].textContent.trim();
                const productInfo = cells[2].textContent.trim().split('\n');
                const product = productInfo[0]?.trim() || '';
                const business = productInfo[1]?.trim() || '';
                const simulated = cells[3].textContent.replace(' L', '').trim();
                const real = cells[4].textContent.replace(' L', '').trim();
                const difference = cells[5].textContent.replace(' L', '').replace('+', '').trim();
                const error = cells[6].querySelector('span')?.textContent.replace('%', '').trim() || '0';
                const verdict = cells[7].textContent.trim();
                
                csv += `${day},"${date}","${product}","${business}",${simulated},${real},${difference},${error},"${verdict}"\n`;
            }
        });
        
        // Agregar totales si existen
        const footerCells = document.querySelectorAll('#validationDetailTable tfoot td');
        if (footerCells.length >= 7) {
            csv += '\nTotales/Promedios,,,,' + 
                   footerCells[3].textContent.replace(' L', '').trim() + ',' +
                   footerCells[4].textContent.replace(' L', '').trim() + ',' +
                   footerCells[5].textContent.replace(' L', '').replace('+', '').trim() + ',' +
                   footerCells[6].querySelector('span')?.textContent.replace('%', '').trim() + ',';
        }
        
        // Descargar archivo
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'validacion_modelo_' + new Date().getTime() + '.csv';
        link.click();
        
        this.showNotification('Resultados de validación exportados exitosamente', 'success');
    }

    // Exportar variables endógenas
    exportEndogenousVariables() {
        let csv = 'Variable,Valor Total,Unidad,Promedio Diario,Tendencia,Descripcion\n';
        
        const rows = document.querySelectorAll('#endogenousTableBody tr[data-variable]');
        rows.forEach(row => {
            if (row.style.display !== 'none') {
                const variable = row.dataset.variable;
                const cells = row.querySelectorAll('td');
                const total = cells[1]?.textContent.replace(/[,]/g, '') || '';
                const unit = cells[2]?.textContent || '';
                const average = cells[3]?.textContent.replace(/[,]/g, '') || '';
                const trend = row.dataset.trend || '';
                const description = cells[0]?.querySelector('small')?.textContent || '';
                
                csv += `"${variable}","${total}","${unit}","${average}","${trend}","${description}"\n`;
            }
        });
        
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'variables_endogenas_' + new Date().getTime() + '.csv';
        link.click();
        
        this.showNotification('Variables endógenas exportadas exitosamente', 'success');
    }

    showNotification(message, type = 'info') {
        // Usar el sistema de notificaciones del chart manager si está disponible
        if (window.chartManager) {
            window.chartManager.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
}

// Exportar instancia global
window.exportManager = new ExportManager();

// Funciones globales para compatibilidad
window.exportValidationResults = () => window.exportManager.exportValidationResults();
window.exportEndogenousVariables = () => window.exportManager.exportEndogenousVariables();