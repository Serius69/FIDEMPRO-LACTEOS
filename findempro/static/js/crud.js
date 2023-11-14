function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
function showModal(modalId) {
    $(`#${modalId}`).modal('show');
}
function hideModal(modalId) {
    $(`#${modalId}`).modal('hide');
    window.location.reload();
}
$(document).ready(function () {
    $(".edit-product").click(function () {
        var productId = $(this).data("product-id");
        $.ajax({
            url: "/product/get_product_details/" + productId + "/",
            method: "GET",
            success: function (data) {
                $("#editProductModal #name").val(data.name);
                $("#editProductModal #type").val(data.type);
                $("#editProductModal #fk_business").val(data.fk_business);
                $("#editProductModal #description").val(data.description);                
                var productForm = document.getElementById('editproductForm');
                productForm.classList.remove('was-validated');
            },
            error: function (error) {
                console.log("Error al obtener los detalles del producto:", error);
            }
        });
    });
});
$(document).ready(function () {
    $('#apply-filters').on('click', function () {
        var selectedBusiness = $('#business-select').val();
        var selectedCategory = $('#category-select').val();

        $('.product-card').each(function () {
            var business = $(this).data('business');
            var category = $(this).data('category');
            if ((selectedBusiness === 'All' || selectedBusiness == business) &&
                (selectedCategory === 'All' || selectedCategory == category)) {
                $(this).show(); 
            } else {
                $(this).hide(); 
            }
        });
    });
});
$(document).ready(function () {
$('#add-selected-products').on('click', function () {
    $('#product-table tbody input[type="checkbox"]').each(function () {
        if ($(this).prop('checked')) {
            // Si la casilla de verificación está marcada, agregar la fila correspondiente a la tabla
            const $row = $(this).closest('tr');
            $('#product-table').append($row.clone());
        }
    });
});
});
document.addEventListener("DOMContentLoaded", function () {
    const deleteButtons = document.querySelectorAll(".delete-product-btn");
    deleteButtons.forEach((button) => {
        button.addEventListener("click", function () {
            const url = button.getAttribute("data-href");
            if (url) {
                window.location.href = url;
            }
        });
    });
});
$('#variableForm').on('submit', async function (event) {
    event.preventDefault();
    try {
        const formData = new FormData(this);
        const response = await fetch('{% url "variable:variable.create" %}', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
        if (response.ok) {
            hideModal(addVariable);
        } else {
            const responseData = await response.json();
            const errorModalContent = document.getElementById('errorModalContent');
            if (responseData.errors && responseData.errors.name) {
                const errorMessagesDiv = document.getElementById('error-messages');
                if (errorModalContent) {
                    errorModalContent.innerHTML = ''; 
                    for (const field in responseData.errors) {
                        const errorsForField = responseData.errors[field];
                        errorsForField.forEach((error) => {
                            errorMessagesDiv.innerHTML += `<p>${error}</p>`;
                        });
                    }
                }
            }
            $('#errorModal').modal('show');
        }
    } catch (error) {
        console.error(error);
    }
});
$('#productForm').on('submit', async function (event) {
    event.preventDefault();
    try {
        const formData = new FormData(this);
        const response = await fetch('{% url "product:product.create" %}', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
        if (response.ok) {
            hideModal('addBusiness');
        } else {
            // Handle errors and display them to the user
            const responseData = await response.json();
            if (responseData.errors && responseData.errors.name) {
                // Display the specific error message for the "name" field
                const errorDiv = document.getElementById('error-name'); // Adjust the element ID as needed
                if (errorDiv) {
                    errorDiv.textContent = responseData.errors.name[0];
                }
            }
        }
    } catch (error) {
        // Handle network or other errors
        console.error(error);
    }
});// Get references to the input field and the search icon
const searchInput = document.getElementById('searchInput');
const searchIcon = document.querySelector('.search-icon');

searchIcon.addEventListener('click', () => {
    performSearch();
});
searchInput.addEventListener('keyup', (event) => {
    if (event.key === 'Enter') {
        performSearch();
    }
});
function performSearch() {
    const searchTerm = searchInput.value;
    alert('Performing search for: ' + searchTerm);
    // Replace the alert with your search logic, e.g., making an API request.
}

$(document).ready(function () {
    // Obtén la cantidad de variables desde tu variable de plantilla, por ejemplo:
    var numberOfVariables = parseInt("{{ product.variables.count|default:'0' }}");

    // Calcula el valor de la barra de progreso (entre 0 y 100)
    var progressValue = (numberOfVariables / MAX_VARIABLES) * 100; // MAX_VARIABLES es el valor máximo posible

    // Actualiza el valor de la barra de progreso
    $('#progress-bar').attr('aria-valuenow', progressValue);
    $('#progress-bar').css('width', progressValue + '%');
    $('#progress-bar').text(progressValue.toFixed(2) + '%'); // Opcional: muestra el valor en el centro de la barra

    // También puedes cambiar el color de la barra de progreso según el valor, si es necesario
    if (progressValue < 30) {
        $('#progress-bar').removeClass('bg-success').addClass('bg-danger');
    } else if (progressValue < 70) {
        $('#progress-bar').removeClass('bg-danger').addClass('bg-warning');
    }
});
$('#variableForm').on('submit', async function (event) {
    event.preventDefault();
    try {
        const formData = new FormData(this);
        const response = await fetch('{% url "variable:variable.create" %}', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        });
        if (response.ok) {
            hideModal('addVariable');
        } else {
            // Handle errors and display them to the user
            const responseData = await response.json();
            const errorModalContent = document.getElementById('errorModalContent'); // Use the correct ID
            if (responseData.errors && responseData.errors.name) {
                // Display the specific error message for the "name" field
                const errorMessagesDiv = document.getElementById('error-messages');
                if (errorModalContent) {
                    errorModalContent.innerHTML = '';  // Clear previous error messages

                    // Iterate through errors and display them
                    for (const field in responseData.errors) {
                        const errorsForField = responseData.errors[field];
                        errorsForField.forEach((error) => {
                            errorMessagesDiv.innerHTML += `<p>${error}</p>`;
                        });
                    }
                }
            }
            $('#errorModal').modal('show');
        }
    } catch (error) {
        // Handle network or other errors
        console.error(error);
    }
});
    $('#businessForm').on('submit', async function (event) {
        event.preventDefault();
    
        const nameInput = $('#name');
        const nameValue = nameInput.val();
    
        if (nameValue.trim() === '') {
            // El campo "name" está vacío, muestra un mensaje de error
            const errorDiv = document.getElementById('error-name'); // Asegúrate de que el elemento con ID 'error-name' exista
            if (errorDiv) {
                errorDiv.textContent = 'Please enter a business name.';
            }
            return; // Detener el envío del formulario
        }
    
        // Si pasa la validación, continúa con el envío de datos al servidor
        try {
            const formData = new FormData(this);
            const response = await fetch('{% url "business:business.create" %}', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                },
            });
    
            if (response.ok) {
                hideModal('addBusiness'); 
                window.location.reload();
            } else {
                // Handle other errors here, if necessary
                // ...
            }
        } catch (error) {
            // Handle network or other errors
            console.error(error);
        }
    });

    // Function to get the CSRF token from cookies (assuming Django uses cookies)
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }