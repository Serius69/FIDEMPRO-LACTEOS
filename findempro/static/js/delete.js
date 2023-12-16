const formUtils2 = {
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
        console.log('Form submission initiated');
        try {
            const formData = new FormData(document.getElementById(formId));
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formUtils2.getCookie('csrftoken'),
                },
            });

            if (response.ok) {
                successCallback();
            } else {
                throw new Error('Request failed');
            }
        } catch (error) {
            // Handle network or other errors
            console.error('Form submission error:', error);
        }
    },
};

$('#removeBusinessModal').on('show.bs.modal', function (event) {
    console.log('Modal shown event triggered');
    var businessId = $('#delete-business-link').data('variable-id');
    var modal = $(this);
    var deleteForm = modal.find('#deleteBusinessForm');
    var deleteFormUrlInput = modal.find('#delete-business-url');
    var url = deleteFormUrlInput.val().replace('0', businessId);
    deleteForm.attr('action', url);
});

$('#removeProductModal').on('show.bs.modal', function (event) {
    var productId = $('#delete-product-link').data('variable-id');
    var modal = $(this);
    var deleteForm = modal.find('#deleteProductForm');
    var deleteFormUrlInput = modal.find('#delete-product-url');
    var url = deleteFormUrlInput.val().replace('0', productId);
    deleteForm.attr('action', url);
});

$('#removeAreaModal').on('show.bs.modal', function (event) {
    var businessId = $('#delete-area-link').data('variable-id');
    var modal = $(this);
    var deleteForm = modal.find('#deleteAreaForm');
    var deleteFormUrlInput = modal.find('#delete-area-url');
    var url = deleteFormUrlInput.val().replace('0', businessId);
    deleteForm.attr('action', url);
});

$('#removeVariableModal').on('show.bs.modal', function (event) {
    console.log('Modal shown event triggered');
    var variableId = $('#delete-variable-link').data('variable-id');
    var modal = $(this);
    var deleteForm = modal.find('#deleteVariableForm');
    var deleteFormUrlInput = modal.find('#delete-variable-url');
    var url = deleteFormUrlInput.val().replace('0', variableId);
    deleteForm.attr('action', url);
    console.log('Button click event configured');
});

const modelActions2 = {
    delete: async (model, id) => {
        try {
            const response = await fetch(`/${model}/${id}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': formUtils2.getCookie('csrftoken'),
                },
            });
            return await response.json();
        } catch (error) {
            console.error(`Error deleting ${model}:`, error);
            return null;
        }
    },
};
