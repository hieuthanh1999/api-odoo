odoo.define('theme_hiiboss.s_feature_slider',function(require){
    'use strict';
    
    var ajax = require('web.ajax');
    var sAnimation = require('website.content.snippets.animation');
    
    sAnimation.registry.FeatureSlider = sAnimation.Class.extend({
        selector: '.feature_slider',
        disabledInEditableMode: false,
    
        start: function (editable_mode) {
            var cr = this;
            if (cr.editableMode){
                cr.$target.empty().append('<div class="container"><div class="seaction-head"><h3>Feature Slider Snippet</h3></div></div>');
            }
            if (!cr.editableMode) {
                this.getFeatureData();
            }
        },
        getFeatureData: function() {
            var cr = this;
            ajax.jsonRpc('/get/get_feature_slider_content', 'call', {
                'collection_id': cr.$target.attr('data-collection-id'),
            }).then(function(data) {
                cr.$target.empty().append(data.slider);
                var sliderData = { 
                    spaceBetween: 15, 
                    slidesPerView: 1,
                    navigation: {
                        nextEl: ".hi_swiper-button-next",
                        prevEl: ".hi_swiper-button-prev",
                    },
                    breakpoints: {
                        640: {
                            slidesPerView: 2,
                        },
                        768: {
                            slidesPerView: 2,
                        },
                        1024: {
                            slidesPerView: 3,
                        },
                    },
                }
                cr.get_slider_data(sliderData);
            });
        },
        get_slider_data: function(data){
            var $slider = this.$target.find(".as-Swiper");
            $slider.attr("id","cr-swiper")
            var swiper = new Swiper("#cr-swiper", data);
            $slider.removeAttr("id");
        },
    });
    });
    