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
        await formUtils.handleFormSubmission('productForm', '/product/create', () => formUtils.hideModal('addProduct'));
    },
};
const variableForm = {
    handleSubmission: async () => {
        await formUtils.handleFormSubmission('variableForm', '/variable/create', () => formUtils.hideModal('addVariable'));
    },
};
const equationForm = {
    handleSubmission: async () => {
        await formUtils.handleFormSubmission('equationForm', '/equation/create', () => formUtils.hideModal('addEquation'));
    },
};
const areaForm = {
    handleSubmission: async () => {
        await formUtils.handleFormSubmission('areaForm', '/area/create', () => formUtils.hideModal('addArea'));
    },
};
async function loadDetailsAndShowModal(model, id, modalId) {
    try {
        const details = await modelActions.getDetails(model, id);
        $(`#${model}_id`).val(id);
        $('#name').val(details.name);
        const baseUrl = '/media';
        const imageSrcInput = $('#image_src');
        imageSrcInput.val(''); // Limpiar el input de la imagen
        // Manejar campos específicos de cada modelo
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
                $('#fk_area').val(details.fk_area);
                $('#description').val(details.description);
                console.log(details.type);
                console.log(details.fk_business);
                const imageUrl3 = `${baseUrl}${details.image_src}`;
                $('#logo-img').attr('src', imageUrl3);
                $('#image_src').val(details.image_src);
                if (details.image_src) {
                    imageSrcInput.data('existing-image', details.image_src);  // Almacenar la URL de la imagen existente en un atributo de datos
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
                $('#initials').val(details.initials);
                $('#description').val(details.description);
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
$('#removeBusinessModal').on('show.bs.modal', function (event) {
    // Retrieve the business ID from the data attribute of the delete-business-link element
    var businessId = $('#delete-business-link').data('variable-id');
    
    // Select modal elements
    var modal = $(this);
    var deleteForm = modal.find('#deleteBusinessForm');
    var deleteFormUrlInput = modal.find('#delete-business-url');

    // Construct the URL for the delete action, replacing '0' with the actual business ID
    var url = deleteFormUrlInput.val().replace('0', businessId);

    // Set the constructed URL as the action attribute of the form
    deleteForm.attr('action', url);
});
$('#removeProductModal').on('show.bs.modal', function (event) {
    // Retrieve the business ID from the data attribute of the delete-business-link element
    var productId = $('#delete-product-link').data('variable-id');
    
    // Select modal elements
    var modal = $(this);
    var deleteForm = modal.find('#deleteProductForm');
    var deleteFormUrlInput = modal.find('#delete-product-url');

    // Construct the URL for the delete action, replacing '0' with the actual business ID
    var url = deleteFormUrlInput.val().replace('0', productId);

    // Set the constructed URL as the action attribute of the form
    deleteForm.attr('action', url);
});
$('#removeAreaModal').on('show.bs.modal', function (event) {
    // Retrieve the business ID from the data attribute of the delete-business-link element
    var businessId = $('#delete-business-link').data('variable-id');
    
    // Select modal elements
    var modal = $(this);
    var deleteForm = modal.find('#deleteBusinessForm');
    var deleteFormUrlInput = modal.find('#delete-business-url');

    // Construct the URL for the delete action, replacing '0' with the actual business ID
    var url = deleteFormUrlInput.val().replace('0', businessId);

    // Set the constructed URL as the action attribute of the form
    deleteForm.attr('action', url);
});
$('#removeVariableModal').on('show.bs.modal', function (event) {
    var variableId = $('#delete-variable-link').data('variable-id');
    var modal = $(this);
    var deleteForm = modal.find('#deleteVariableForm');
    var deleteFormUrlInput = modal.find('#delete-variable-url');
    var url = deleteFormUrlInput.val().replace('0', variableId);
    deleteForm.attr('action', url);
});
const modelActions = {
    // Funciones comunes para operaciones CRUD en modelos
    getDetails: async (model, id) => {
        try {
            const response = await fetch(`/${model}/get_details/${id}/`);
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
