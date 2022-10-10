# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from builtins import list, set

from odoo import api, fields, models, _
from odoo.http import request
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def delete_item_line(self):
        """
        Delete products in sale_order_line
        """
        for item in self.order_line:
            item.unlink()

    def delete_addons_line(self):
        """
        Delete products in sale_order_line
        """
        for index in self.order_line:
            index.unlink()
        return self

    def add_data_line(self, list_product, pricelist_id_trial, quantity_plans_selected):
        """
        Update the fields of sale_subscription and create a dataset for sale_order
        :param list list_product: list id product buy
        :param int pricelist_id_trial: price list buy
        """
        value = []
        list_record_subscription = self.env['product.product'].sudo().search(
            [('id', 'in', list_product), ('is_subscription_plans', '=', True)])
        list_record_addons = self.env['product.product'].sudo().search(
            [('id', 'in', list_product), ('is_add_ons', '=', True)])
        product_pro = list_record_subscription.product_tmpl_id
        pricelist_plan = product_pro._get_combination_info(False, int(list_record_subscription.id or 0),
                                                           int(quantity_plans_selected),
                                                           self.env['product.pricelist'].browse(
                                                               int(pricelist_id_trial)))
        value.append((0, 0, {
            'product_id': list_record_subscription.id,
            'name': list_record_subscription.name,
            'product_uom_qty': quantity_plans_selected,
            'price_unit': pricelist_plan['price'],
        }))
        for item in list_record_addons:
            product_pro = item.product_tmpl_id
            pricelist_addons = product_pro._get_combination_info(False, int(item.id or 0),
                                                                 int(1),
                                                                 self.env['product.pricelist'].browse(
                                                                     int(pricelist_id_trial)))
            if item.is_recurring == True:
                value.append((0, 0, {
                    'name': item.name,
                    'product_id': item.id,
                    'product_uom_qty': 1,
                    'price_unit': pricelist_addons['price'],
                }))
            else:
                value.append((0, 0, {
                    'name': item.name,
                    'product_id': item.id,
                    'product_uom_qty': 1,
                    'price_unit': item.list_price,
                }))


        return value

    def get_addons_order_line(self):
        list_ids = []
        for index in self.order_line:
            if index.product_id.is_add_ons == True:
                list_ids.append(index.product_id.id)

        return list_ids

    def get_sale_subscription_order_line(self):
        self.ensure_one()
        for index in self.order_line.product_id:
            if index.is_subscription_plans == True:
                return index

    def get_quantity_plans(self):
        for index in self.order_line:
            if index.product_id.is_subscription_plans == True:
                return index.product_uom_qty

    def change_sale(self):
        self.sudo().write({'state': 'sale'})

    def delete_addons_order_line(self):
        for index in self.order_line:
            if index.product_template_id.is_add_ons == True:
                index.sudo().unlink()

        return True

    def add_addons_order_line(self, list_product, pricelist_id, number_user):
        """
        Update the fields of sale_subscription and create a dataset for sale_order
        :param list list_product: list id product buy
        :param int pricelist_id_trial: price list buy
        """
        value = []

        for item in list_product:
            if item.is_add_ons == True:
                if item.is_recurring == True:
                    product_pro = request.env['product.product'].sudo().search([('product_tmpl_id', '=', item.id)],
                                                                                 limit=1)
                    pricelist_addons = item._get_combination_info(False, int(product_pro.id or 0),
                                                                         int(1),
                                                                         request.env['product.pricelist'].browse(
                                                                             int(pricelist_id)))
                    value.append((0, 0, {
                        'name': item.name,
                        'product_id': item.id,
                        'product_uom_qty': 1,
                        'price_unit': pricelist_addons['price'],
                    }))
                else:
                    value.append((0, 0, {
                        'name': item.name,
                        'product_id': item.id,
                        'product_uom_qty': 1,
                        'price_unit': item.list_price,
                    }))

        return self.sudo().write({
            'order_line': value
        })
