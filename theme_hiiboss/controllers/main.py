# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class ServiceController(http.Controller):

    @http.route('/get_service_slider_collection', type='json', auth='public', website=True)
    def get_service_slider_collection(self, **kwargs):
        values = {}
        col_list = []
        collections = request.env['service.collections'].sudo().search([('active', '=', True)])
        for col in collections:
            col_list.append([col.id, col.name])
        return col_list

    @http.route('/get/get_service_slider_content', type='json', auth='public', website=True)
    def get_service_slider_content(self, **kwargs):
        values = {}
        collection_id = int(kwargs.get('collection_id'))
        collection = request.env['service.collections'].sudo().search([('id', '=', collection_id)])
        services = collection.services
        tmplt = request.website.viewref("theme_hiiboss.service_slider_layout")
        values.update({'slider': tmplt._render({'services': services})})
        return values

    @http.route('/get_feature_slider_collection', type='json', auth='public', website=True)
    def get_feature_slider_collection(self, **kwargs):
        values = {}
        col_list = []
        collections = request.env['feature.slider.collection'].sudo().search([])
        for col in collections:
            col_list.append([col.id, col.name])
        return col_list

    @http.route('/get/get_feature_slider_content', type='json', auth='public', website=True)
    def get_feature_slider_content(self, **kwargs):
        values = {}
        collection_id = int(kwargs.get('collection_id'))
        collection = request.env['feature.slider.collection'].sudo().search([('id', '=', collection_id)])
        # collection_data = collection.services
        tmplt = request.website.viewref("theme_hiiboss.feature_slider_layout")
        values.update({'slider': tmplt._render({'collection': collection})})
        return values
