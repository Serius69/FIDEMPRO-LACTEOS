function applyFilter(elementSelector, filterValue) {
    $(elementSelector).each(function() {
        var filterElement = $(this).find('.badge-primary, .job-type'); // Puedes ajustar según tus necesidades

        if (filterValue === 'All' || filterElement.text().trim() === filterValue) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

$(document).ready(function() {
    // Manejar el cambio en cualquier select con la clase 'filter-select'
    $('.filter-select').change(function() {
        var selectedValue = $(this).val();
        var targetElementSelector = $(this).data('target-element');

        applyFilter(targetElementSelector, selectedValue);
    });

    // Manejar el envío del formulario (si es necesario)
    $('form').submit(function(event) {
        // Evitar la recarga de la página al enviar el formulario
        event.preventDefault();

        // Realizar otras acciones de envío del formulario si es necesario
        // ...

    });
});