odoo.define('onnet_customer_signup.checkout_form_ajax2', require => {
                    'use strict';
    const publicWidget = require('web.public.widget');
    const paymentFormMixin = require('payment.payment_form_mixin');
    const core = require('web.core');
    const Dialog = require('web.Dialog');

    const _t = core._t;

    publicWidget.registry.websiteClickAddon = publicWidget.Widget.extend(paymentFormMixin, {
        selector: '.customer-plan',
        events: {
            'click div[name="o_payment_option_card"]': '_onClickPaymentOption',
            'click a[name="o_payment_icon_more"]': '_onClickMorePaymentIcons',
            'click a[name="o_payment_icon_less"]': '_onClickLessPaymentIcons',
            'click button[name="o_payment_submit_button"]': '_onClickPay',
            'submit': '_onSubmit',
        },
        /**
         * @constructor
         */
        init: function () {
            const preventDoubleClick = handlerMethod => {
                return _.debounce(handlerMethod, 500, true);
            };
            this._super(...arguments);
            // Prevent double-clicks and browser glitches on all inputs
            this._onClickLessPaymentIcons = preventDoubleClick(this._onClickLessPaymentIcons);
            this._onClickMorePaymentIcons = preventDoubleClick(this._onClickMorePaymentIcons);
            this._onClickPay = preventDoubleClick(this._onClickPay);
            this._onClickPaymentOption = preventDoubleClick(this._onClickPaymentOption);
            this._onSubmit = preventDoubleClick(this._onSubmit);
        },
        start: async function () {
            await this._super(...arguments);
            window.addEventListener('pageshow', function (event) {
                if (event.persisted) {
                    window.location.reload();
                }
            });
            this.$('[data-toggle="tooltip"]').tooltip();
            this.txContext = {};
            Object.assign(this.txContext, this.$el.data());
            const $checkedRadios = this.$('input[name="o_payment_radio"]:checked');
            if ($checkedRadios.length === 1) {
                const checkedRadio = $checkedRadios[0];
                this._displayInlineForm(checkedRadio);
                this._enableButton();
            } else {
                this._setPaymentFlow(); // Initialize the payment flow to let acquirers overwrite it
            }
        },
        _onClickPaymentOption: function (ev) {
             const $dataForm = this.$('form[name="o_payment_checkout"]');
             this.txContext.accessToken = $dataForm.data('access-token');
             this.txContext.allowTokenSelection = $dataForm.data('allow-token-selection');
             this.txContext.amount = $dataForm.data('amount');
             this.txContext.currencyId = $dataForm.data('currency-id');
             this.txContext.landingRoute = $dataForm.data('landing-route');
             this.txContext.partnerId = $dataForm.data('partner-id');
             this.txContext.transactionRoute = $dataForm.data('transaction-route');

            // Uncheck all radio buttons
            this.$('input[name="o_payment_radio"]').prop('checked', false);
            // Check radio button linked to selected payment option
            const checkedRadio = $(ev.currentTarget).find('input[name="o_payment_radio"]')[0];
            $(checkedRadio).prop('checked', true);

              // Show the inputs in case they had been hidden
            this._showInputs();

            // Disable the submit button while building the content
//            this._disableButton(false);

            // Unfold and prepare the inline form of selected payment option
            this._displayInlineForm(checkedRadio);

            // Re-enable the submit button
            this._enableButton();
        },

        _showInputs: function () {
            const $submitButton = this.$('button[name="o_payment_submit_button"]');
            const $tokenizeCheckboxes = this.$('input[name="o_payment_save_as_token"]');
            $submitButton.removeClass('d-none');
            $tokenizeCheckboxes.closest('label').removeClass('d-none');
        },
        _onClickLessPaymentIcons: ev => {
            ev.preventDefault();
            ev.stopPropagation();
            // Hide the extra payment icons, and the "show less" button
            const $itemList = $(ev.currentTarget).parents('ul');
            const maxIconNumber = $itemList.data('max-icons');
            $itemList.children('li').slice(maxIconNumber).addClass('d-none');
            // Show the "show more" button
            $itemList.find('a[name="o_payment_icon_more"]').parents('li').removeClass('d-none');
        },
        _disableButton: (showLoadingAnimation = true) => {
            const $submitButton = this.$('button[name="o_payment_submit_button"]');
            const iconClass = $submitButton.data('icon-class');
            $submitButton.attr('disabled', true);
            if (showLoadingAnimation) {
                $submitButton.find('i').removeClass(iconClass);
                $submitButton.prepend(
                    '<span class="o_loader"><i class="fa fa-refresh fa-spin"></i>&nbsp;</span>'
                );
            }
        },
        _displayError: function (title, description = '', error = '') {
            const $checkedRadios = this.$('input[name="o_payment_radio"]:checked');
            if ($checkedRadios.length !== 1) { // Cannot find selected payment option, show dialog
                return new Dialog(null, {
                    title: _.str.sprintf(_t("Error: %s"), title),
                    size: 'medium',
                    $content: `<p>${_.str.escapeHTML(description) || ''}</p>`,
                    buttons: [{text: _t("Ok"), close: true}]
                }).open();
            } else { // Show error in inline form
                this._hideError(); // Remove any previous error

                // Build the html for the error
                let errorHtml = `<div class="alert alert-danger mb4" name="o_payment_error">
                                 <b>${_.str.escapeHTML(title)}</b>`;
                if (description !== '') {
                    errorHtml += `</br>${_.str.escapeHTML(description)}`;
                }
                if (error !== '') {
                    errorHtml += `</br>${_.str.escapeHTML(error)}`;
                }
                errorHtml += '</div>';

                // Append error to inline form and center the page on the error
                const checkedRadio = $checkedRadios[0];
                const paymentOptionId = this._getPaymentOptionIdFromRadio(checkedRadio);
                const formType = $(checkedRadio).data('payment-option-type');
                const $inlineForm = this.$(`#o_payment_${formType}_inline_form_${paymentOptionId}`);
                $inlineForm.removeClass('d-none'); // Show the inline form even if it was empty
                $inlineForm.append(errorHtml).find('div[name="o_payment_error"]')[0]
                    .scrollIntoView({behavior: 'smooth', block: 'center'});
            }
            this._enableButton(); // Enable button back after it was disabled before processing
            $('body').unblock(); // The page is blocked at this point, unblock it
        },
        _displayInlineForm: function (radio) {
            this._hideInlineForms(); // Collapse previously opened inline forms
            this._hideError(); // The error is only relevant until it is hidden with its inline form
            this._setPaymentFlow(); // Reset the payment flow to let acquirers overwrite it

            // Extract contextual values from the radio button
            const provider = this._getProviderFromRadio(radio);
            const paymentOptionId = this._getPaymentOptionIdFromRadio(radio);
            const flow = this._getPaymentFlowFromRadio(radio);

            // Prepare the inline form of the selected payment option and display it if not empty
            this._prepareInlineForm(provider, paymentOptionId, flow);
            const formType = $(radio).data('payment-option-type');
            const $inlineForm = this.$(`#o_payment_${formType}_inline_form_${paymentOptionId}`);
            if ($inlineForm.children().length > 0) {
                $inlineForm.removeClass('d-none');
            }
        },
        _enableButton: function () {
//            if (this._isButtonReady()) {
                const $submitButton = this.$('button[name="o_payment_submit_button"]');
                const iconClass = $submitButton.data('icon-class');
                $submitButton.attr('disabled', false);
                $submitButton.find('i').addClass(iconClass);
                $submitButton.find('span.o_loader').remove();
                return true;
//            }
//            return false;
        },
        _ensureRadioIsChecked: function ($checkedRadios) {
            if ($checkedRadios.length === 0) {
                this._displayError(
                    _t("No payment option selected"),
                    _t("Please select a payment option.")
                );
                return false;
            } else if ($checkedRadios.length > 1) {
                this._displayError(
                    _t("Multiple payment options selected"),
                    _t("Please select only one payment option.")
                );
                return false;
            }
            return true;
        },
        _getPaymentFlowFromRadio: function (radio) {
            if (
                $(radio).data('payment-option-type') === 'token'
                || this.txContext.flow === 'token'
            ) {
                return 'token';
            } else if (this.txContext.flow === 'redirect') {
                return 'redirect';
            } else {
                return 'direct';
            }
        },
        _getPaymentOptionIdFromRadio: radio => $(radio).data('payment-option-id'),
        _getProviderFromRadio: radio => $(radio).data('provider'),
        _hideError: () => this.$('div[name="o_payment_error"]').remove(),
        _hideInlineForms: () => this.$('[name="o_payment_inline_form"]').addClass('d-none'),
        _hideInputs: function () {
            const $submitButton = this.$('button[name="o_payment_submit_button"]');
            const $tokenizeCheckboxes = this.$('input[name="o_payment_save_as_token"]');
            $submitButton.addClass('d-none');
            $tokenizeCheckboxes.closest('label').addClass('d-none');
        },
        _isButtonReady: function () {
            const $checkedRadios = this.$('input[name="o_payment_radio"]:checked');
            if ($checkedRadios.length === 1) {
                const checkedRadio = $checkedRadios[0];
                const flow = this._getPaymentFlowFromRadio(checkedRadio);
                return flow !== 'token' || this.txContext.allowTokenSelection;
            } else {
                return false;
            }
        },
        _prepareTransactionRouteParams: function (provider, paymentOptionId, flow) {
            return {
                'payment_option_id': paymentOptionId,
                'reference_prefix': this.txContext.referencePrefix !== undefined
                    ? this.txContext.referencePrefix.toString() : null,
                'amount': this.txContext.amount !== undefined
                    ? parseFloat(this.txContext.amount) : null,
                'currency_id': this.txContext.currencyId
                    ? parseInt(this.txContext.currencyId) : null,
                'partner_id': parseInt(this.txContext.partnerId),
                'invoice_id': this.txContext.invoiceId
                    ? parseInt(this.txContext.invoiceId) : null,
                'flow': flow,
                'tokenization_requested': this.txContext.tokenizationRequested,
                'landing_route': this.txContext.landingRoute,
                'is_validation': this.txContext.isValidation,
                'access_token': this.txContext.accessToken
                    ? this.txContext.accessToken : undefined,
                'csrf_token': core.csrf_token,
            };
        },
        _prepareInlineForm: (provider, paymentOptionId, flow) => Promise.resolve(),
        _processPayment: function (provider, paymentOptionId, flow) {
            // Call the transaction route to create a tx and retrieve the processing values

            return this._rpc({
                route: this.txContext.transactionRoute,
                params: this._prepareTransactionRouteParams(provider, paymentOptionId, flow),
            }).then(processingValues => {
                if (flow === 'redirect') {
                    return this._processRedirectPayment(
                        provider, paymentOptionId, processingValues
                    );
                } else if (flow === 'direct') {
                    return this._processDirectPayment(provider, paymentOptionId, processingValues);
                } else if (flow === 'token') {
                    return this._processTokenPayment(provider, paymentOptionId, processingValues);
                }
            }).guardedCatch(error => {
                error.event.preventDefault();
                this._displayError(
                    _t("Server Error"),
                    _t("We are not able to process your payment."),
                    error.message.data.message
                );
            });
        },
        _processDirectPayment: (provider, acquirerId, processingValues) => Promise.resolve(),
        _processRedirectPayment: (provider, acquirerId, processingValues) => {
            // Append the redirect form to the body
            const $redirectForm = $(processingValues.redirect_form_html).attr(
                'id', 'o_payment_redirect_form'
            );
            $(document.getElementsByTagName('body')[0]).append($redirectForm);

            // Submit the form
            $redirectForm.submit();
        },
        _processTokenPayment: (provider, tokenId, processingValues) => {
            // The flow is already completed as payments by tokens are immediately processed
            window.location = '/payment/status';
        },
        _setPaymentFlow: function (flow = 'redirect') {
            if (flow !== 'redirect' && flow !== 'direct' && flow !== 'token') {
                console.warn(
                    `payment_form_mixin: method '_setPaymentFlow' was called with invalid flow:
                    ${flow}. Falling back to 'redirect'.`
                );
                this.txContext.flow = 'redirect';
            } else {
                this.txContext.flow = flow;
            }
        },
        _onClickMorePaymentIcons: ev => {
            ev.preventDefault();
            ev.stopPropagation();
            // Display all the payment icons, and the "show less" button
            $(ev.currentTarget).parents('ul').children('li').removeClass('d-none');
            // Hide the "show more" button
            $(ev.currentTarget).parents('li').addClass('d-none');
        },
        _onClickPay: async function (ev) {
            ev.stopPropagation();
            ev.preventDefault();
            // Check that the user has selected a payment option
            const $checkedRadios = this.$('input[name="o_payment_radio"]:checked');
            if (!this._ensureRadioIsChecked($checkedRadios)) {
                return;
            }
            const checkedRadio = $checkedRadios[0];

            // Extract contextual values from the radio button
            const provider = this._getProviderFromRadio(checkedRadio);
            const paymentOptionId = this._getPaymentOptionIdFromRadio(checkedRadio);
            const flow = this._getPaymentFlowFromRadio(checkedRadio);

            // Update the tx context with the value of the "Save my payment details" checkbox
            if (flow !== 'token') {
                const $tokenizeCheckbox = this.$(
                    `#o_payment_acquirer_inline_form_${paymentOptionId}` // Only match acq. radios
                ).find('input[name="o_payment_save_as_token"]');
                this.txContext.tokenizationRequested = $tokenizeCheckbox.length === 1
                    && $tokenizeCheckbox[0].checked;
            } else {
                this.txContext.tokenizationRequested = false;
            }

            // Make the payment
            this._hideError(); // Don't keep the error displayed if the user is going through 3DS2
            this._disableButton(true); // Disable until it is needed again
            $('body').block({
                message: false,
                overlayCSS: {backgroundColor: "#000", opacity: 0, zIndex: 1050},
            });
            this._processPayment(provider, paymentOptionId, flow);
        },
         /**
         * Delegate the handling of the payment request to `_onClickPay`.
         *
         * Called when submitting the form (e.g. through the Return key).
         *
         * @private
         * @param {Event} ev
         * @return {undefined}
         */
        _onSubmit: function (ev) {
            ev.stopPropagation();
            ev.preventDefault();

            this._onClickPay(ev);
        }
    });
    return publicWidget.registry.websiteClickAddon;
});

