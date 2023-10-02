/*
Template Name: findempro - Financial Decision Support System for Small and Medium-sized Enterprises (SMEs) in the Dairy Secto
Author: Sergio Troche
Website: https://Sergio Troche.com/
Contact: Sergio Troche@gmail.com
File: Project overview init js
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