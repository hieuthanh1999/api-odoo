odoo.define('onnet_customer_signup.layout', function (require) {

    var rpc = require('web.rpc');
    var core = require('web.core');
    var ajax = require('web.ajax');
    var QWeb = core.qweb;

    //------------------------------------Check Field Input-----------------------------
    $("input[name='name']").keyup(function(){
        checkName($(this).val());
    });
    $("input[name='email']").keyup(function(){
        checkEmail($(this).val());
    });
    $("input[name='company_name']").keyup(function(){
        changeCompanyName($(this).val());
    });
    $("input[name='website']").keyup(function(){
        CheckDomain($(this).val());
    });
    $("input[name='phone']").keyup(function(){
        checkPhone($(this).val());
    });
    $('select[name="country_id"]').change(function(){
        $('input[name="country_check"]').attr('value','Email Adress');
        checkCountry($(this).val());
    });
    $("input[name='street']").keyup(function(){
        checkStreet($(this).val());
    });

    //------------------------------------Check back with browser------------------------
    $("input[name='name_addons']:checked:enabled").each(function () {
        get_add_click();
    });

    //------------------------------------Check State------------------------------------
    var country_check = $('input[name="country_check"]').val();
    check_hidden_state(country_check);

    /**
     * @private
     * @param {MouseEvent} event
     * Click Buy or Trial
     */
    $(document).on('click', '.btn_buy_now', function(){
        var data = {
            'industry': $(this).attr('industry'),
            'plans': $(this).attr('plans'),
            'pricelist_id': $(this).attr('pricelist'),
            'trial': $(this).attr('trial'),
            'action': 'new'
        };
        ajax.jsonRpc('/pricing-plans', 'call',{
                'data' : data,
            })
        .then(function (data) {
            if(data == true){
                window.location.href = window.location.origin + '/shop/add-ons';
            }else{
                window.location.href = window.location.origin;
            }
        });
    });

    //------------------------------------Click Users-----------------------------------
    $('.customer-plan input[name="num_users"]').change(function () {
        let numUser = $(this).val();
        let min = $(this).attr("min");
        let trial = $('#trial').val();
        let product_id = $('#form_product_id').val();
        let pricelist_id = $('#pricelist_id').val();
        var data = {
                'numUser': numUser,
                'product_id': product_id,
                'pricelist_id': pricelist_id,
                'trial': trial
            };
        $(this).attr('value', numUser);
        get_pricelist_plan($(this), data);
    });

    //------------------------------------Click Add-ons---------------------------------
    $(".customer-plan input[name='name_addons']").click(function () {
        get_add_click(this);
    });

    //------------------------------------Click Step------------------------------------
    $('#next_step').click(function () {
        let step_click = parseFloat($(this).attr('data-step'));
        let trial = $("input[name='trial']").val();
        let list_addons = $("input[name='product_order']").val();
        let country_check = $('input[name="country_check"]').val();
        let total = $('input[name="package_total"]').val();
        let num_users = parseFloat($('#users').attr('value'));

        let check_back = $('input[name="check_back"]').attr('check');
        if(step_click==2){
            if(trial == '1'){
                 data = {
                    'trial': trial,
                    'country_check': country_check,
                    'list_addons': list_addons,
                    'total': total,
                    'num_users': 1
                };
            }else{
              data = {
                    'trial': trial,
                    'country_check': country_check,
                    'list_addons': list_addons,
                    'total': total,
                    'num_users': num_users
                };
            }
         $(this).hide();
         $('#loading_gif').css("visibility", "visible");
         var order_id = $('input[name="order_id"]').val();
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/view-address',
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{
                        window.location = window.location.origin + '/shop/address';
                        $('#loading_gif').css("visibility", "hidden");
                    }
                },
            });
        }
        if(step_click==3){

            let trial = $("input[name='trial']").val();
            let product_order = $("input[name='product_order']").val();
            let product_id = $("input[name='product_id']").val();
            let package_users_num = $("input[name='package_users_num']").val();
            var reg_name = $("input[name='name']").val();
            var reg_email = $("input[name='email']").val();
            var reg_phone = $("input[name='phone']").val();
            var code_country = $("input[name='phone_partner']").attr('data-code');
            var reg_company_name = $("input[name='company_name']").val();
            var reg_country = $('select[name="country_id"]').val();
            var reg_state = $('select[name="state_id"]').val();
            var reg_zipcode = $("input[name='zipcode']").val();
            var reg_street = $("input[name='street']").val();
            var reg_language = $('#language_id').val();
            var partner_id = $('input[name="partner_id"]').val();
            var reg_website = $('input[name="website"]').val();
            var reg_industry = $('input[name="indistry"]').val();
            var pricelist_id = $('input[name="pricelist_id"]').val();
            var order_id = $('input[name="order_id"]').val();
            if(check_back == 'new'){
                  if(ddlValidate(reg_name, reg_email, reg_phone, reg_company_name, reg_country, reg_language, reg_website, reg_street)) {
                        $('#loading_gif').css("visibility", "visible");
                    $(this).css("visibility", "hidden");
                    data = {
                        'reg_name': reg_name,
                        'reg_email': reg_email,
                        'reg_phone': reg_phone,
                        'reg_company_name': reg_company_name,
                        'reg_country': reg_country,
                        'reg_language_id': reg_language,
                        'reg_domain': reg_website,
                        'product_order': product_order,
                        'product_id': product_id,
                        'number_user': package_users_num,
                        'reg_industry': reg_industry,
                        'pricelist_id': pricelist_id,
                        'code_country': code_country,
                        'reg_state': reg_state,
                        'zipcode': reg_zipcode,
                        'reg_street': reg_street,
                        'check_back': check_back
                        }
                    if($("input[name='email']" ).hasClass("is-invalid")){
                        return false;
                    }
                    $(this).hide();
                    jQuery.ajax({
                        type: "POST",
                        dataType: 'json',
                        url: '/view-payment',
                        contentType: "application/json; charset=utf-8",
                        data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
                        success: function (data) {
                            console.log(data)
                            if(data.error){
                                alert('Error: '+ data.error.data.message);
                            }else{
                                if(data.result) {
                                    if(data.result.trial==1){
                                        window.location= window.location.origin + '/firework?product_id=' + data.result.id_plans + '&industry_id=' + reg_industry;
                                    }else{
                                        window.location= window.location.origin + '/shop/payment';
                                    }
                                }

                            }
                        }
                    });
                }else{
                    $('#loading_gif').css("visibility", "hidden");
                    $(this).css("visibility", "visible");
                }
            }else{
                if(ddlValidate(reg_name, reg_email, reg_phone, reg_company_name, reg_country, reg_language, reg_website, reg_street)) {
                    data = {
                        'reg_name': reg_name,
                        'reg_email': reg_email,
                        'reg_phone': reg_phone,
                        'reg_company_name': reg_company_name,
                        'reg_country': reg_country,
                        'reg_language_id': reg_language,
                        'reg_domain': reg_website,
                        'product_order': product_order,
                        'product_id': product_id,
                        'number_user': package_users_num,
                        'reg_industry': reg_industry,
                        'pricelist_id': pricelist_id,
                        'code_country': code_country,
                        'reg_state': reg_state,
                        'zipcode': reg_zipcode,
                        'reg_street': reg_street,
                        'check_back': check_back
                        }
                    if($("input[name='email']" ).hasClass("is-invalid")){
                        return false;
                    }
                    $(this).hide();
                    jQuery.ajax({
                        type: "POST",
                        dataType: 'json',
                        url: '/view-payment',
                        contentType: "application/json; charset=utf-8",
                        data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
                        success: function (data) {
                            console.log(data)
                            if(data.error){
                                alert('Error: '+ data.error.data.message);
                            }else{
                                if(data.result) {
                                       if(data.result.trial==1){
                                    window.location= window.location.origin + '/firework?product_id=' + data.result.id_plans + '&industry_id=' + reg_industry;
                                }else{
                                    window.location= window.location.origin + '/shop/payment';
                                }
                                }

                            }
                        }
                    });
                }
            }

        }

    });


    //------------------------------------Back Step------------------------------------
    $('#back_step').click(function () {
        let step_click = parseFloat($(this).attr('data-step'));
        $('input[name="check_back"]').attr('check','back');
        if(step_click==1){
            window.location= window.location.origin + '/plans';
        }
        if(step_click==2){
            window.location= window.location.origin + '/shop/add-ons';
        }
        if(step_click==3){
            window.location= window.location.origin + '/shop/address';
        }
    })



    function wcqib_refresh_quantity_increments() {
        jQuery("div.quantity:not(.buttons_added), td.quantity:not(.buttons_added)").each(function(a, b) {
            var c = jQuery(b);
            c.addClass("buttons_added"), c.children().first().before('<input type="button" value="-" class="minus" />'), c.children().last().after('<input type="button" value="+" class="plus" />')
        })
    }
    String.prototype.getDecimals || (String.prototype.getDecimals = function() {
            var a = this,
                b = ("" + a).match(/(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/);
            return b ? Math.max(0, (b[1] ? b[1].length : 0) - (b[2] ? +b[2] : 0)) : 0
            }),
    jQuery(document).ready(function() {
    wcqib_refresh_quantity_increments()
    }),
    jQuery(document).on("updated_wc_div", function() {
        wcqib_refresh_quantity_increments()
    }),
    jQuery(document).on("click", ".plus, .minus", function() {
        var a = jQuery(this).closest(".quantity").find(".qty"),
            b = parseFloat(a.val()),
            c = parseFloat(a.attr("max")),
            d = parseFloat(a.attr("min")),
            e = a.attr("step");
        b && "" !== b && "NaN" !== b || (b = 0), "" !== c && "NaN" !== c || (c = ""), "" !== d && "NaN" !== d || (d = 0), "any" !== e && "" !== e && void 0 !== e && "NaN" !== parseFloat(e) || (e = 1), jQuery(this).is(".plus") ? c && b >= c ? a.val(c) : a.val((b + parseFloat(e)).toFixed(e.getDecimals())) : d && b <= d ? a.val(d) : b > 0 && a.val((b - parseFloat(e)).toFixed(e.getDecimals())), a.trigger("change")
    });
    //-----------------------------------End Function Check Field------------------------------------

    //-----------------------------------Check inspace------------------------------------
//var pageURL = $(location).attr("href");
//if(pageURL.includes("inspect=1")){
//}else{
//    $(document).keydown(function (event) {
//        if (event.keyCode == 123) { // Prevent F12
//            return false;
//        } else if (event.ctrlKey && event.shiftKey && event.keyCode == 73) { // Prevent Ctrl+Shift+I
//            return false;
//        }
//    });
//    $(document).on("contextmenu", function (e) {
//        e.preventDefault();
//    });
//
//    // set debugger
//    setInterval(function () {
//        debugger;
//    }, 50);
//}
// geri butonunu yakalama
// $(document).ready(function() {
//
//    function disableBack() {
//        window.history.forward(
//        {  var pageURL = $(location).attr("href");
//
//    if(pageURL.includes("/shop/add-ons")){
//        alert("dasdsad");
//    }})
//    }
//    window.onload = disableBack();
////    window.onpageshow = function(e) {
////        if (e.persisted)
////            disableBack();
////    }
// });
$(document).ready(function () {
    let country = 'sg';
    call_phone(country);

    function call_phone(country) {
        var input = document.querySelector("#phone_partner");
        window.intlTelInput(input, {
            initialCountry: country,
            utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@17.0.3/build/js/utils.js",
        });
 }
});


//-----------------------------------Begin Function Check Field------------------------------------


function changeCompanyName(e) {
let slugCompanyName = slugify(this.$("input[name='company_name']").val());

if (slugCompanyName !='') {
$("input[name='company_name']").removeClass('is-invalid');
$(".form-group .error_message").addClass('d-none');
this.$('#db-name').val(slugCompanyName);
this.$('.db-name-section #website').val(slugCompanyName);
this.$('#db-name-read-only').html(slugCompanyName);
return true;
}else{
$("input[name='company_name']").addClass('is-invalid');
$(".form-group .error_message").html('Required Field');
$(".form-group .error_message").removeClass('d-none');
return false;
}
}

function CheckDomain(e) {
let DomainName = slugify(this.$("input[name='website']").val());
this.$("input[name='website']").val(DomainName);
if(DomainName.length < 4){
$("input[name='website']").addClass('is-invalid');
$(".domain-name-form .error_website").removeClass('d-none');
$(".domain-name-form .error_website").html('Your domain must be at least 4 characters long');
return false;
} else if(DomainName == 'http' || DomainName == 'https'){
$("input[name='website']").addClass('is-invalid');
$(".domain-name-form .error_website").removeClass('d-none');
$(".domain-name-form .error_website").html('Your domain should not include \'http\' or \'https\'');
} else {
jQuery.ajax({
    type: "POST",
    dataType: 'json',
    url:'/check-domain',
    data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'domain': DomainName}}),
    contentType: "application/json; charset=utf-8",
    success: function (data) {
        if(data.error){
            alert('Error: '+ data.error.data.message);
        }else{
            if(data.result.check == false){
                $("input[name='website']").addClass('is-invalid');
                $(".domain-name-form .error_website").removeClass('d-none');
                $('.domain-name-form .error_website').html('Domain address already exists');
            }else{
                $("input[name='website']").removeClass('is-invalid');
                $(".domain-name-form .error_website").addClass('d-none');
            }
        }
    },
});
}
}

