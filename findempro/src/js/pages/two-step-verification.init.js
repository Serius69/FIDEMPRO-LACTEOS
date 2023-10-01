/*
Template Name: findempro - Admin & Dashboard Template
Author: Sergio Troche
Website: https://Sergio Troche.com/
Contact: Sergio Troche@gmail.com
File: Two step verification Init Js File
*/

// move next
function moveToNext(elem, count) {
    if (elem.value.length > 0) {
        document.getElementById("digit" + count + "-input").focus();
    }
}