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

    showError: (message) => {
        var toastHtml = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="mr-auto">Error</strong>
                <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>`;
        var toastElement = $(toastHtml);
        $('body').append(toastElement);
        toastElement.toast({ delay: 5000 });
        toastElement.toast('show');
    },
};
handleFormSubmission = async (formId, url, successCallback) => {
    try {
        const formData = new FormData(document.getElementById(formId));
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formUtils.getCookie('csrftoken'),
            }
        });
        if (response.ok) {
            // ...
        } else {
            throw new Error('Request failed');
        }
    } catch (error) {
        console.error(error);
        formUtils.showError('An error occurred while submitting the form. Please try again.');
    }
};
const handleSubmission = async (formId, url, modalId) => {
    try {
        const formData = new FormData(document.getElementById(formId));
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': formUtils.getCookie('csrftoken'),
            }
        });
        if (response.ok) {
            formUtils.hideModal(modalId);
        } else {
            throw new Error('Request failed');
        }
    } catch (error) {
        console.error(error);
        debugger; 
    }
};
const formHandlers = {
    handleFormSubmission: async (formId, id, type) => {
        const url = id ? `/${type}/${id}/update/` : `/${type}/create/`;
        await handleFormSubmission(formId, url, () => formUtils.hideModal(`addOrUpdate${type.charAt(0).toUpperCase() + type.slice(1)}`));
    },

    handleBusinessSubmission: async () => {
        const businessId = $('#business_id').val();
        await formHandlers.handleFormSubmission('businessForm', businessId, 'business');
    },
    
    handleProductSubmission: async () => {
        const productId = $('#product_id').val();
        await formHandlers.handleFormSubmission('productForm', productId, 'product');
    },

    handleAreaSubmission: async () => {
        const areaId = $('#area_id').val();
        await formHandlers.handleFormSubmission('areaForm', areaId, 'area');
    },
    
    handleVariableSubmission: async () => {
        const variableId = $('#variable_id').val();
        await formHandlers.handleFormSubmission('variableForm', variableId, 'variable');
    },
    
    handleEquationSubmission: async () => {
        const equationId = $('#equation_id').val();
        await formHandlers.handleFormSubmission('equationForm', equationId, 'equation');
    },    
};

const formIds = ['businessForm', 'productForm', 'areaForm', 'variableForm', 'equationForm'];

formIds.forEach(formId => {
    $(`#${formId}`).on('submit', async (event) => {
        event.preventDefault();
        const type = formId.replace('Form', '');
        await formHandlers[`handle${type.charAt(0).toUpperCase() + type.slice(1)}Submission`]();
    });
});

async function loadDetailsAndShowModal(model, id, modalId) {
    try {
        const details = await modelActions.getDetails(model, id);
        $(`#${model}_id`).val(id);
        $('#name').val(details.name);
        const baseUrl = '/media';
        const imageSrcInput = $('#image_src');
        imageSrcInput.val(''); 
        setModalTitle($(`#${modalId}`), $(`#${model}_id`), model);
        loadImageAndDetails(model, details, baseUrl, imageSrcInput);
        $(`#${modalId}`).modal('show');
    } catch (error) {
        console.error(`Error al cargar detalles del ${model}:`, error);
        formUtils.showError(`Error al cargar detalles del ${model}: ${error.message}`);
    }
}