function CheckUser(e) {
let Email = this.$("input[name='email']").val();
let partner_id = this.$("input[name='partner_id']").val();
jQuery.ajax({
type: "POST",
dataType: 'json',
url:'/check-user',
data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'email': Email, 'partner_id': partner_id}}),
contentType: "application/json; charset=utf-8",
success: function (data) {
    if(data.error){
        alert('Error: '+ data.error.data.message);
    }else{
        if(data.result.check == true){
            $("input[name='email']").addClass('is-invalid');
            $(".error_email").removeClass('d-none');
            $('.error_email').html('Email address already exists');
            return false;
        }else{
            $("input[name='email']").removeClass('is-invalid');
            $(".error_email").addClass('d-none');
            return true;
        }
    }
},
});
}

function slugify(str){
if (str == null)
return '';
var from = "ąàáäâãåæăćęèéëêìíïîłńòóöôõøśșțùúüûñçżź"
, to = "aaaaaaaaaceeeeeiiiilnoooooosstuuuunczz"
, regex = new RegExp(defaultToWhiteSpace(from),'g');
str = String(str).toLowerCase().replace(regex, function(c) {
var index = from.indexOf(c);
return to.charAt(index) || '-';
});
str = str.replace(/[^\w\s-]/g, '');
return str.replace(/([A-Z])/g, '-$1').replace(/[-_\s]+/g, '-').toLowerCase();
}

