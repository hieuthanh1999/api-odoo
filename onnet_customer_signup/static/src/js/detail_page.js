$(document).ready(function(){

    jQuery.validator.addMethod('valid_email', function (value) {
        var regexEmail = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
        return value.trim().match(regexEmail);
    });

    jQuery.validator.addMethod('valid_phone', function (value) {
        var regexPhone = /^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{2,3}[-\s\.]?[0-9]{2,6}$/im;
        return value.trim().match(regexPhone);
      });


    $('#detailForm').validate({
        rules: {
          'email': {
            required: true,
            email: true,
            valid_email: true
          },
          'phone': {
              required: true,
              valid_phone: true
          },
          'street': {
            required: true,
          }
        },
        messages: {
          'street': {
            required: 'Required Field',
          },
          'email': {
            required: "Invalid email",
            email: "Invalid Email Address",
            valid_email: "Invalid Email Address"
          },
          'phone': {
              required: "Required Field",
              minlength: 5,
              maxlength: 12,
              valid_phone: "Invalid phone number"

          }
        }
    })
});

// $(document).ready( function(country) {
//        var input = document.querySelector("#phone_country");
//        window.intlTelInput(input, {
//            initialCountry: 'sg',
//            utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@17.0.3/build/js/utils.js",
//        });
// })

 $(document).ready(function(){
    $('.oe_reset_password_form').submit(function(){
        $('.confirm-btn').hide()
    })
 })