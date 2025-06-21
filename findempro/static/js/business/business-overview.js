/**
 * Business Overview Management
 * Handles product operations, data visualization, and overview interactions
 */

class BusinessOverviewManager {
    constructor() {
        this.businessId = null;
        this.currentPage = 1;
        this.filters = {
            status: 'all',
            type: 'all',
            search: ''
        };
        
        this.init();
    }

    init() {
        this.extractBusinessId();
        this.setupElements();
        this.bindEvents();
        this.initializeFeatures();
    }

    extractBusinessId() {
        // Extract business ID from URL or data attribute
        const pathParts = window.location.pathname.split('/');
        this.businessId = pathParts[pathParts.indexOf('business') + 1] || 
                         document.querySelector('[data-business-id]')?.dataset.businessId;
    }

    setupElements() {
        this.elements = {
            // Product table elements
            productsTable: document.querySelector('.products-table'),
            productsTableWrapper: document.querySelector('.products-table-wrapper'),
            emptyProductsState: document.querySelector('.empty-products'),
            
            // Filter and search elements
            searchInput: document.getElementById('productSearch'),
            statusFilter: document.getElementById('statusFilter'),
            typeFilter: document.getElementById('typeFilter'),
            
            // Pagination elements
            pagination: document.querySelector('.products-pagination'),
            
            // Action buttons
            addProductBtn: document.querySelector('a[href*="product.create"]'),
            editProductBtns: document.querySelectorAll('.edit-product'),
            deleteProductBtns: document.querySelectorAll('.delete-product'),
            
            // Business profile elements
            businessImage: document.querySelector('.business-image'),
            businessName: document.querySelector('.business-name'),
            businessDetails: document.querySelector('.business-details')
        };
    }

    bindEvents() {
        // Product operations
        this.bindProductEvents();
        
        // Search and filter
        this.bindFilterEvents();
        
        // Table interactions
        this.bindTableEvents();
        
        // Business profile interactions
        this.bindProfileEvents();
        
        // Window events
        window.addEventListener('resize', () => this.handleResize());
        window.addEventListener('scroll', () => this.handleScroll());
    }