var defaultToWhiteSpace = function(characters) {
if (characters == null)
return '\\s';
else if (characters.source)
return characters.source;
else
return '[' + escapeRegExp(characters) + ']';
};

function editDbName(e) {
this.customDomainName = true;
this.$('.field-db-name-read-only').addClass('d-none');
this.$('.db-name-section').removeClass('d-none');
}

function get_add_click(){
var list_packages = [];
var list_2= [];
var total = 0;
var price = $('#form_package_total').val();
var price_old = $('#form_package_total_change').val();
var pro1 = $("input[name='product_id']").val();
var pricelist_id = $("input[name='pricelist_id']").val();
var trial = $("#trial").val();
var sum_total = 0;
$("input[name='name_addons']:checked:enabled").each(function () {
addons_price = $(this).attr('data-price');
if(trial == 1){
    list_packages.push($(this).attr('data-name')+'-0.00');
}else{
    list_packages.push($(this).attr('data-name')+'-'+addons_price);
}
total += parseFloat(addons_price);
list_2.push($(this).val());

});
sum_total = total + parseFloat(price_old);
$("input[name='product_order']").val(list_2);

var data = {
'list_addons': list_2,
'trial': trial,
'pricelist': pricelist_id
};
jQuery.ajax({
type: "POST",
dataType: 'json',
url:'/plans/show-add-on',
contentType: "application/json; charset=utf-8",
data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
success: function (data_result) {
    if(data.error){
        alert('Error: '+ data_result.error.data.message);
    }else{
        $('.list_package').remove();
        $('.header_one_off').remove();
        $("input[name='product_order']").before(data_result.result.html);
    }
},
});
if(trial != 1){
$('.package_total .onnet_pricing_apps_price_total').html('$ '+formatNumber(parseFloat(sum_total).toFixed(2)));
$("input[name='package_total']").val(parseFloat(sum_total).toFixed(2));
}
}

