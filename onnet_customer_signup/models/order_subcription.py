# -*- coding: utf-8 -*-

from odoo import api, fields, models, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class OrderSubcription(models.Model):
    _inherit = 'sale.subscription'

    access_token = fields.Text('Access Token')
    order_id = fields.Many2one('sale.order', string='Order id', required=False, index=True, copy=False)
    industry_management_id = fields.Many2one('industry.management', string='Industry Management', required=False, index=True, copy=False)
    website = fields.Char('Website')
    is_extra_maintenance = fields.Boolean(string='Extra Maintenance', default=False)
    is_check_trial = fields.Boolean(string='Is Check', default=False)
    is_check_delete_instance = fields.Boolean(string='Check delete instance', default=False)

    def delete_item_line(self):
        """
        Delete products in sale_subscription_line
        """
        for item in self.recurring_invoice_line_ids:
            item.unlink()

    def add_data_line(self, list_product, pricelist_id_trial, pricelist_template_trial, recurring_next_date, quantity_plans_selected):
        """
        Update the fields of sale_subscription and create a dataset for sale_subscription_line
        :param list list_product: list id product buy
        :param int pricelist_id_trial: price list buy
        :param int pricelist_template_trial: template buy (years or months)
        :param int progress_order: stage sale subscription
        :param date recurring_next_date: date sale subscription (+1 years or +1 months)
        """
        value = []
        list_record_subscription = self.env['product.product'].sudo().search([('id', 'in', list_product), ('is_subscription_plans', '=', True)])
        list_record_addons = self.env['product.product'].sudo().search([('id', 'in', list_product), ('is_add_ons', '=', True)])
        product_pro = list_record_subscription.product_tmpl_id
        pricelist_plan = product_pro._get_combination_info(False, int(list_record_subscription.id or 0),
                                                           int(quantity_plans_selected),
                                                           self.env['product.pricelist'].browse(
                                                               int(pricelist_id_trial)))
        value.append((0,0, {
                    'name': list_record_subscription.name,
                    'product_id': list_record_subscription.id,
                    'quantity': quantity_plans_selected,
                    'price_unit': pricelist_plan['price'],
                    'uom_id': 1
                }))
        for item in list_record_addons:
            product_pro = item.product_tmpl_id
            pricelist_addons= product_pro._get_combination_info(False, int(item.id or 0),
                                                               int(1),
                                                               self.env['product.pricelist'].browse(
                                                                   int(pricelist_id_trial)))
            if item.is_recurring == True:
                value.append((0, 0, {
                    'name': item.name,
                    'product_id': item.id,
                    'quantity': 1,
                    'price_unit':  pricelist_addons['price'],
                    'uom_id': item.uom_id.id
                }))
            else:
                value.append((0,0, {
                    'name': item.name,
                    'product_id': item.id,
                    'quantity': 1,
                    'price_unit': item.list_price,
                    'uom_id': item.uom_id.id
                }))

        sale_subs = {
            'name': 'Subscription book',
            'partner_id': self.partner_id.id,
            'pricelist_id': pricelist_id_trial,
            'template_id': pricelist_template_trial,
            'date_start': datetime.now(),
            'recurring_next_date': recurring_next_date,
            'recurring_invoice_line_ids': value,
            'date_unpail': datetime.now(),
            'extension_date': ''
        }

        self.browse(self.id).sudo().write(sale_subs)