$(document).ready(function () {
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
        get_peicelist_plan($(this), data);
    });

    $(".customer-plan input[name='name_addons']").click(function () {
        get_add_click(this);
    });

    $('#next_step').click(function () {
        let step_click = parseFloat($(this).attr('data-step'));
        let trial = $("input[name='trial']").val();
         var country_check = $('input[name="country_check"]').val();
        if(step_click==2){
            var order_id = $('input[name="order_id"]').val();
            jQuery.ajax({
                type: "POST",
                dataType: 'json',
                url:'/plans/step'+step_click,
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'trial': trial, 'order_id': order_id}}),
                success: function (data) {
                    if(data.error){
                        alert('Error: '+ data.error.data.message);
                    }else{

                        $('#wizard-step20').removeClass('active');
                        $('#wizard-step20').addClass('complete');
                        $('#wizard-step30').removeClass('disabled');
                        $('#wizard-step30').addClass('active');
                        $('#next_step').attr('data-step', 3);
                        $('#back_step').attr('data-step', 3);

                        $('.customer-plan').html(data.result.html);
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
                        $('#back_step').click(function () {
                            let step_back = parseFloat($('#back_step').attr('data-step'));
                            CallBack(step_back, trial);
                        });
                        let country = 'sg';
                        call_phone(country);
                        var country_check = $('input[name="country_check"]').val();
                        if(country_check == 999999999){
                            $('#div_state').css("visibility", "hidden");
                        }else{
                            if(country_check){
                                get_province(country_check)
                            }
                        }
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
            var code_country = $("input[name='phone']").attr('data-code');
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
            if(ddlValidate(reg_name,reg_email,reg_phone,reg_company_name,reg_country,reg_language, reg_website, reg_street)) {
                if($("input[name='email']" ).hasClass("is-invalid")){
                    return false;
                }
                $(this).hide();
                jQuery.ajax({
                    type: "POST",
                    dataType: 'json',
                    url: '/plans/step'+step_click,
                    contentType: "application/json; charset=utf-8",
                    data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'trial': trial, 'reg_name': reg_name, 'reg_email': reg_email, 'reg_phone': reg_phone, 'reg_company_name': reg_company_name, 'reg_country': reg_country, 'reg_language_id': reg_language, 'reg_domain': reg_website, 'product_order': product_order, 'product_id': product_id, 'number_user': package_users_num, 'reg_industry': reg_industry, 'pricelist_id': pricelist_id, 'code_country': code_country, 'reg_state': reg_state, 'zipcode': reg_zipcode, 'reg_street': reg_street, 'order_id': order_id}}),
                    success: function (data) {
                        if(data.error){
                            alert('Error: '+ data.error.data.message);
                        }else{
                            if(data.result.trial==1){
                                window.location= window.location.origin + '/firework?product_id=' + data.result.id_plans + '&industry_id=' + reg_industry;
                            }else{
                                $('#wizard-step30').removeClass('active');
                                $('#wizard-step30').addClass('complete');
                                $('#wizard-step30').removeClass('disabled');
                                $('#wizard-step40').addClass('active');
                                $('#wizard-step40').removeClass('disabled');

                                $('#next_step').attr('data-step', 4);
                                $('#next_step').hide();
                                $('#back_step').hide();
                                $('#back_step').attr('data-step', 4);
                                $('.back_step').css("visibility", "hidden");
                               $('#loading_gif').css("visibility", "hidden");
                                window.location= window.location.origin + '/pricing-payment';
                            }
                        }
                    },
                });
            }
        }
    });

    $('#back_step').click(function () {
        let step_back = parseFloat($('#back_step').attr('data-step'));
        CallBack(step_back, $('#trial').val());
    });
});
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
    const obj = new contentHtml()
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


    $("input[name='product_order']").val(list_2);
    obj.add(list_packages);
    $('#o_yearly_table .list_package').remove()