function ddlValidate(reg_name, reg_email, reg_phone, reg_company_name, reg_country, reg_language, reg_website, reg_street) {
var check = true;
if(!checkName(reg_name)){
check = false;
}
if(!checkPhone(reg_phone)){
check = false;
}

if(!changeCompanyName(reg_company_name)){
check = false;
}
if(!checkCountry(reg_country)){
check = false;
}

if($("input[name='website']").val() ==''){
CheckDomain(reg_website)
}

CheckDomain(reg_website)

if($("input[name='website']").hasClass("is-invalid")) {
check = false;
}
if(!checkStreet(reg_street)){
check = false;
}
if($("input[name='email']").hasClass("is-invalid")) {
check = false;
}
if(reg_email ==="") {
$("input[name='email']").addClass('is-invalid');
$(".form-group .error_email").removeClass('d-none');
$(".form-group .error_email").html('Required Field');
check = false;
}else{
if(validateEmail(reg_email)) {
    CheckUser(reg_email);
}else{
    $("input[name='email']").addClass('is-invalid');
    $(".form-group .error_email").removeClass('d-none');
    $(".form-group .error_email").html('Invalid Email Address');
    check = false;
}
}

if(check == false){
return false;
}else{
$('#loading_gif').css("visibility", "visible");
return true;
}
}

