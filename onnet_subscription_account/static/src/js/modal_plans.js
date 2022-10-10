$(document).ready(function () {
    var country_check = $('input[name="country_check"]').val();
    check_hidden_state(country_check);

    function call_phone(country) {
        var input = document.querySelector("#phone_partner");
        window.intlTelInput(input, {
            initialCountry: country,
            utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@17.0.3/build/js/utils.js",
        });
 }
    function get_addons_click(){
        var list_2= [];
        $("input[name='checkbox_addons']:checked:enabled").each(function () {
            list_2.push($(this).val());
        });
        $("input[name='list_addons_buy']").val(list_2);
    }
    $('.o_portal_wrap').on('input', '#numPlans', function() {
         var user_quantity = $(this).val()
         $("input[name='quantity_trial']").val(user_quantity);
         step_five(5, user_quantity)
    });

    $(function () { // to ensure that code evaluates on page load
    $('.o_portal_wrap').on("click", '.quantity-down', function(){
        var qty = $(this).closest("div.quantity").find("input");
        var qty_min = $(this).closest("div.quantity").find("input").attr('min');
        const check = Number(qty_min)
        var value = Number(qty.val());
            if(value > check) {
                value = value - 1;
            }
        qty.attr('value', value);

        $("input[name='quantity_trial']").val(value);
         step_five(5, value)
    });
    $('.o_portal_wrap').on("click", '.quantity-up', function(){
        var qty = $(this).closest("div.quantity").find("input");
        var value = Number(qty.val());
        value = value + 1;
            qty.attr('value', value);
        $("input[name='quantity_trial']").val(value);
        step_five(5, value)
    });
});
    function get_addons_upgrade(){
        var list_2= [];
        $("input[name='checkbox_addons']:checked:enabled").each(function () {
            list_2.push($(this).val());
        });
        $("input[name='list_addons']").val(list_2);
    }
     $('.o_portal_wrap').on('change','#pricelist_id', function() {
        $('input[name="is_pricelist"]').attr('value', $(this).val());
     });
     $('#hidden_subscription_modal').hide();
     $(".active_subscription_status").on('click', function () {
          jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/buy_pricelist',
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'id_sub': $(this).attr('data-id'), 'stage': $(this).attr('data-stage'), 'id_order': $(this).attr('data-order')}}),
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{
                        if(data.result.check_active == 2){
                            window.location= window.location.origin + '/plans/payment';
                        }else{
                            $('input[name="is_pricelist"]').attr('value', data.result.month_id);
                            $('#hidden_subscription_modal .modal-dialog.modal-content').height(300);
                            $('.content_data').html(data.result.html);
                            $('#next_step_account').attr('data-step',4);
                            $('#hidden_subscription_modal').modal('show');
                        }
                    }
                },
           });
     });

     $('#next_step_account').click(function () {
        let step_click = parseFloat($(this).attr('data-step'));
        let id_sub = $(this).attr('data-id');
        let total = $("input[name='total']").val();
         if(step_click==4){
             jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/add-addons',
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data':{'list_addons': $('input[name="list_addons_buy"]').val()}, 'is_pricelist':$('input[name="is_pricelist"]').val()}}),
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{
                        $('#hidden_subscription_modal .modal-dialog.modal-content').height(700);
                        $('#next_step_account').attr('data-step',5);
                        $('.content_data').html(data.result.html);
                        $('#trial_back_step').css("visibility", "visible");
                        $("input[name='checkbox_addons']").click(function () {
                            get_addons_click(this);
                        });
                    }
                },
            });
         }
         var user_quantity = $('input[name="quantity_trial"]').val()
         step_five(step_click, user_quantity)

         if(step_click==6){
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/data/'+step_click,
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'id_sub': id_sub, 'total': total}}),
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{

                        $('#hidden_subscription_modal .modal-dialog.modal-content').height(620);
                        $('#next_step_account').attr('data-step',7);
                        $('.content_data').html(data.result.html);
                        $('#trial_back_step').attr('data-step',4);
                         let country = 'sg';
                        call_phone(country);
                        $('select[name="country_id"]').change(function(){
                            checkCountry($(this).val());
                        });
                    }
                },
            });
         }
         if(step_click==7){
            var reg_name = $("input[name='name']").val();
            var reg_email = $("input[name='email']").val();
            var reg_phone = $("input[name='phone']").val();
            var code_country = $("input[name='phone_partner']").attr('data-code');
            var reg_company_name = $("input[name='company_name']").val();
            var total_price = $("input[name='total']").val();
            var reg_country = $('select[name="country_id"]').val();
            var reg_language_id = $('select[name="language_id"]').val();
            var quantity_select_plans = $('input[name="quantity_trial"]').val();

            var data = {
                'name': reg_name,
                'email': reg_email,
                'phone': reg_phone,
                'code_phone': code_country,
                'company': reg_company_name,
                'country': reg_country,
                'lang': reg_language_id,
                'total_price': total_price
            };
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/data/'+step_click,
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'id_sub': id_sub, 'data_info': data, 'is_pricelist':$('input[name="is_pricelist"]').val(), 'list_product': $('input[name="list_product_buy"]').val(), 'quantity_select_plans': quantity_select_plans}}),
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{
                        $('#trial_back_step').hide()
                        $('#next_step_account').hide()
                        $('#loading_gif_trial').css('visibility', 'visible')
                        window.location= window.location.origin + '/plans/payment';
                    }
                },
           });
        }
    });

    function step_five(step_click, number_user){
        if(step_click == 5){
                 list_id_addons = $("input[name='list_addons_buy']").val();
                 jQuery.ajax({
                    type: "POST",
                    dataType: 'json',
                    url:'/data/'+step_click,
                    data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'id_sub': $("input[name='id_sale_subscription']").val(), 'is_pricelist':$('input[name="is_pricelist"]').val(), 'list_addons': list_id_addons, 'quantity': number_user}}),
                    contentType: "application/json; charset=utf-8",
                    success: function (data) {
                        if(data.error){
                            alert('Error: '+ data.error.data.message);
                        }else{
                            $('input[name="list_product_buy"]').val(data.result.list_ids);
                            $('#hidden_subscription_modal .modal-dialog.modal-content').height(670);
                            $('#next_step_account').attr('data-step',6);
                            $('.content_data').html(data.result.html);
                            $('#trial_back_step').attr('data-step',3);
                        }
                    },
                });
             }
        }

     $(".upsell_subscription_status").on('click', function () {
        $('#upsell_subscription').attr('data-step', 1);
        var id_order = $(this).attr("data-id");
        var list_id_industry = $(this).attr("industry-list");
        var data_arr = {
            'order_id': id_order, 'type': 'upgrade', 'list_id_industry': list_id_industry
        };
        action_upgrade(data_arr);
     });

    $("#upsell_subscription").on('click', function () {
           var step =  parseFloat($(this).attr('data-step'));
           var type =  $('input[name="type"]').val()
           var data = {
                 'sale_id': $('input[name="order_id"]').val(),
                 'product_subscription': $('input[name="product_id"]').val(),
                 'type': $('input[name="type"]').val(),
                 'quanty': $('input[name="quanty"]').val(),
                 'list_addons': $('input[name="list_addons"]').val()
                 }
           status = $('input[name="status"]').val();
           if(step == 1){
                   jQuery.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: '/show-add-ons',
                    contentType: "application/json; charset=utf-8",
                    data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
                    success: function (data) {
                        if(data.error){
                            alert('Error: '+ data.error.data.message);
                        }else{
                            $('#upsell_subscription').attr('data-step', 2);
                            $('#hidden_subscription_upsell_modal .modal-dialog.modal-content').height(580);
                            $('#hidden_subscription_upsell_modal .content_data').html(data.result.html);
                            $('#back_step_modal').css("visibility", "visible");
                            if(data.result.list_addons){
                                $("input[name='list_addons']").val(data.result.list_addons)
                            }
                             $("input[name='checkbox_addons']").click(function () {
                                get_addons_upgrade(this);
                            });
                        }
                    },
                });
           }
         if(step == 2){
             var data = {
                 'sale_id': $('input[name="order_id"]').val(),
                 'product_subscription': $('input[name="product_id"]').val(),
                 'type': $('input[name="type"]').val(),
                 'quanty': $('input[name="quanty"]').val(),
                 'list_addons': $('input[name="list_addons"]').val(),
                 }
              var type =  $('input[name="type"]').val()
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url: '/show-bill',
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{

                        $('#upsell_subscription').attr('data-step', 3);
                        $('input[name="price_update_plans"]').val(data.result.price_update);
                        $('#hidden_subscription_upsell_modal .modal-dialog.modal-content').height(600);
                        $('#hidden_subscription_upsell_modal .content_data').html(data.result.html);
                        $('#back_step_modal').attr('data-step',3);
                    }
                },
            });
            }
         if(step == 3){
            var country =$('input[name="country_check"]').attr('value')
            checkCountry(country);
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url: '/show-confirm-info',
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'id_sale': $('input[name="order_id"]').val()}}),
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{
                        $('#upsell_subscription').attr('data-step', 4);
                        $('#hidden_subscription_upsell_modal .modal-dialog.modal-content').height(630);
                        $('#hidden_subscription_upsell_modal .content_data').html(data.result.html);
                        let country = 'sg';
                        call_phone(country);
                        $('select[name="country_id"]').change(function(){
                            checkCountry($(this).val());
                        });
                        $('#back_step_modal').attr('data-step', 4);
                    }
                },
            });
         }
         if(step == 4){
            var reg_name = $("input[name='name']").val();
            var reg_email = $("input[name='email']").val();
            var reg_phone = $("input[name='phone']").val();
            var code_country = $("input[name='phone_partner']").attr('data-code');
            var reg_company_name = $("input[name='company_name']").val();
            var price_update_plans = $("input[name='price_update_plans']").val();
            var list_addons_buy = $("input[name='list_addons']").val();
            var reg_country = $('select[name="country_id"]').val();
            var reg_language_id = $('select[name="language_id"]').val();
            var reg_state = $('select[name="state_id"]').val();
            var reg_zipcode = $("input[name='zipcode']").val();
            var reg_street = $("input[name='street']").val();
            var order_id = $('input[name="order_id"]').val();
            var product_id = $('input[name="product_id"]').val();
            var quanty = $('input[name="quanty"]').val();
            var type = $('input[name="type"]').val();
            var data_partner = {
                'name': reg_name,
                'email': reg_email,
                'phone': reg_phone,
                'code_country': code_country,
                'reg_state': reg_state,
                'reg_zipcode': reg_zipcode,
                'reg_street': reg_street,
                'company': reg_company_name,
                'country': reg_country,
                'lang': reg_language_id,
            }
            var data = {
                'data_partner': data_partner,
                'price_update_plans':price_update_plans,
                'list_addons_buy': list_addons_buy,
                'order_id': order_id,
                'product_id': product_id,
                'quanty': quanty,
                'type': type,
            };
           var type =  $('input[name="type"]').val()
           url = (type === 'upgrade') ? '/create-order' : '/downgrade-plans'
           jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url: url,
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{
                        if(data.result.html){
                            const Toast = Swal.mixin({
                              toast: true,
                              position: 'top-end',
                              showConfirmButton: false,
                              timer: 3000,
                              timerProgressBar: true,
                              didOpen: (toast) => {
                                toast.addEventListener('mouseenter', Swal.stopTimer)
                                toast.addEventListener('mouseleave', Swal.resumeTimer)
                              }
                            })

                            Toast.fire({
                              icon: 'success',
                              title: 'Downgrade Success!'
                            })
                            location.reload();
                        }
                        if(data.result.order_id){
                            window.location= window.location.origin + '/plans/payment';
                        }
                    }
                },
            });
         }
     });

    $('.o_portal_wrap').on('change','#action_update', function() {
         var data_arr = {
            'order_id': $('input[name="order_id"]').val(),
            'type': $(this).val(),
            'list_id_industry': $('input[name="list_id_industry"]').val()
            };
         $('input[name="type"]').val($(this).val());
         if($(this).val() =='upgrade'){
            $('input[name="list_addons"]').removeAttr('value');
         }
         change_select_sale_subscription(data_arr);
     });

    $('.o_portal_wrap').on('change','#select_plans', function() {
                 var data_user = {
                    'order_id':  $('input[name="order_id"]').val(), 'id_sale_select':  $(this).children("option:selected").val(), 'type':  $('input[name="type"]').val()
                 };
                 $('input[name="product_id"]').val($(this).val());
                 change_select_users(data_user);
         });

