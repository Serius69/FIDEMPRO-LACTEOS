/*
Template Name: findempro - Financial Decision Support System for Small and Medium-sized Enterprises (SMEs) in the Dairy Secto
Author: Sergio Troche
Website: https://Sergio Troche.com/
Contact: Sergio Troche@gmail.com
File: Modal init js
*/


var varyingcontentModal = document.getElementById('varyingcontentModal')
if (varyingcontentModal) {
    varyingcontentModal.addEventListener('show.bs.modal', function (event) {
        // Button that triggered the modal
        var button = event.relatedTarget
        // Extract info from data-bs-* attributes
        var recipient = button.getAttribute('data-bs-whatever')
        // If necessary, you could initiate an AJAX request here
        // and then do the updating in a callback.
        //
        // Update the modal's content.
        var modalTitle = varyingcontentModal.querySelector('.modal-title')
        var modalBodyInput = varyingcontentModal.querySelector('.modal-body input')

        modalTitle.textContent = 'New message to ' + recipient
        modalBodyInput.value = recipient
    })
}