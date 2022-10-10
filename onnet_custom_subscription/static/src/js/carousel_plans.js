$(document).ready(function () {
    mod_price = $("#color_mode").prop("checked");
    if(mod_price == true){
        $('.pricelist_span').addClass('hihi');
    }
    else{
        $('.pricelist_span').removeClass('hihi');
    }
});


var screenSize= $( window ).width();
     $(".active-instance").on('click', function () {
       jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/active-token',
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'id_sub': $(this).attr('data-id')}}),
                contentType: "application/json; charset=utf-8",
                success: function (data) {
                    location.reload(true);
                },
           });
         });

function plans(id){
//slide Plans
   count_plans = $( '#' +id +' .count_plans').attr("data-count");

   if(count_plans <= 3){
        $( '#' +id +'.plans_content .owl-carousel').owlCarousel({
            margin: 5,
            mouseDrag: false,
            responsive:{
                0:{
                    items: 1
                },
                480:{
                    items: 2
                },
                768:{
                    items: 2
                },
                992:{
                    items: 3
                }
            }
     });
    }
   if(count_plans < 5 && count_plans > 3){
        $( '#' +id +'.plans_content .owl-carousel').owlCarousel({
            margin: 5,
            mouseDrag: false,
            responsive:{
                0:{
                    items: 1
                },
                480:{
                    items: 2
                },
                768:{
                    items: 2
                },
                992:{
                    items: 4
                }
            }
     });
   }else if(count_plans >= 5) {
        $( '#' +id +'.plans_content .owl-carousel').owlCarousel({
            loop: true,
            nav: true,
            margin: 5,
            responsive:{
                0:{
                    items: 1
                },
                480:{
                    items: 2
                },
                768:{
                    items: 2
                },
                992:{
                    items: 4
                }
            }
     });
   }
}


var screenSize= $( window ).width();

count_plans = $('.your-plans .count_plans').attr("data-count");
if(count_plans <=3 ){
    $('.your-plans.owl-carousel').owlCarousel({
        loop: false,
        margin:2,
        nav: false,
        mouseDrag: false,
        responsive:{
            0:{
                items: 1
            },
            480:{
                items: 2
            },
            768:{
                items: 3
            },
            992:{
                items: 3
            }
        }
    })
}else{
    $('.your-plans.owl-carousel').owlCarousel({
        loop: false,
        margin:2,
        nav: false,
        responsive:{
            0:{
                items: 1
            },
            480:{
                items: 2
            },
            768:{
                items: 3
            },
            992:{
                items: 3
            }
        }
    })
}


window.onload = load_view();
function load_view(){
        id_industry = $('.customer_items.show').attr("data-values");
        ajax_plans(id_industry, $("#color_mode").prop("checked"));
        ajax_description(id_industry);
        activeTab($('.tab_customers .customer_items.show:first-child'));
}
$(document).ready(function () {

     $('.plans_container').on('click', '.btn_try_now', function() {
            var industry = $(this).attr('industry');
            var plan = $(this).attr('plans');
            var pricelist_id = $(this).attr('pricelist');
            var trial = $(this).attr('trial');

            var data = {
                'industry': $(this).attr('industry'),
                'plans': $(this).attr('plans'),
                'pricelist_id': $(this).attr('pricelist'),
                'trial': $(this).attr('trial'),
                'action': 'new'
            };
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/check-industry-plans',
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'industry': industry,
                                                'plan': plan, 'pricelist_id': pricelist_id, 'trial': trial}}),
                success: function (data_result) {
                    if(data_result.error){
                        alert('Error: '+ data_result.error.data.message);
                    }else{
                        if(data_result.result.check == 1){
                            jQuery.ajax({
                                type: "POST",
                                dataType: 'json',
                                url:'/pricing-plans',
                                contentType: "application/json; charset=utf-8",
                                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
                                success: function (data) {
                                    console.log(data);
                                    if(data.error){
                                        alert('Error: '+ data.error.data.message);
                                    }else{
                                          if(data.result == true){
                                                window.location.href = window.location.origin + '/shop/add-ons';
                                            }else{
                                                window.location.href = window.location.origin;
                                            }
                                    }
                                }
                            });
                        }else{
                            $('#industry_popup').modal('show');
                            $('#industry_popup .modal-dialog.modal-content').height('auto');
                        }
                    }
                }
            });
     });
    $("#color_mode").on("change", function () {
        if($(this).prop("checked") == true){
            $('.pricelist_span').addClass('hihi');
        }
        else{
            $('.pricelist_span').removeClass('hihi');
        }
        ajax_plans($('.customer_items.show').attr("data-values"), $(this).prop("checked"))

    });

    $('.tab_customers ').on('click', '.customer_items', function() {
        activeTab(this);
        ajax_plans($(this).attr("data-values"), $("#color_mode").prop("checked"))
        ajax_description($(this).attr("data-values"));
    });

    count_industry = $('.count_industry').attr("data-count");

     if(count_plans <= 4){
         $('.tab_customers').owlCarousel({
            mouseDrag: false,
            loop:false,
            responsive:{
                0:{
                    items: 1
                },
                480:{
                    items: 2
                },
                768:{
                    items: 3
                },
                992:{
                    items: 3
                }
            }
         });
     }
      else{
         $('.tab_customers').owlCarousel({
            mouseDrag: false,
            loop:false,
            responsive:{
                0:{
                    items: 1
                },
                480:{
                    items: 2
                },
                768:{
                    items: 3
                },
                992:{
                    items: 4
                }
            }
         });
     }


});

 function activeTab(obj){
        $('.customer_items.show').removeClass('show');
        $(obj).addClass('show');
       return $(obj).attr('data-values');
 }

 function ajax_description(id_industry){
       jQuery.ajax({
        type: "POST",
        dataType: 'json',
        url:'/show-description',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'id_industry': id_industry}}),
        success: function (data) {
            if(data.error){
                alert('Error: '+ data.error.data.message);
            }else{
                if(data.result.html){
                    $('.industry_description').html(data.result.html);
                }
            }
        }
    });
}

function ajax_plans(id_industry, price_list){
       jQuery.ajax({
        type: "POST",
        dataType: 'json',
        url:'/show-plans',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'id_industry': id_industry, 'price_list': price_list}}),
        success: function (data) {
            if(data.error){
                alert('Error: '+ data.error.data.message);
            }else{
                if(data.result.html){
                    $('#plans_container').html(data.result.html);
                }
                plans(data.result.id_insdustry)
            }
        }
    });
}

