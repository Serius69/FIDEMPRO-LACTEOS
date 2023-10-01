/*
Template Name: findempro - Admin & Dashboard Template
Author: Sergio Troche
Version: 3.0.0
Website: https://Sergio Troche.com/
Contact: Sergio Troche@gmail.com
File: Common Plugins Js File
*/

//Common plugins
if(document.querySelectorAll("[toast-list]") || document.querySelectorAll('[data-choices]') || document.querySelectorAll("[data-provider]")){ 
  document.writeln("<script type='text/javascript' src='https://cdn.jsdelivr.net/npm/toastify-js'></script>");
  document.writeln("<script type='text/javascript' src='/static/libs/choices.js/public/assets/scripts/choices.min.js'></script>");
  document.writeln("<script type='text/javascript' src='/static/libs/flatpickr/dist/flatpickr.min.js'></script>");    
}