//    $('.package_total').before(obj.html);
    sum_total = total + parseFloat(price_old);
    var data = {
        'list_add_on': list_2,
        'trial': trial,
        'pricelist_id': pricelist_id
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

function contentHtml(){
     this.html = "";
}

contentHtml.prototype.add = function (array){
    array.forEach(list_package,this)
}

function list_package(item) {
    var items = item.split("-");
    this.html +='<tr class="list_package">';
        this.html +='<td>';
            this.html +='<span class="btn-link name_package">'+ items[0] +'</span>';
        this.html +='</td>';
        this.html +='<td class="text-right">';
        if($("#trial").val() == 1){
            this.html +='<b class="onnet_pricing_apps_price_yearly">$0.00</b>';
        }else{
            this.html +='<b class="onnet_pricing_apps_price_yearly">$'+ formatNumber(parseFloat(items[1]).toFixed(2)) +'</b>';
        }
            this.html +='<span class="onnet_pricing_currency"> '+$("input[name='currency_name']").val()+'</span>';
        this.html +='</td>';
    this.html +='</tr>';
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

    if ($("input[name='website']").hasClass("is-invalid")) {
        check = false;
    }
    if(!checkStreet(reg_street)){
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
    var filter = /^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{2,3}[-\s\.]?[0-9]{2,6}$/im;
//    var filter = /^[\+65]?[(]?[0-9]{2}[)]?[-\s\.]?[0-9]{4}[-\s\.]?[0-9]{4}$/im;
    if (filter.test(txtPhone)) {
        return true;
    }
    else {
        return false;
    }
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
        get_province(country);
        return true;
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

function CallBack(step, trial) {
    if(step==3){
        product_order = $("input[name='product_order']").val();
        quantity = $("input[name='package_users_num']").val();
        product_id = $("input[name='product_id']").val();
        jQuery.ajax({
            type: "POST",
            dataType: 'json',
            url:'/plans/step1',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'trial': trial, 'product_order': product_order, 'quantity': quantity, 'product_id': product_id}}),
            success: function (data) {
                if(data.error){
                    alert('Error: '+ data.error.data.message);
                }else{
                    $('#wizard-step30').removeClass('active');
                    $('#wizard-step30').addClass('disabled');
                    $('#wizard-step20').addClass('active');
                    $('#wizard-step20').removeClass('complete');

                    $('#back_step').attr('data-step', 2);
                    $('#next_step').attr('data-step', 2);
                    $('.customer-plan').html(data.result.html);
                    $("input[name='name_addons']").click(function () {
                        get_add_click(this);
                    });
                    $('input[name="num_users"]').change(function () {
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
                        get_peicelist_plan($(this), data);
                    });
                }
            },
        });
    }else if(step==4){
        order_id = $("input[name='order_id']").val();
        jQuery.ajax({
            type: "POST",
            dataType: 'json',
            url:'/plans/step2',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'trial': trial, 'order_id': order_id}}),
            success: function (data) {
                if(data.error){
                    alert('Error: '+ data.error.data.message);
                }else{
                    $('#wizard-step20').removeClass('active');
                    $('#wizard-step20').addClass('complete');
                    $('#wizard-step30').addClass('active');
                    $('#wizard-step40').removeClass('disabled');
                    $('#next_step').show();
                    $('#next_step').attr('data-step', 3);
                    $('#back_step').attr('data-step', 3);

                    $('.customer-plan').html(data.result.html);
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
                        checkCountry($(this).val());
                    });
                    $("input[name='street']").keyup(function(){
                        checkStreet($(this).val());
                    });
                    $('#back_step').click(function () {
                        let step_back = parseFloat($('#back_step').attr('data-step'));
                        CallBack(step_back, trial);
                    });
                    let country = 'sg';
                    call_phone(country);
                }
            },
        });
    }else{
        window.location= window.location.origin + '/plans';
    }
}