//    $('.o_portal_wrap').on('input', '#numUser', function() {
//        if($(this).val() <= 20){
//            $('input[name="quanty"]').val($(this).val());
//        }
//    });
     $('.o_portal_wrap').on('change', '#numUser', function() {
        let quanty = $(this).val();
        let quanty_max = $('input[name="quanty_max"]').val();
        let quanty_min = $(this).attr('min');
        if(Number($(this).val()) >= quanty_max){
            $('input[name="numUser"]').val(quanty);
            $('.msg_number').html('The maximum users for the current subscription plan is '+quanty_max+'. Thank you.');
        }else{
            if(Number($(this).val()) == quanty_min){
                $('.msg_number').html('The minimum users for the current subscription plan is '+quanty_min+'. Thank you');
            }else{
                $('.msg_number').html('');
            }
        }
        $('input[name="quanty"]').val(quanty);
    });

    $('.modal-footer #back_step_modal').click(function () {
        let step = parseFloat($(this).attr('data-step'));
        var data = {
                 'sale_id': $('input[name="order_id"]').val(),
                 'product_subscription': $('input[name="product_id"]').val(),
                 'type': $('input[name="type"]').val(),
                 'quanty': $('input[name="quanty"]').val(),
                 'list_addons': $('input[name="list_addons"]').val(),
                 }
        if(step==2){
            $('#upsell_subscription').attr('data-step', 1);
            var list_id_industry = $('input[name="list_id_industry"]').val();
            $('#upsell_subscription').attr('data-step',1);
            $('.back_step').css("visibility", "hidden");
            action_upgrade({'order_id': $('input[name="order_id"]').val(), 'type': $('input[name="type"]').val(), 'list_id_industry': list_id_industry});
            return false;
        }
        if(step==3){
            show_add_ons(data);
        }
        if(step==4){
            show_bill(data);
        }
    });

    $('.modal-body #trial_back_step').click(function () {
        let step = parseFloat($(this).attr('data-step'));
        var data_arr = {
                 'id_sub': $('input[name="id_sale_subscription"]').val(),
                 'stage': 'trial',
                 'id_order': $('a.active_subscription_status').attr('data-order'),
                 'is_pricelist': $('input[name="is_pricelist"]').val()
                 }
        if(step==2){
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/buy_pricelist',
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": data_arr}),
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{
                        if(data.result.check_active == 2){
                            window.location= window.location.origin + '/plans/payment';
                        }else{
                            $('input[name="is_pricelist"]').attr('value', data.result.month_id);
                            $('#hidden_subscription_modal .modal-dialog.modal-content').height(300);
                            $('.content_data').html(data.result.html);
                            $('#next_step_account').attr('data-step',4);
                            $('.trial_back_step').css("visibility", "hidden");
                        }
                    }
                },
           });
        }
        if(step==3){
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/add-addons',
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data':{'list_addons': $('input[name="list_addons_buy"]').val()}, 'is_pricelist':$('input[name="is_pricelist"]').val()}}),
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{
                        $('#hidden_subscription_modal .modal-dialog.modal-content').height(700);
                        $('#next_step_account').attr('data-step',5);
                        $('.content_data').html(data.result.html);
                        $("input[name='checkbox_addons']").click(function () {
                            get_addons_click(this);
                        });
                        $('#trial_back_step').attr('data-step',2);
                        $('.trial_back_step').css("visibility", "visible");
                    }
                },
            });
        }
        if(step==4){

           list_id_addons = $("input[name='list_addons_buy']").val();
             jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/data/5',
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'id_sub': $("input[name='id_sale_subscription']").val(), 'is_pricelist':$('input[name="is_pricelist"]').val(), 'list_addons': list_id_addons, 'quantity': $('input[name="quantity_trial"]').val()}}),
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{
                        $('input[name="list_product_buy"]').val(data.result.list_ids);
                        $('#hidden_subscription_modal .modal-dialog.modal-content').height(520);
                        $('#next_step_account').attr('data-step',6);
                        $('.content_data').html(data.result.html);
                        $('#trial_back_step').attr('data-step',3);
                    }
                },
            });
        }
    });

    function show_bill(data_arr){
        jQuery.ajax({
            type: "POST",
            dataType: 'json',
            url: '/show-bill',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data_arr}}),
            success: function (data) {
                if(data.error){
                    alert('Error: '+ data.error.data.message);
                }else{

                    $('#upsell_subscription').attr('data-step', 3);
                    $('input[name="price_update_plans"]').val(data.result.price_update);
                    $('#hidden_subscription_upsell_modal .modal-dialog.modal-content').height(600);
                    $('#hidden_subscription_upsell_modal .content_data').html(data.result.html);
                    $('#back_step_modal').attr('data-step',3);
                }
            },
        });
    }
    function show_add_ons(data_arr){
        jQuery.ajax({
            type: "POST",
            dataType: 'json',
            url: '/show-add-ons',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data_arr}}),
            success: function (data) {
                if(data.error){
                    alert('Error: '+ data.error.data.message);
                }else{
                    $('#upsell_subscription').attr('data-step', 2);
                    $('#hidden_subscription_upsell_modal .modal-dialog.modal-content').height(580);
                    $('#hidden_subscription_upsell_modal .content_data').html(data.result.html);
                    $('#back_step_modal').attr('data-step',2);
                    $('#back_step_modal').css("visibility", "visible");
                    if(data.result.list_addons){
                        $("input[name='list_addons']").val(data.result.list_addons)
                    }
                     $("input[name='checkbox_addons']").click(function () {
                        get_addons_upgrade(this);
                    });
                }
            },
        });
    }
    function action_upgrade(data_arr){
        jQuery.ajax({
            type: "POST",
            dataType: 'json',
            url: '/action-upgrade',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": data_arr}),
            success: function (data) {
                if(data.error){
                    alert('Error: '+ data.error.data.message);
                }else{
                    $('#hidden_subscription_upsell_modal .modal-dialog.modal-content').height(500);
                    change_select_sale_subscription(data_arr);
                    $('input[name="type"]').val(data_arr['type']);
                     $('input[name="status"]').val(true);
                    $('input[name="product_id"]').val($('#select_plans').children("option:selected").val());
                    $('#hidden_subscription_upsell_modal .content_data').html(data.result.html);
                    $('#hidden_subscription_upsell_modal').modal('show');
                    $('#back_step_modal').attr('data-step',2);
                    $('.back_step').css("visibility", "hidden");
                }
            },
        });
    }
    function change_select_sale_subscription(data_arr){
          jQuery.ajax({
            type: "POST",
            dataType: 'json',
            url: '/status-subscription',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data_arr}}),
            success: function (data) {
                if(data.error){
                    alert('Error: '+ data.error.data.message);
                }else{
                    $('#hidden_subscription_upsell_modal .content_data .subscription_template').html(data.result.html);
                    plans_id = ($('#select_plans').length) ? $('#select_plans').val() : ''

                  if(data.result.check === true){
                     var data_user = {
                        'order_id':  $('input[name="order_id"]').val(), 'id_sale_select': plans_id, 'type':  $('input[name="type"]').val()
                         };
                     change_select_users(data_user);
                     $('input[name="product_id"]').val($('#select_plans').val());
                     $("#upsell_subscription").show();
                     $(".users_template").show();
                  }else{
                     $(".row.users_template").html();
                     $("#upsell_subscription").hide();
                     $(".users_template").hide();
                  }
                  $('input[name="status"]').val(data.result.check);
                }
            },
        });
     }
    function change_select_users(data){
      jQuery.ajax({
        type: "POST",
        dataType: 'json',
        url: '/status-users',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
        success: function (data) {
            if(data.error){
                alert('Error: '+ data.error.data.message);
            }else{
                $('#hidden_subscription_upsell_modal .content_data .users_template').html(data.result.html);
                $('input[name="quanty"]').val($('#numUser').val());
            }
        },
    });
 }
 });



// get Province by country
function get_province(e) {
    jQuery.ajax({
        type: "POST",
        dataType: 'json',
        url:'/plans/get-province',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'country_id': e}}),
        success: function (data_result) {
            if(data_result.error){
                alert('Error: '+ data_result.error.data.message);
            }else{
                if(data_result.result.html !=''){
                    $('#div_state').css("display", "block");
                    $('#select_state_id').html(data_result.result.html);
                }else{
                    $('#div_state').css("display", "none");
                }
            }
        },
    });
}

$(document).ready(function () {
    let country = 'sg';
    call_phone(country);

    function call_phone(country) {
        var input = document.querySelector("#phone_partners");
        window.intlTelInput(input, {
            initialCountry: country,
            utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@17.0.3/build/js/utils.js",
        });
 }
});