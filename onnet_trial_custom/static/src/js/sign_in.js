odoo.define('onnet_trial_custom.sign_in', function (require) {
'use strict';

    $('.sign-in-custom .input-group-append .btn.btn-secondary').click(function(){
        var x = document.getElementById("password");
        if (x.type === "password") {
            x.type = "text";
        } else {
            x.type = "password";
        }
    });

    /*
    when click redirect domain
    */
    $('#redirect_domain').click(function(e) {
        e.preventDefault();
        var dcode = $(this).attr('data-value');
        var id = $(this).attr('data-id');
          $('#loading_gif_instance_done').css("visibility", "visible");
          $.ajax({
            type: 'POST',
            url: '/check-status-domain',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'url_instance': dcode, 'id': id}}),
            success: function(response) {
            if(response.result.check){
                  if(response.result.check == 1){
                        $('#loading_gif_instance_done').css("visibility", "hidden");
                        if(response.result.status === 'done'){
                            $(".done_overlay").fadeOut(500);
                            window.location = response.result.url;
                        }else if(response.result.status === 'loading') {
                             setTimeout(function(){
                                    $('#redirect_domain').trigger('click');
                                    $('#loading_gif_instance_done').css("visibility", "hidden");
                                }, 800);
                                $(".done_overlay").fadeIn();
                                $('#loading_gif_instance_done').css("visibility", "hidden");
                        }
                    }
                    else if(response.result.check == 2){
                        $('#check_status_popup').modal('show');
                        $('#loading_gif_instance_done').css("visibility", "hidden");
                        $('#check_status_popup .modal-dialog.modal-content').height('auto');
                    }
            }


            },
            error: function (error) {
                console.log(error);
            }
          });
    });
    $('#redirect_domain_invite').click(function(e) {
        e.preventDefault();
        window.location= window.location.origin + '/creating-instance/';
    });

     $('.invite-left .send_email').click(function(){
        var values = {};
        var arr_key = [];
        var arr_value = [];
        var val_name = true
        var val_email = true

        let input_name = $("input[name='name']");
        let input_email = $('input[name="email"]');
        input_name.each(function(i) {
            if($(this).val() != ''){
                var check_email = $(this).parents('.row_input').find('input[name="email"]');

                if(check_email.val() == ''){
                    check_email.addClass('is-invalid');
                    $(this).parents('.row_input').find(".error_email").removeClass('d-none');
                    $(this).parents('.row_input').find(".error_email").html('Email is empty!');
                }else{
                    arr_key.push($(this).val())
                    check_email.removeClass('is-invalid');
                    $(this).parents('.row_input').find(".error_email").addClass('d-none');
                }
            }
        });
        input_email.each(function(i) {
             if($(this).val() != ''){
                if(validateEmail($(this).val())){
                    arr_value.push($(this).val())
                    $(this).removeClass('is-invalid');
                    $(this).parents('.form__group').find(".error_email").addClass('d-none');
                    let check_name = $(this).parents('.row_input').find('input[name="name"]');
                    if(check_name.val() == ''){
                        check_name.addClass('is-invalid');
                        $(this).parents('.row_input').find(".error_name").removeClass('d-none');
                        $(this).parents('.row_input').find(".error_name").html('User is empty!');
                    }else{
                        check_name.removeClass('is-invalid');
                        $(this).parents('.row_input').find(".error_name").addClass('d-none');
                    }
                }else{
                    $(this).addClass('is-invalid');
                    $(this).parents('.form__group').find(".error_email").removeClass('d-none');
                    $(this).parents('.form__group').find(".error_email").html('Invalid email');
                }
             }
        });
        input_name.each(function(i) {
            if($(this).hasClass('is-invalid')){
              val_name = false;
                return
            }
        });
        input_email.each(function(i) {
            if($(this).hasClass('is-invalid')){
              val_email = false;
              return
            }
        });

        if(val_email == true && val_name == true){
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/send_email',
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'arr_key': arr_key, 'arr_value': arr_value}}),
                success: function (data) {
                        window.location= window.location.origin + '/creating-instance/';
                  }
            });
        }
    });

    function validateEmail($email) {
        var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
        return emailReg.test( $email );
    }
    window.onload = load_view();
    function load_view(){
        $('.invite_loadscreen_container .bottom').hide();
        if($('.invite_loadscreen_container').length>0){
          var dcode = $('#redirect_domain_hiboss').attr('data-value');
          var id =  $('#redirect_domain_hiboss').attr('data-id');
          var url_page =  $('#redirect_domain_hiboss').attr('data-url');
          $.ajax({
            type: 'POST',
            url: '/check-status-domain',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'url_instance': dcode, 'id': id}}),
            success: function(response) {
                 if(response.result.check == 1){
                    if(response.result.status === 'done'){
                        $('#loading_gif_instance').css("visibility", "hidden");
                        $(".hiboss_overlay").fadeOut(500);
                        window.location.href  = response.result.url;
                    }else if(response.result.status === 'loading') {
                        $('#loading_gif').css("visibility", "hidden");
                         setTimeout(function(){
                                $('#redirect_domain_hiboss').trigger('click');
                                $('#loading_gif_instance').css("visibility", "hidden");
                            }, 800);
                            $(".hiboss_overlay").fadeIn();
                    }
                }
                else if(response.result.check == 2){
                  $('#loading_gif').css("visibility", "hidden");
                    $('#check_status_popup_x').modal('show');
                    $('#check_status_popup_x .modal-dialog.modal-content').height('auto');
                    setTimeout(function(){
                           window.location.href = url_page
                    },1400);
                }
            },
            error: function (error) {
                console.log(error);
            }
          });
        }
     }


});

$(document).ready(function () {
     $('#redirect_domain_hiboss').click(function(e) {
        e.preventDefault();
        var dcode = $(this).attr('data-value');
        var id = $(this).attr('data-id');
        $.ajax({
            type: 'POST',
            url: '/check-status-domain',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'url_instance': dcode, 'id': id}}),
            success: function(response) {
                if(response.result){
                    if(response.result.status === 'done'){
                        $(".hiboss_overlay").fadeOut(500);
                        window.location = response.result.url;
                    }else if(response.result.status === 'loading') {
                        setTimeout(function(){
                             $('#redirect_domain_hiboss').trigger('click');
                        }, 800);
                        $(".hiboss_overlay").fadeIn();
                    }
                }else{
                    setTimeout(function(){
                            $('#redirect_domain_hiboss').trigger('click');
                    }, 800);
                    $(".hiboss_overlay").fadeIn();
               }
            },
            error: function (error) {
                console.log(error);
            }
          });
    });
});