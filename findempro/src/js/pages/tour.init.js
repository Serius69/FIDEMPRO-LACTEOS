/*
Template Name: findempro - Admin & Dashboard Template
Author: Sergio Troche
Website: https://Sergio Troche.com/
Contact: Sergio Troche@gmail.com
File: tour init js
*/

var tour = new Shepherd.Tour({
    defaultStepOptions: {
        cancelIcon: {
            enabled: true
        },

        classes: 'shadow-md bg-purple-dark',
        scrollTo: {
            behavior: 'smooth',
            block: 'center'
        }
    },
    useModalOverlay: {
        enabled: true
    },
});

if (document.querySelector('#logo-tour'))
    tour.addStep({
        title: 'Welcome Back !',
        text: 'This is Step 1',
        attachTo: {
            element: '#logo-tour',
            on: 'bottom'
        },
        buttons: [{
            text: 'Next',
            classes: 'btn btn-success',
            action: tour.next
        }]
    });
// end step 1

if (document.querySelector('#register-tour'))
    tour.addStep({
        title: 'Register your account',
        text: 'Get your Free findempro account now.',
        attachTo: {
            element: '#register-tour',
            on: 'bottom'
        },
        buttons: [{
                text: 'Back',
                classes: 'btn btn-light',
                action: tour.back
            },
            {
                text: 'Next',
                classes: 'btn btn-success',
                action: tour.next
            }
        ]
    });
// end step 2

if (document.querySelector('#login-tour'))
    tour.addStep({
        title: 'Login your account',
        text: 'Sign in to continue to findempro.',
        attachTo: {
            element: '#login-tour',
            on: 'bottom'
        },
        buttons: [{
                text: 'Back',
                classes: 'btn btn-light',
                action: tour.back
            },
            {
                text: 'Next',
                classes: 'btn btn-success',
                action: tour.next
            }
        ]
    });

// end step 3
if (document.querySelector('#getproduct-tour'))
    tour.addStep({
        title: 'Get yout Product',
        text: 'Sign in to continue to findempro.',
        attachTo: {
            element: '#getproduct-tour',
            on: 'bottom'
        },
        buttons: [{
                text: 'Back',
                classes: 'btn btn-light',
                action: tour.back
            },
            {
                text: 'Next',
                classes: 'btn btn-success',
                action: tour.next
            }
        ]
    });
// end step 4

if (document.querySelector('#thankyou-tour'))
    tour.addStep({
        title: 'Thank you !',
        text: 'Sign in to continue to findempro.',
        attachTo: {
            element: '#thankyou-tour',
            on: 'bottom'
        },
        buttons: [{
                text: 'Back',
                classes: 'btn btn-light',
                action: tour.back
            },
            {
                text: 'Thank you !',
                classes: 'btn btn-primary',
                action: tour.complete
            }
        ]
    });
// end step 5

tour.start();