function loadImageAndDetails(model, details, baseUrl, imageSrcInput) {
    const imageUrl = `${baseUrl}${details.image_src}`;
    $('#logo-img').attr('src', imageUrl);
    $('#image_src').val(details.image_src);
    if (details.image_src) {
        imageSrcInput.data('existing-image', details.image_src);  // Almacenar la URL de la imagen existente en un atributo de datos
        loadImagePreview(details.image_src);
    }
    switch (model) {
        case 'business':
            $('#id').val(details.id);
            $('#type').val(details.type);
            $('#location').val(details.location);
            break;
        case 'product':
            $('#type').val(details.type);
            $('#description').val(details.description);
            $('#fk_business').val(details.fk_business);
            break;
        case 'area':
            $('#description').val(details.description);
            break;
        case 'variable':
            $('#initials').val(details.initials);
            $('#unit').val(details.unit);
            $('#description').val(details.description);
            break;
        case 'equation':
            $('#expression').val(details.expression);
            $('#fk_variable1').val(details.fk_variable1);
            $('#fk_variable2').val(details.fk_variable2);
            $('#fk_variable3').val(details.fk_variable3);
            $('#fk_variable4').val(details.fk_variable4);
            $('#fk_variable5').val(details.fk_variable5);
            $('#location').val(details.location);
            break;
        default:
            break;
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
$('#image_src').on('change', function () {
    const imageSrcInput = $(this);
    const existingImage = imageSrcInput.data('existing-image');
    const newImage = imageSrcInput[0].files[0];

    // Mostrar la vista previa de la nueva imagen
    if (newImage) {
        const reader = new FileReader();
        reader.onload = function (e) {
            loadImagePreview(e.target.result);
        };
        reader.readAsDataURL(newImage);
    } else if (existingImage) {
        loadImagePreview(existingImage);
    } else {
        loadImagePreview('');
    }
});
function setModalEvent(modalId, deleteLinkId, deleteFormId, deleteFormUrlId, variableId) {
    $(modalId).on('show.bs.modal', function (event) {
        var modal = $(this);
        var deleteForm = modal.find(deleteFormId);
        var deleteFormUrlInput = modal.find(deleteFormUrlId);
        var variableId = $(deleteLinkId).data('variable-id');
        var url = deleteFormUrlInput.val().replace('0', variableId);
        console.log('Setting delete form action to:', url); 
        deleteForm.attr('action', url);
    });
}
setModalEvent('#removeBusinessModal', '#delete-business-link', '#deleteBusinessForm', 
'#delete-business-url', $('#delete-business-link').data('variable-id'));
setModalEvent('#removeProductModal', '#delete-product-link', '#deleteProductForm', 
'#delete-product-url', $('#delete-product-link').data('variable-id'));
setModalEvent('#removeAreaModal', '#delete-area-link', '#deleteAreaForm', 
'#delete-area-url', $('#delete-area-link').data('variable-id'));
setModalEvent('#removeVariableModal', '#delete-variable-link', '#deleteVariableForm', 
'#delete-variable-url', $('#delete-variable-link').data('variable-id'));
setModalEvent('#removeEquationModal', '#delete-equation-link', '#deleteEquationForm', 
'#delete-equation-url', $('#delete-equation-link').data('variable-id'));
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
                method: 'PUT',
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
            const response = await fetch(`/${model}/delete/${id}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': formUtils.getCookie('csrftoken')
                },
            });
    
            if (response.ok) {
                console.log(`${model} deleted successfully`);
            } else {
                throw new Error(`Error deleting ${model}`);
            }
        } catch (error) {
            console.error(`Error deleting ${model}:`, error);
        }
    },
    create: async (model, data) => {
        try {
            const response = await fetch(`/${model}/create/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': formUtils.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error(`Error creating ${model}:`, error);
            return null;
        }
    },

    update: async (model, id, data) => {
        try {
            const response = await fetch(`/${model}/${id}/update/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': formUtils.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error(`Error updating ${model}:`, error);
            return null;
        }
    },
};





function setModalTitle(modal, idInput, modalName) {
    if (!modal || !idInput || !modalName) {
        throw new Error('Modal, input o nombre del modal no especificados');
    }

    const nameMapping = {
        'business': 'negocio',
        'product': 'producto',
        'variable': 'variable',
        'equation': 'ecuación',
        'area': 'área'
    };

    modalName = nameMapping[modalName] || modalName;

    const modalTitle = modal.find('.modal-title');
    const action = idInput.val() ? 'Actualizar' : 'Añadir';

    modalTitle.text(`${action} ${modalName}`);
}