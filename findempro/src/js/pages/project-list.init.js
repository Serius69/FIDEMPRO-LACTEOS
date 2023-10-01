/*
Template Name: findempro - Admin & Dashboard Template
Author: Sergio Troche
Website: https://Sergio Troche.com/
Contact: Sergio Troche@gmail.com
File: Project list init js
*/

// favourite btn
var favouriteBtn = document.querySelectorAll(".favourite-btn");
if (favouriteBtn) {
    Array.from(document.querySelectorAll(".favourite-btn")).forEach(function (item) {
        item.addEventListener("click", function (event) {
            this.classList.toggle("active");
        });
    });
}

// Remove product from cart
var removeProduct = document.getElementById('removeProjectModal')
if (removeProduct) {
    removeProduct.addEventListener('show.bs.modal', function (e) {
        document.getElementById('remove-project').addEventListener('click', function (event) {
            e.relatedTarget.closest('.project-card').remove();
            document.getElementById("close-modal").click();
        });
    });
}