/*
Template Name: findempro - Financial Decision Support System for Small and Medium-sized Enterprises (SMEs) in the Dairy Secto
Author: Sergio Troche
Website: https://Sergio Troche.com/
Contact: Sergio Troche@gmail.com
File: Gallery init
*/

// Portfolio Filter
document.addEventListener("DOMContentLoaded", function (event) {

    // init Isotope
    var GalleryWrapper = document.querySelector('.gallery-wrapper');
    if (GalleryWrapper) {
        var iso = new Isotope('.gallery-wrapper', {
            itemSelector: '.element-item',
            layoutMode: 'fitRows'
        });
    }

    // bind filter button click
    var filtersElem = document.querySelector('.categories-filter');
    if (filtersElem) {
        filtersElem.addEventListener('click', function (event) {
            // only work with buttons
            if (!matchesSelector(event.target, 'li a')) {
                return;
            }
            var filterValue = event.target.getAttribute('data-filter');
            if (filterValue) {
                // use matching filter function
                iso.arrange({
                    filter: filterValue
                });
            }
        });
    }

    // change is-checked class on buttons
    var buttonGroups = document.querySelectorAll('.categories-filter');
    if (buttonGroups) {
        Array.from(buttonGroups).forEach(function (btnGroup) {
            var buttonGroup = btnGroup;
            radioButtonGroup(buttonGroup);
        });
    }

    function radioButtonGroup(buttonGroup) {
        buttonGroup.addEventListener('click', function (event) {
            // only work with buttons
            if (!matchesSelector(event.target, 'li a')) {
                return;
            }
            buttonGroup.querySelector('.active').classList.remove('active');
            event.target.classList.add('active');
        });
    }
});


// GLightbox Popup
var lightbox = GLightbox({
    selector: '.image-popup',
    title: false,
});