function checkName(name) {
if(name === "") {
$("input[name='name']").addClass('is-invalid');
$(".form-group .error_name").removeClass('d-none');
$(".form-group .error_name").html('Required Field');
return false
}else{
$("input[name='name']").removeClass('is-invalid');
$(".form-group .error_name").addClass('d-none');
return true
}
}

function checkPhone(phone) {
if(phone === "") {
$("input[name='phone']").addClass('is-invalid');
$(".form-group .error_phone").removeClass('d-none');
$(".form-group .error_phone").html('Required Field');
return false
}else{
if(validatePhone(phone)){
    $("input[name='phone']").removeClass('is-invalid');
    $(".form-group .error_phone").addClass('d-none');
    return true
}else{
    $("input[name='phone']").addClass('is-invalid');
    $(".error_phone").removeClass('d-none');
    $(".error_phone").html('Invalid phone number');
    return false;
}
}
}

function checkEmail(email) {
if(email ==="") {
$("input[name='email']").addClass('is-invalid');
$(".form-group .error_email").removeClass('d-none');
$(".form-group .error_email").html('Required Field');
return false;
}
else{
if(validateEmail($("input[name='email']").val())) {
    CheckUser(this);
    return false;
}else{
    $("input[name='email']").addClass('is-invalid');
    $(".form-group .error_email").removeClass('d-none');
    $(".form-group .error_email").html('Invalid Email Address');
    return false;
}
}
}

function validateEmail($email) {
var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
return emailReg.test( $email );
}

function validatePhone(txtPhone) {
var filter = /^[\]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{2,3}[-\s\.]?[0-9]{2,6}$/im;
if (filter.test(txtPhone)) {
return true;
}
else {
return false;
}
}



function checkStreet(street) {
if(street === "") {
$("#street").addClass('is-invalid');
$(".form-group .error_street").removeClass('d-none');
$(".form-group .error_street").html('Required Field');
return false;
}else{
$("#street").removeClass('is-invalid');
$(".form-group .error_street").addClass('d-none');
return true;
}
}

function escapeRegExp(str) {
if (str == null)
return '';
return String(str).replace(/([.*+?^=!:${}()|[\]\/\\])/g, '\\$1');
}
// get price list plans
function get_pricelist_plan(e, data, type) {
jQuery.ajax({
type: "POST",
dataType: 'json',
url:'/plans/get-pricelist-plan',
contentType: "application/json; charset=utf-8",
data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'data': data}}),
success: function (data_result) {
    if(data_result.error){
        alert('Error: '+ data_result.error.data.message);
    }else{
        if(data_result.result.msg !=''){
            $('.line2.error_number_user').html(data_result.result.msg);
        }else{
            $('.line2.error_number_user').html('');
        }
        $('.numuser').html(data_result.result.numUser);
        $("input[name='num_users']").val(data_result.result.numUser);
        $("input[name='package_users_num']").val(data_result.result.numUser);
        if(data_result.result.trial !=1){
            var total = 0;
            $("input[name='name_addons']:checked:enabled").each(function () {
                addons_price = $(this).attr('data-price');
                total += parseFloat(addons_price);
            });
            total = total + data_result.result.total_price;
            $('.openerp_plan_pricing .oe_currency_value').html(formatNumber(parseFloat(data_result.result.total_price).toFixed(2)));
            $('.package_total .onnet_pricing_apps_price_total').html('$ '+formatNumber(parseFloat(total).toFixed(2)));
            $("input[name='package_total']").val(total);
             if($("input[name='num_users']").val() !=''){
                $("input[name='package_total_change']").val(data_result.result.total_price);
            }else{
                $("input[name='package_total_change']").val(total);
            }
        }
    }
},
});
}


});

function formatNumber(num) {
return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
}



function checkCountry(country) {
          if(country === "") {
            $("#country_id").addClass('is-invalid');
            $(".form-group .error_country").removeClass('d-none');
            $(".form-group .error_country").html('Required Field');
            return false;
        }else{
            $("#country_id").removeClass('is-invalid');
            $(".form-group .error_country").addClass('d-none');
            $('input[name="country_check"]').val(country);
            check_hidden_state(country);
            get_province(country);
            return true;
        }
    }
function check_hidden_state(country_check){
        if(country_check == 999999999){
        $('#div_state').css("display", "none");
        }else{
        if(country_check){
            get_province(country_check);
        }
        }
}
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