function escapeRegExp(str) {
    if (str == null)
        return '';
    return String(str).replace(/([.*+?^=!:${}()|[\]\/\\])/g, '\\$1');
}
// get price list plans
function get_peicelist_plan(e, data, type) {
    jQuery.ajax({
        type: "POST",
        dataType: 'json',
        url:'/plans/get-peicelist-plan',
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

function formatNumber(num) {
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,')
}

function call_phone(country) {
        var input = document.querySelector("#phone_country");
        window.intlTelInput(input, {
            initialCountry: country,
            utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@17.0.3/build/js/utils.js",
        });
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
                console.log(data_result)
                if(data_result.result.html !=''){
                    $('#div_state').css("visibility", "visible");
                    $('#select_state_id').html(data_result.result.html);
                }else{
                    $('#div_state').css("visibility", "hidden");
                }
            }
        },
    });
}

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
}), jQuery(document).ready(function() {
    wcqib_refresh_quantity_increments()
}), jQuery(document).on("updated_wc_div", function() {
    wcqib_refresh_quantity_increments()
}), jQuery(document).on("click", ".plus, .minus", function() {
    var a = jQuery(this).closest(".quantity").find(".qty"),
        b = parseFloat(a.val()),
        c = parseFloat(a.attr("max")),
        d = parseFloat(a.attr("min")),
        e = a.attr("step");
    b && "" !== b && "NaN" !== b || (b = 0), "" !== c && "NaN" !== c || (c = ""), "" !== d && "NaN" !== d || (d = 0), "any" !== e && "" !== e && void 0 !== e && "NaN" !== parseFloat(e) || (e = 1), jQuery(this).is(".plus") ? c && b >= c ? a.val(c) : a.val((b + parseFloat(e)).toFixed(e.getDecimals())) : d && b <= d ? a.val(d) : b > 0 && a.val((b - parseFloat(e)).toFixed(e.getDecimals())), a.trigger("change")
});

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