/*
Template Name: findempro - Financial Decision Support System for Small and Medium-sized Enterprises (SMEs) in the Dairy Secto
Author: Sergio Troche
Website: https://Sergio Troche.com/
Contact: Sergio Troche@gmail.com
File: Ecommerce product Details Js File
*/

var productNavSlider = new Swiper(".product-nav-slider", {
	loop: false,
	spaceBetween: 10,
	slidesPerView: 4,
	freeMode: true,
	watchSlidesProgress: true,
});
var productThubnailSlider = new Swiper(".product-thumbnail-slider", {
	loop: false,
	spaceBetween: 24,
	navigation: {
		nextEl: ".swiper-button-next",
		prevEl: ".swiper-button-prev",
	},
	thumbs: {
		swiper: productNavSlider,
	},
});