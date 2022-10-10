odoo.define('theme_hiiboss.s_service_slider_options', function (require) {
"use strict";

const options = require('web_editor.snippets.options');
const webUtils = require('web.utils');
var core = require('web.core');
var qweb = core.qweb;

options.registry.ServiceSlider= options.Class.extend({
    xmlDependencies: [ '/theme_hiiboss/static/src/xml/service_dialog.xml'],
    events:{'click .set-service-config':'_service_configure' },
    init: function(){
        this._super.apply(this, arguments);
    },
    onBuilt: function(){
        this._super();
        this._service_configure();
    },
    _service_configure: function(){
        let cr = this;
        var current_col = cr.$target.attr("data-collection-id");
        var $modal = $(qweb.render('theme_hiiboss.service_dialog_template'));
        $modal.modal();
        cr._rpc({
            route: '/get_service_slider_collection',
            params: {
                'collection_id':cr.$target.attr("data-collection-id"),
            }
        }).then(function (data) {
            var service_col_ele =  $modal.find('select[name="service_collection"]');
            var collection_name = "";
            if(data.length > 0){
                for(var i = 0; i < data.length; i++){
                    if(current_col == data[i][0]){
                        service_col_ele.append("<option value='" + data[i][0] + "' selected='selected'>" + data[i][1] + "</option>");
                    } else {
                        service_col_ele.append("<option value='" + data[i][0] + "'>" + data[i][1] + "</option>");
                    }
                }
            }
            $modal.on('click', '.btn_apply', function(e){
                e.preventDefault();
                var selected_collection = $modal.find('select[name="service_collection"]').val();
                cr.$target.attr("data-collection-id", selected_collection);
            });
        });
    },
    cleanForSave: function(){
        this.$target.empty();
    },
});
});