const formUtils = {
    getCookie: (name) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        return parts.length === 2 ? parts.pop().split(';').shift() : null;
    },
    
    showModal: (modalId) => {
        $(`#${modalId}`).modal('show');
    },
    
    hideModal: (modalId) => {
        $(`#${modalId}`).modal('hide');
        window.location.reload();
    },

    handleFormSubmission: async (formId, url, successCallback) => {
        try {
            const formData = new FormData(document.getElementById(formId));
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formUtils.getCookie('csrftoken'),
                },
            });

            if (response.ok) {
                successCallback();
            } else {
                throw new Error('Request failed');
            }
        } catch (error) {
            // Handle network or other errors
            console.error(error);
        }
    },
};
// Manejo de formularios específicos
const businessForm = {
    handleSubmission: async () => {
        await formUtils.handleFormSubmission('businessForm', '/business/create/', () => formUtils.hideModal('addOrUpdateBusiness'));
    },
};
const productForm = {
    handleSubmission: async () => {
        await formUtils.handleFormSubmission('productForm', '/product/create/', () => formUtils.hideModal('addOrUpdateProduct'));
    },
};
const variableForm = {
    handleSubmission: async () => {
        await formUtils.handleFormSubmission('variableForm', '/variable/create/', () => formUtils.hideModal('addOrUpdateVariable'));
    },
};
const equationForm = {
    handleSubmission: async () => {
        await formUtils.handleFormSubmission('equationForm', '/equation/create/', () => formUtils.hideModal('addOrUpdateEquation'));
    },
};
const areaForm = {
    handleSubmission: async () => {
        await formUtils.handleFormSubmission('areaForm', '/area/create/', () => formUtils.hideModal('addOrUpdateArea'));
    },
};

function setModalTitle(modal, idInput, modalName) {
    if (!modal || !idInput || !modalName) {
        throw new Error('Modal, input o nombre del modal no especificados');
    }
    if (modalName === 'business') {
        modalName = 'negocio';
    }else if (modalName === 'product') {
        modalName = 'producto';
    }else if (modalName === 'variable') {
        modalName = 'variable';
    }else if (modalName === 'equation') {
        modalName = 'ecuación';
    }else if (modalName === 'area') {
        modalName = 'área';
    }
    var modalTitle = modal.find('.modal-title');
    if (idInput.val()) {
        modalTitle.text(`Actualizar ${modalName}`);
    } else {
        modalTitle.text(`Añadir ${modalName}`);
    }
}
async function loadDetailsAndShowModal(model, id, modalId) {
    try {
        const details = await modelActions.getDetails(model, id);
        $(`#${model}_id`).val(id);
        $('#name').val(details.name);
        const baseUrl = '/media';
        const imageSrcInput = $('#image_src');
        imageSrcInput.val(''); 
        setModalTitle($(`#${modalId}`), $(`#${model}_id`), model);
        switch (model) {
            case 'business':
                $('#id').val(details.id);
                $('#type').val(details.type);
                $('#location').val(details.location);
                console.log(details.type);
                console.log(details.id);
                const imageUrl2 = `${baseUrl}${details.image_src}`;
                $('#logo-img').attr('src', imageUrl2);
                $('#image_src').val(details.image_src);
                if (details.image_src) {
                    imageSrcInput.data('existing-image', details.image_src);  // Almacenar la URL de la imagen existente en un atributo de datos
                    loadImagePreview(details.image_src);
                }
                break;
            case 'product':
                console.log(details.type);
                console.log(details.fk_business);
                const imageUrl1 = `${baseUrl}${details.image_src}`;
                $('#logo-img').attr('src', imageUrl1);
                $('#type').val(details.type);
                $('#description').val(details.description);
                $('#image_src').val(details.image_src);
                $('#fk_business').val(details.fk_business);
                if (details.image_src) {
                    imageSrcInput.data('existing-image', details.image_src);  // Almacenar la URL de la imagen existente en un atributo de datos
                    loadImagePreview(details.image_src);
                }
                break;
            case 'area':
                $('#description').val(details.description);
                console.log(details.fk_product);
                const imageUrl3 = `${baseUrl}${details.image_src}`;
                $('#logo-img').attr('src', imageUrl3);
            
                // Crear un nuevo input de tipo file
                var newInput = $('<input type="file" class="form-control d-none" accept="image/png, image/jpeg" name="image_src"/>');
            
                // Copiar los atributos necesarios del input existente al nuevo input
                newInput.prop('files', $('#image_src').prop('files'));
                newInput.data('existing-image', details.image_src);
            
                // Reemplazar el input existente con el nuevo input
                $('#image_src').replaceWith(newInput);
            
                // Limpiar el input (opcional)
                newInput.val('');
            
                if (details.image_src) {
                    loadImagePreview(details.image_src);
                }
                break;
            case 'variable':
                console.log(details.unit);
                $('#initials').val(details.initials);
                $('#unit').val(details.unit);
                $('#description').val(details.description);
                const imageUrl = `${baseUrl}${details.image_src}`;
                $('#logo-img').attr('src', imageUrl);
                $('#image_src').val(details.image_src);
                if (details.image_src) {
                    imageSrcInput.data('existing-image', details.image_src);  // Almacenar la URL de la imagen existente en un atributo de datos
                    loadImagePreview(details.image_src);
                }
                break;
            case 'equation':
                $('#expression').val(details.expression);
                $('#fk_variable1').val(details.fk_variable1);
                $('#fk_variable2').val(details.fk_variable2);
                $('#fk_variable3').val(details.fk_variable3);
                $('#fk_variable4').val(details.fk_variable4);
                $('#fk_variable5').val(details.fk_variable5);
                $('#location').val(details.location);
                $('#image_src').val(details.image_src);
                break;
            default:
                break;
        }
        $(`#${modalId}`).modal('show');
    } catch (error) {
        console.error(`Error al cargar detalles del ${model}:`, error);
    }
}