    bindProductEvents() {
        // Edit product buttons
        this.elements.editProductBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleEditProduct(e));
        });

        // Delete product buttons
        this.elements.deleteProductBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.handleDeleteProduct(e));
        });

        // Product row interactions
        document.querySelectorAll('.product-row').forEach(row => {
            this.enhanceProductRow(row);
        });
    }

    bindFilterEvents() {
        // Search input
        if (this.elements.searchInput) {
            let searchTimeout;
            this.elements.searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.filters.search = e.target.value;
                    this.applyFilters();
                }, 300);
            });
        }

        // Status filter
        if (this.elements.statusFilter) {
            this.elements.statusFilter.addEventListener('change', (e) => {
                this.filters.status = e.target.value;
                this.applyFilters();
            });
        }

        // Type filter
        if (this.elements.typeFilter) {
            this.elements.typeFilter.addEventListener('change', (e) => {
                this.filters.type = e.target.value;
                this.applyFilters();
            });
        }
    }

    bindTableEvents() {
        // Table sorting
        const tableHeaders = this.elements.productsTable?.querySelectorAll('th[data-sortable]');
        tableHeaders?.forEach(header => {
            header.addEventListener('click', () => this.handleSort(header));
        });

        // Row selection
        const checkboxes = this.elements.productsTable?.querySelectorAll('input[type="checkbox"]');
        checkboxes?.forEach(checkbox => {
            checkbox.addEventListener('change', () => this.handleRowSelection());
        });
    }

    bindProfileEvents() {
        // Business image lightbox
        if (this.elements.businessImage) {
            this.elements.businessImage.addEventListener('click', () => {
                this.openImageLightbox(this.elements.businessImage.src);
            });
        }

        // Copy business details
        const copyButtons = document.querySelectorAll('[data-copy]');
        copyButtons.forEach(btn => {
            btn.addEventListener('click', (e) => this.copyToClipboard(e));
        });
    }

    // Product Operations
    handleEditProduct(e) {
        e.preventDefault();
        const productId = e.currentTarget.dataset.productId;
        this.openEditProductModal(productId);
    }

    handleDeleteProduct(e) {
        e.preventDefault();
        const productId = e.currentTarget.dataset.productId;
        this.openDeleteProductModal(productId);
    }

    async openEditProductModal(productId) {
        try {
            this.showLoadingState('Cargando producto...');
            
            const response = await fetch(`/product/api/details/${productId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.displayEditProductModal(data.data);
            } else {
                this.showToast('error', data.message || 'Error al cargar el producto');
            }
        } catch (error) {
            console.error('Error loading product:', error);
            this.showToast('error', 'Error de conexión');
        } finally {
            this.hideLoadingState();
        }
    }

    displayEditProductModal(productData) {
        // Create or show edit modal
        let modal = document.getElementById('editProductModal');
        
        if (!modal) {
            modal = this.createEditProductModal();
            document.body.appendChild(modal);
        }
        
        this.populateEditForm(modal, productData);
        
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }

    createEditProductModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'editProductModal';
        modal.setAttribute('tabindex', '-1');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="ri-edit-line me-2"></i>Editar Producto
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="editProductForm" class="needs-validation" novalidate>
                            <input type="hidden" name="product_id" id="edit_product_id">
                            
                            <div class="row g-3">
                                <div class="col-12 text-center">
                                    <div class="image-preview-container">
                                        <img id="edit_product_image" class="product-preview-image" alt="Preview">
                                        <div class="upload-overlay">
                                            <input type="file" id="edit_image_input" name="image" accept="image/*">
                                            <label for="edit_image_input" class="upload-label">
                                                <i class="ri-camera-line"></i>
                                                <span>Cambiar imagen</span>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="col-md-6">
                                    <label for="edit_product_name" class="form-label">
                                        <i class="ri-product-hunt-line me-1"></i>Nombre del Producto
                                    </label>
                                    <input type="text" class="form-control" id="edit_product_name" 
                                           name="name" required>
                                    <div class="invalid-feedback">Ingresa el nombre del producto</div>
                                </div>
                                
                                <div class="col-md-6">
                                    <label for="edit_product_type" class="form-label">
                                        <i class="ri-price-tag-line me-1"></i>Tipo
                                    </label>
                                    <select class="form-select" id="edit_product_type" name="type" required>
                                        <option value="">Seleccionar tipo</option>
                                        <option value="lacteo">Lácteo</option>
                                        <option value="panaderia">Panadería</option>
                                        <option value="carniceria">Carnicería</option>
                                        <option value="verduleria">Verdulería</option>
                                        <option value="otros">Otros</option>
                                    </select>
                                    <div class="invalid-feedback">Selecciona un tipo</div>
                                </div>
                                
                                <div class="col-12">
                                    <label for="edit_product_description" class="form-label">
                                        <i class="ri-file-text-line me-1"></i>Descripción
                                    </label>
                                    <textarea class="form-control" id="edit_product_description" 
                                              name="description" rows="3"></textarea>
                                </div>
                                
                                <div class="col-md-6">
                                    <div class="form-check form-switch">
                                        <input class="form-check-input" type="checkbox" 
                                               id="edit_product_active" name="is_active">
                                        <label class="form-check-label" for="edit_product_active">
                                            Producto activo
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            Cancelar
                        </button>
                        <button type="submit" form="editProductForm" class="btn btn-primary" 
                                id="saveProductBtn">
                            <i class="ri-save-line me-1"></i>Guardar Cambios
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Bind form submission
        const form = modal.querySelector('#editProductForm');
        form.addEventListener('submit', (e) => this.handleProductFormSubmit(e));
        
        return modal;
    }

    populateEditForm(modal, data) {
        modal.querySelector('#edit_product_id').value = data.id;
        modal.querySelector('#edit_product_name').value = data.name || '';
        modal.querySelector('#edit_product_type').value = data.type || '';
        modal.querySelector('#edit_product_description').value = data.description || '';
        modal.querySelector('#edit_product_active').checked = data.is_active || false;
        
        const imagePreview = modal.querySelector('#edit_product_image');
        if (data.image_url) {
            imagePreview.src = data.image_url;
            imagePreview.style.display = 'block';
        }
    }

    async handleProductFormSubmit(e) {
        e.preventDefault();
        
        const form = e.target;
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            return;
        }
        
        try {
            this.setProductFormLoading(true);
            
            const formData = new FormData(form);
            const productId = formData.get('product_id');
            
            const response = await fetch(`/product/update/${productId}/`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('success', data.message || 'Producto actualizado exitosamente');
                this.hideModal('editProductModal');
                this.refreshProductsTable();
            } else {
                this.showToast('error', data.message || 'Error al actualizar el producto');
            }
        } catch (error) {
            console.error('Error updating product:', error);
            this.showToast('error', 'Error de conexión');
        } finally {
            this.setProductFormLoading(false);
        }
    }

    openDeleteProductModal(productId) {
        const modal = this.createDeleteProductModal(productId);
        document.body.appendChild(modal);
        
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // Remove modal when hidden
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    createDeleteProductModal(productId) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header border-0">
                        <h5 class="modal-title">Confirmar Eliminación</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center py-4">
                        <div class="mb-4">
                            <i class="ri-delete-bin-line text-danger" style="font-size: 4rem;"></i>
                        </div>
                        <h4 class="mb-3">¿Estás seguro?</h4>
                        <p class="text-muted">
                            Esta acción eliminará permanentemente el producto. 
                            <strong>No se puede deshacer.</strong>
                        </p>
                    </div>
                    <div class="modal-footer border-0 justify-content-center">
                        <button type="button" class="btn btn-light px-4" data-bs-dismiss="modal">
                            Cancelar
                        </button>
                        <button type="button" class="btn btn-danger px-4" id="confirmDeleteProduct">
                            <i class="ri-delete-bin-line me-1"></i>Eliminar
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Bind delete confirmation
        modal.querySelector('#confirmDeleteProduct').addEventListener('click', () => {
            this.confirmDeleteProduct(productId, modal);
        });
        
        return modal;
    }

    async confirmDeleteProduct(productId, modal) {
        try {
            const deleteBtn = modal.querySelector('#confirmDeleteProduct');
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Eliminando...';
            
            const response = await fetch(`/product/delete/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showToast('success', data.message || 'Producto eliminado exitosamente');
                bootstrap.Modal.getInstance(modal).hide();
                this.refreshProductsTable();
            } else {
                this.showToast('error', data.message || 'Error al eliminar el producto');
            }
        } catch (error) {
            console.error('Error deleting product:', error);
            this.showToast('error', 'Error de conexión');
        }
    }

    // Table Management
    enhanceProductRow(row) {
        // Add hover effects
        row.addEventListener('mouseenter', () => {
            row.style.transform = 'scale(1.01)';
        });
        
        row.addEventListener('mouseleave', () => {
            row.style.transform = 'scale(1)';
        });
        
        // Add keyboard navigation
        row.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const editBtn = row.querySelector('.edit-product');
                if (editBtn) editBtn.click();
            }
        });
    }

    applyFilters() {
        const rows = document.querySelectorAll('.product-row');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const shouldShow = this.shouldShowRow(row);
            row.style.display = shouldShow ? '' : 'none';
            
            if (shouldShow) {
                visibleCount++;
                this.animateElement(row, 'fadeInLeft');
            }
        });
        
        this.updateEmptyState(visibleCount === 0);
        this.updateResultsCount(visibleCount);
    }

    shouldShowRow(row) {
        const productName = row.querySelector('.product-name')?.textContent.toLowerCase() || '';
        const productType = row.querySelector('.product-type-cell')?.textContent.toLowerCase() || '';
        const productStatus = row.querySelector('.status-badge')?.classList.contains('status-active') ? 'active' : 'inactive';
        
        // Search filter
        if (this.filters.search) {
            const searchTerm = this.filters.search.toLowerCase();
            if (!productName.includes(searchTerm) && !productType.includes(searchTerm)) {
                return false;
            }
        }
        
        // Status filter
        if (this.filters.status !== 'all' && this.filters.status !== productStatus) {
            return false;
        }
        
        // Type filter
        if (this.filters.type !== 'all' && !productType.includes(this.filters.type.toLowerCase())) {
            return false;
        }
        
        return true;
    }

    handleSort(header) {
        const column = header.dataset.sortable;
        const currentOrder = header.dataset.order || 'asc';
        const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
        
        // Update header
        document.querySelectorAll('th[data-sortable]').forEach(th => {
            th.classList.remove('sorted-asc', 'sorted-desc');
            delete th.dataset.order;
        });
        
        header.classList.add(`sorted-${newOrder}`);
        header.dataset.order = newOrder;
        
        // Sort rows
        this.sortTable(column, newOrder);
    }

    sortTable(column, order) {
        const tbody = this.elements.productsTable?.querySelector('tbody');
        if (!tbody) return;
        
        const rows = Array.from(tbody.querySelectorAll('.product-row'));
        
        rows.sort((a, b) => {
            let aVal, bVal;
            
            switch (column) {
                case 'name':
                    aVal = a.querySelector('.product-name')?.textContent || '';
                    bVal = b.querySelector('.product-name')?.textContent || '';
                    break;
                case 'type':
                    aVal = a.querySelector('.product-type-cell')?.textContent || '';
                    bVal = b.querySelector('.product-type-cell')?.textContent || '';
                    break;
                case 'date':
                    aVal = new Date(a.querySelector('.product-date-cell')?.textContent || '');
                    bVal = new Date(b.querySelector('.product-date-cell')?.textContent || '');
                    break;
                case 'status':
                    aVal = a.querySelector('.status-badge')?.classList.contains('status-active') ? 1 : 0;
                    bVal = b.querySelector('.status-badge')?.classList.contains('status-active') ? 1 : 0;
                    break;
                default:
                    return 0;
            }
            
            if (aVal < bVal) return order === 'asc' ? -1 : 1;
            if (aVal > bVal) return order === 'asc' ? 1 : -1;
            return 0;
        });
        
        // Re-append sorted rows
        rows.forEach(row => tbody.appendChild(row));
        
        // Animate rows
        rows.forEach((row, index) => {
            row.style.animationDelay = `${index * 0.1}s`;
            this.animateElement(row, 'fadeInLeft');
        });
    }

    handleRowSelection() {
        const checkboxes = this.elements.productsTable?.querySelectorAll('tbody input[type="checkbox"]');
        const checkedBoxes = this.elements.productsTable?.querySelectorAll('tbody input[type="checkbox"]:checked');
        
        this.updateBulkActions(checkedBoxes?.length || 0);
    }

    updateBulkActions(selectedCount) {
        let bulkActions = document.getElementById('bulkActions');
        
        if (selectedCount > 0) {
            if (!bulkActions) {
                bulkActions = this.createBulkActionsBar();
                this.elements.productsTableWrapper?.parentNode.insertBefore(bulkActions, this.elements.productsTableWrapper);
            }
            
            bulkActions.querySelector('.selected-count').textContent = selectedCount;
            bulkActions.style.display = 'block';
        } else if (bulkActions) {
            bulkActions.style.display = 'none';
        }
    }

    createBulkActionsBar() {
        const bulkActions = document.createElement('div');
        bulkActions.id = 'bulkActions';
        bulkActions.className = 'bulk-actions-bar bg-primary text-white p-3 rounded mb-3';
        bulkActions.style.display = 'none';
        
        bulkActions.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <i class="ri-checkbox-line me-2"></i>
                    <span class="selected-count">0</span> productos seleccionados
                </div>
                <div class="btn-group">
                    <button class="btn btn-sm btn-light" onclick="businessOverview.bulkEdit()">
                        <i class="ri-edit-line me-1"></i>Editar
                    </button>
                    <button class="btn btn-sm btn-outline-light" onclick="businessOverview.bulkDelete()">
                        <i class="ri-delete-bin-line me-1"></i>Eliminar
                    </button>
                    <button class="btn btn-sm btn-outline-light" onclick="businessOverview.clearSelection()">
                        <i class="ri-close-line me-1"></i>Cancelar
                    </button>
                </div>
            </div>
        `;
        
        return bulkActions;
    }

    // Utility Methods
    async refreshProductsTable() {
        try {
            this.showLoadingState('Actualizando productos...');
            
            const response = await fetch(`/business/overview/${this.businessId}/?ajax=1`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();
            
            if (data.success) {
                this.updateProductsTable(data.products);
            }
        } catch (error) {
            console.error('Error refreshing products:', error);
            this.showToast('error', 'Error al actualizar la tabla');
        } finally {
            this.hideLoadingState();
        }
    }

    updateProductsTable(products) {
        const tbody = this.elements.productsTable?.querySelector('tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (products.length === 0) {
            this.showEmptyProductsState();
            return;
        }
        
        products.forEach((product, index) => {
            const row = this.createProductRow(product);
            row.style.animationDelay = `${index * 0.1}s`;
            tbody.appendChild(row);
            this.enhanceProductRow(row);
        });
        
        this.bindProductEvents();
    }

    createProductRow(product) {
        const row = document.createElement('tr');
        row.className = 'product-row';
        row.dataset.productId = product.id;
        
        row.innerHTML = `
            <td class="product-image-cell">
                <img src="${product.image_url}" alt="${product.name}" class="product-image" />
            </td>
            <td class="product-name-cell">
                <h6 class="product-name">${product.name}</h6>
            </td>
            <td class="product-type-cell">${product.type_display || product.type}</td>
            <td class="product-date-cell">${product.date_created}</td>
            <td class="product-status-cell">
                <span class="status-badge ${product.is_active ? 'status-active' : 'status-inactive'}">
                    ${product.is_active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td class="product-actions-cell">
                <div class="dropdown">
                    <button class="btn btn-sm btn-light dropdown-toggle" type="button" data-bs-toggle="dropdown">
                        <i class="ri-more-2-fill"></i>
                    </button>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <li>
                            <a class="dropdown-item edit-product" href="#" data-product-id="${product.id}">
                                <i class="ri-pencil-fill me-2"></i>Editar
                            </a>
                        </li>
                        <li><hr class="dropdown-divider"></li>
                        <li>
                            <a class="dropdown-item delete-product text-danger" href="#" data-product-id="${product.id}">
                                <i class="ri-delete-bin-fill me-2"></i>Eliminar
                            </a>
                        </li>
                    </ul>
                </div>
            </td>
        `;
        
        return row;
    }

    updateEmptyState(isEmpty) {
        const emptyState = this.elements.emptyProductsState;
        const table = this.elements.productsTableWrapper;
        
        if (isEmpty) {
            if (table) table.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
        } else {
            if (table) table.style.display = 'block';
            if (emptyState) emptyState.style.display = 'none';
        }
    }

    updateResultsCount(count) {
        let resultsInfo = document.getElementById('resultsInfo');
        
        if (!resultsInfo) {
            resultsInfo = document.createElement('div');
            resultsInfo.id = 'resultsInfo';
            resultsInfo.className = 'results-info text-muted mb-2';
            this.elements.productsTableWrapper?.parentNode.insertBefore(resultsInfo, this.elements.productsTableWrapper);
        }
        
        if (this.filters.search || this.filters.status !== 'all' || this.filters.type !== 'all') {
            resultsInfo.textContent = `${count} productos encontrados`;
            resultsInfo.style.display = 'block';
        } else {
            resultsInfo.style.display = 'none';
        }
    }

    // Business Profile Features
    openImageLightbox(imageSrc) {
        const lightbox = this.createLightbox(imageSrc);
        document.body.appendChild(lightbox);
        
        setTimeout(() => lightbox.classList.add('show'), 100);
        
        // Remove on click outside or ESC
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox) {
                this.closeLightbox(lightbox);
            }
        });
        
        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                businessOverview.closeLightbox(lightbox);
                document.removeEventListener('keydown', escHandler);
            }
        });
    }

    createLightbox(imageSrc) {
        const lightbox = document.createElement('div');
        lightbox.className = 'lightbox position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
        lightbox.style.cssText = `
            background: rgba(0, 0, 0, 0.9);
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
            cursor: pointer;
        `;
        
        lightbox.innerHTML = `
            <div class="lightbox-content text-center">
                <img src="${imageSrc}" alt="Business Image" 
                     style="max-width: 90vw; max-height: 90vh; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.5);">
                <button class="btn-close btn-close-white position-absolute top-0 end-0 m-3" 
                        style="font-size: 1.5rem; opacity: 0.8;"
                        onclick="businessOverview.closeLightbox(this.closest('.lightbox'))"></button>
            </div>
        `;
        
        return lightbox;
    }

    closeLightbox(lightbox) {
        lightbox.style.opacity = '0';
        setTimeout(() => lightbox.remove(), 300);
    }

    async copyToClipboard(e) {
        e.preventDefault();
        const textToCopy = e.currentTarget.dataset.copy;
        
        try {
            await navigator.clipboard.writeText(textToCopy);
            this.showToast('success', 'Copiado al portapapeles');
            
            // Visual feedback
            const icon = e.currentTarget.querySelector('i');
            const originalClass = icon.className;
            icon.className = 'ri-check-line';
            
            setTimeout(() => {
                icon.className = originalClass;
            }, 2000);
        } catch (error) {
            this.showToast('error', 'Error al copiar');
        }
    }

    // Advanced Features
    initializeFeatures() {
        this.initializeStats();
        this.initializeCharts();
        this.initializeSearch();
        this.initializeExport();
    }

    initializeStats() {
        // Calculate and display quick stats
        const activeProducts = document.querySelectorAll('.status-active').length;
        const totalProducts = document.querySelectorAll('.product-row').length;
        const inactiveProducts = totalProducts - activeProducts;
        
        this.displayQuickStats({
            total: totalProducts,
            active: activeProducts,
            inactive: inactiveProducts
        });
    }

    displayQuickStats(stats) {
        let statsContainer = document.getElementById('quickStats');
        
        if (!statsContainer) {
            statsContainer = document.createElement('div');
            statsContainer.id = 'quickStats';
            statsContainer.className = 'quick-stats row g-3 mb-4';
            
            const productsHeader = document.querySelector('.products-header');
            productsHeader?.parentNode.insertBefore(statsContainer, productsHeader.nextSibling);
        }
        
        statsContainer.innerHTML = `
            <div class="col-md-4">
                <div class="stat-card bg-primary text-white p-3 rounded">
                    <div class="d-flex align-items-center">
                        <i class="ri-box-line fs-2 me-3"></i>
                        <div>
                            <h3 class="mb-0">${stats.total}</h3>
                            <small>Total Productos</small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card bg-success text-white p-3 rounded">
                    <div class="d-flex align-items-center">
                        <i class="ri-check-line fs-2 me-3"></i>
                        <div>
                            <h3 class="mb-0">${stats.active}</h3>
                            <small>Productos Activos</small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="stat-card bg-warning text-white p-3 rounded">
                    <div class="d-flex align-items-center">
                        <i class="ri-pause-line fs-2 me-3"></i>
                        <div>
                            <h3 class="mb-0">${stats.inactive}</h3>
                            <small>Productos Inactivos</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    initializeCharts() {
        // Initialize product type distribution chart
        if (typeof ApexCharts !== 'undefined') {
            this.createProductTypeChart();
        }
    }

    createProductTypeChart() {
        const chartContainer = document.createElement('div');
        chartContainer.id = 'productTypeChart';
        chartContainer.className = 'mt-4';
        
        const productsCard = document.querySelector('.products-card .products-content');
        productsCard?.appendChild(chartContainer);
        
        // Get data
        const typeData = this.getProductTypeData();
        
        const options = {
            series: typeData.values,
            chart: {
                type: 'donut',
                height: 300
            },
            labels: typeData.labels,
            colors: ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d'],
            legend: {
                position: 'bottom'
            },
            title: {
                text: 'Distribución por Tipo de Producto',
                align: 'center'
            }
        };
        
        const chart = new ApexCharts(chartContainer, options);
        chart.render();
    }

    getProductTypeData() {
        const types = {};
        
        document.querySelectorAll('.product-type-cell').forEach(cell => {
            const type = cell.textContent.trim();
            types[type] = (types[type] || 0) + 1;
        });
        
        return {
            labels: Object.keys(types),
            values: Object.values(types)
        };
    }

    initializeSearch() {
        // Enhanced search with suggestions
        if (this.elements.searchInput) {
            this.setupSearchSuggestions();
        }
    }

    setupSearchSuggestions() {
        const searchContainer = this.elements.searchInput.parentNode;
        const suggestions = document.createElement('div');
        suggestions.className = 'search-suggestions position-absolute bg-white border rounded shadow-sm';
        suggestions.style.cssText = `
            top: 100%; left: 0; right: 0; z-index: 1000; display: none;
            max-height: 200px; overflow-y: auto;
        `;
        
        searchContainer.style.position = 'relative';
        searchContainer.appendChild(suggestions);
        
        this.elements.searchInput.addEventListener('input', (e) => {
            this.updateSearchSuggestions(e.target.value, suggestions);
        });
        
        // Hide suggestions on outside click
        document.addEventListener('click', (e) => {
            if (!searchContainer.contains(e.target)) {
                suggestions.style.display = 'none';
            }
        });
    }

    updateSearchSuggestions(query, suggestionsContainer) {
        if (query.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        const products = Array.from(document.querySelectorAll('.product-row'));
        const suggestions = new Set();
        
        products.forEach(row => {
            const name = row.querySelector('.product-name')?.textContent.toLowerCase() || '';
            const type = row.querySelector('.product-type-cell')?.textContent.toLowerCase() || '';
            
            if (name.includes(query.toLowerCase())) {
                suggestions.add(row.querySelector('.product-name')?.textContent);
            }
            if (type.includes(query.toLowerCase())) {
                suggestions.add(row.querySelector('.product-type-cell')?.textContent);
            }
        });
        
        if (suggestions.size > 0) {
            suggestionsContainer.innerHTML = Array.from(suggestions)
                .slice(0, 5)
                .map(suggestion => `
                    <div class="suggestion-item p-2 border-bottom cursor-pointer" 
                         onclick="businessOverview.selectSuggestion('${suggestion}')">
                        ${suggestion}
                    </div>
                `).join('');
            suggestionsContainer.style.display = 'block';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    }

    selectSuggestion(suggestion) {
        this.elements.searchInput.value = suggestion;
        this.filters.search = suggestion;
        this.applyFilters();
        
        const suggestions = document.querySelector('.search-suggestions');
        if (suggestions) suggestions.style.display = 'none';
    }

    initializeExport() {
        // Add export functionality
        const exportBtn = document.createElement('button');
        exportBtn.className = 'btn btn-outline-primary btn-sm';
        exportBtn.innerHTML = '<i class="ri-download-line me-1"></i>Exportar';
        exportBtn.onclick = () => this.exportProducts();
        
        const productsHeader = document.querySelector('.products-header');
        productsHeader?.appendChild(exportBtn);
    }

    async exportProducts() {
        try {
            const response = await fetch(`/business/export-products/${this.businessId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `productos_${this.businessId}_${new Date().getTime()}.xlsx`;
                a.click();
                window.URL.revokeObjectURL(url);
                
                this.showToast('success', 'Productos exportados exitosamente');
            } else {
                this.showToast('error', 'Error al exportar productos');
            }
        } catch (error) {
            console.error('Error exporting products:', error);
            this.showToast('error', 'Error de conexión');
        }
    }

    // Event Handlers
    handleResize() {
        // Handle responsive behavior
        if (window.innerWidth < 768) {
            this.adaptToMobile();
        } else {
            this.adaptToDesktop();
        }
    }

    adaptToMobile() {
        const overview = document.querySelector('.business-overview');
        if (overview) {
            overview.style.gridTemplateColumns = '1fr';
        }
    }

    adaptToDesktop() {
        const overview = document.querySelector('.business-overview');
        if (overview) {
            overview.style.gridTemplateColumns = '350px 1fr';
        }
    }

    handleScroll() {
        // Sticky header for products table
        const header = this.elements.productsTable?.querySelector('thead');
        if (header) {
            const rect = header.getBoundingClientRect();
            if (rect.top <= 0) {
                header.classList.add('sticky-header');
            } else {
                header.classList.remove('sticky-header');
            }
        }
    }

    // Utility methods
    setProductFormLoading(loading) {
        const btn = document.getElementById('saveProductBtn');
        if (!btn) return;
        
        if (loading) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Guardando...';
        } else {
            btn.disabled = false;
            btn.innerHTML = '<i class="ri-save-line me-1"></i>Guardar Cambios';
        }
    }

    showLoadingState(message = 'Cargando...') {
        // Implementation for loading state
        const loader = document.createElement('div');
        loader.id = 'pageLoader';
        loader.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
        loader.style.cssText = 'background: rgba(255,255,255,0.8); z-index: 9999;';
        loader.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary mb-3"></div>
                <div>${message}</div>
            </div>
        `;
        document.body.appendChild(loader);
    }

    hideLoadingState() {
        const loader = document.getElementById('pageLoader');
        if (loader) loader.remove();
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const instance = bootstrap.Modal.getInstance(modal);
            if (instance) instance.hide();
        }
    }

    showToast(type, message) {
        // Toast implementation (reuse from other managers)
        const toastContainer = this.getToastContainer();
        const toast = this.createToast(type, message);
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    getToastContainer() {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }

    createToast(type, message) {
        const toast = document.createElement('div');
        const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
        const icon = type === 'success' ? 'ri-check-line' : 'ri-error-warning-line';
        
        toast.className = `toast align-items-center text-white ${bgClass} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="${icon} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        return toast;
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    animateElement(element, animation = 'fadeIn', duration = 300) {
        element.style.animation = `${animation} ${duration}ms ease-in-out`;
        
        setTimeout(() => {
            element.style.animation = '';
        }, duration);
    }

    // Bulk operations
    bulkEdit() {
        const selectedIds = this.getSelectedProductIds();
        // Implementation for bulk edit
        console.log('Bulk edit:', selectedIds);
    }

    bulkDelete() {
        const selectedIds = this.getSelectedProductIds();
        // Implementation for bulk delete
        console.log('Bulk delete:', selectedIds);
    }

    clearSelection() {
        const checkboxes = this.elements.productsTable?.querySelectorAll('tbody input[type="checkbox"]');
        checkboxes?.forEach(cb => cb.checked = false);
        this.updateBulkActions(0);
    }

    getSelectedProductIds() {
        const checkedBoxes = this.elements.productsTable?.querySelectorAll('tbody input[type="checkbox"]:checked');
        return Array.from(checkedBoxes || []).map(cb => cb.closest('.product-row').dataset.productId);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const businessOverview = new BusinessOverviewManager();
    
    // Make it globally available
    window.businessOverview = businessOverview;
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BusinessOverviewManager;
}