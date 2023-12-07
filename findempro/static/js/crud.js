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
                    'X-CSRFToken': utils.getCookie('csrftoken'),
                },
            });

            if (response.ok) {
                successCallback();
            } else {
                // Handle errors and display them to the user
                // ...
            }
        } catch (error) {
            // Handle network or other errors
            console.error(error);
        }
    },
};

const modelActions = {
    // Funciones comunes para operaciones CRUD en modelos
    getDetails: async (model, id) => {
        try {
            const response = await fetch(`/${model}/get_details/${id}/`);
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
            const response = await fetch(`/${model}/delete/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            return await response.json();
        } catch (error) {
            console.error(`Error al eliminar ${model}:`, error);
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
// Manejo de formularios específicos
const businessForm = {
    handleSubmission: async () => {
        await formUtils.handleFormSubmission('businessForm', '/business/create', () => formUtils.hideModal('addBusiness'));
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