async function loadBusinessDetails(businessId) {
    await loadDetailsAndShowModal('business', businessId, 'addOrUpdateBusiness');
}

async function loadProductDetails(productId) {
    await loadDetailsAndShowModal('product', productId, 'addOrUpdateProduct');
}

async function loadAreaDetails(areaId) {
    await loadDetailsAndShowModal('area', areaId, 'addOrUpdateArea');
}

async function loadVariableDetails(variableId) {
    await loadDetailsAndShowModal('variable', variableId, 'addOrUpdateVariable');
}

async function loadEquationDetails(equationId) {
    await loadDetailsAndShowModal('equation', equationId, 'addOrUpdateEquation');
}

function loadImagePreview(imageSrc) {
    const imagePreview = $('#logo-img');
    imagePreview.attr('src', imageSrc);
}

// Event listener para el cambio en el input de la imagen
$('#image_src').on('change', function () {
    const imageSrcInput = $(this);
    const existingImage = imageSrcInput.data('existing-image');
    
    // Obtener la nueva imagen seleccionada
    const newImage = imageSrcInput[0].files[0];

    // Mostrar la vista previa de la nueva imagen
    if (newImage) {
        const reader = new FileReader();
        reader.onload = function (e) {
            loadImagePreview(e.target.result);
        };
        reader.readAsDataURL(newImage);
    } else if (existingImage) {
        // Si no se selecciona una nueva imagen pero hay una imagen existente, mostrar la imagen existente
        loadImagePreview(existingImage);
    } else {
        // Limpiar la vista previa si no hay nueva imagen ni imagen existente
        loadImagePreview('');
    }
});
function setModalEvent(modalId, deleteLinkId, deleteFormId, deleteFormUrlId, variableId) {
    $(modalId).on('show.bs.modal', function (event) {
        var modal = $(this);
        var deleteForm = modal.find(deleteFormId);
        var deleteFormUrlInput = modal.find(deleteFormUrlId);
        var url = deleteFormUrlInput.val().replace('0', variableId);
        deleteForm.attr('action', url);
    });
}
// Usage:
setModalEvent('#removeBusinessModal', '#delete-business-link', '#deleteBusinessForm', '#delete-business-url', $('#delete-business-link').data('variable-id'));
setModalEvent('#removeProductModal', '#delete-product-link', '#deleteProductForm', '#delete-product-url', $('#delete-product-link').data('variable-id'));
setModalEvent('#removeAreaModal', '#delete-area-link', '#deleteAreaForm', '#delete-area-url', $('#delete-area-link').data('variable-id'));
setModalEvent('#removeVariableModal', '#delete-variable-link', '#deleteVariableForm', '#delete-variable-url', $('#delete-variable-link').data('variable-id'));
setModalEvent('#removeEquationModal', '#delete-equation-link', '#deleteEquationForm', '#delete-equation-url', $('#delete-equation-link').data('variable-id'));
const modelActions = {
    getDetails: async (model, id) => {
        try {
            console.log(model);
            if (!model || !id) {
                throw new Error(`Error al obtener detalles de ${model}: modelo o ID no especificados`);
            }
            let response;
            if (model === 'area') {
                response = await fetch(`/product/${model}/get_details/${id}/`);
            } else if (model === 'equation') {
                response = await fetch(`/variable/${model}/get_details/${id}/`);
            } else {
                response = await fetch(`/${model}/get_details/${id}/`);
            }
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error(`Error al obtener detalles de ${model}: respuesta no es JSON`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Error al obtener detalles de ${model}:`, error);
            return null;
        }
    },

    edit: async (model, id, data) => {
        try {
            const response = await fetch(`/${model}/edit/${id}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error(`Error al editar ${model}:`, error);
            return null;
        }
    },

    delete: async (model, id) => {
        try {
            const response = await fetch(`/${model}/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
            });
            return await response.json();
        } catch (error) {
            console.error(`Error deleting ${model}:`, error);
            return null;
        }
    },
    

    add: async (model, data) => {
        try {
            const response = await fetch(`/${model}/add/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error(`Error al agregar ${model}:`, error);
            return null;
        }
    },
};

// Event listeners
$(document).ready(() => {
    // Configurar event listeners según tus necesidades
    $('#businessForm').on('submit', async (event) => {
        event.preventDefault();
        await businessForm.handleSubmission();
    });

    $('#productForm').on('submit', async (event) => {
        event.preventDefault();
        await productForm.handleSubmission();
    });

    $('#variableForm').on('submit', async (event) => {
        event.preventDefault();
        await variableForm.handleSubmission();
    });

    $('#equationForm').on('submit', async (event) => {
        event.preventDefault();
        await productForm.handleSubmission();
    });

    $('#equationForm').on('submit', async (event) => {
        event.preventDefault();
        await productForm.handleSubmission();
    });
});
