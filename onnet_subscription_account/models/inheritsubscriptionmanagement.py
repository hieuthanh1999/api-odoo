# -*- coding: utf-8 -*-
from odoo import api, fields, models
from markupsafe import Markup

class InheritSaleSubscriptionStage(models.Model):
    _inherit = 'sale.order'

    subscription_management = fields.Selection(string='Subscription Management',
                                               selection=[('create', 'Creation'), ('renew', 'Renewal'),
                                                          ('upsell', 'Upselling'), ('extend', 'Extending')],
                                               default='create',
                                               help="Creation: The Sales Order created the subscription\n"
                                                    "Upselling: The Sales Order added lines to the subscription\n"
                                                    "Renewal: The Sales Order replaced the subscription's content with its ownn\n"
                                                    "Extending: The Sales Order added extend lines to the subscription")

    def detail_order_html(self, item):
        texts = ''
        texts += Markup('<tr><td colspan="5" style="background: #E0FFFF;">Recurring</td></tr>')
        check = True
        i = 1
        total_next_bill = 0
        for index in item.order_line:
            total_next_bill += index.price_subtotal
            if (index.product_id.is_recurring == True and index.product_id.is_add_ons == True and index.product_id.is_trial == False) or index.product_id.is_subscription_plans == True:
                texts += Markup('<tr style="text-align:center;">') + Markup('<td style="padding:10px;">') \
                         + str(i) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.name) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.product_uom_qty) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_unit)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_subtotal)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td></tr>')
                total_next_bill += index.price_subtotal
            if (index.product_id.recurring_invoice == False and index.product_id.is_recurring == False and index.product_id.is_add_ons == False and index.product_id.is_trial == False and index.product_id.is_subscription_plans == False):
                texts += Markup('<tr style="text-align:center;">') + Markup('<td style="padding:10px;">') \
                         + str(i) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.name) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.product_uom_qty) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_unit)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_subtotal)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td></tr>')
                total_next_bill += index.price_subtotal
            i += 1
            if index.product_id.is_recurring == False and index.product_id.is_add_ons == True:
                check = False
                break

        if check == False:
            texts += Markup('<tr><td colspan="5" style="background: #E9D7FE;color:#7D4DFC;font-weight:600;">One-off</td></tr>')
            for index in item.order_line:
                if index.product_id.is_recurring == False and index.product_id.is_add_ons == True:
                    texts += Markup('<tr style="text-align:center;">') + Markup('<td style="padding:10px;">') \
                             + str(i) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                             + str(index.name) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                             + str(index.product_uom_qty) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                             + str("{:,.2f}".format(index.price_unit)) + ' ' + str(index.currency_id.name) + Markup(
                        '</td>') + Markup('<td style="padding:10px;">') \
                             + str("{:,.2f}".format(index.price_subtotal)) + ' ' + str(index.currency_id.name) + Markup(
                        '</td></tr>')
                    i += 1
        values = {
            'total': total_next_bill,
            'row': texts
        }
        return values

    def detail_order_extend_html(self, item):
        texts = ''
        i = 1
        total_next_bill = 0
        for index in item.order_line:
            total_next_bill += index.price_subtotal
            if (index.product_id.is_recurring == True and index.product_id.is_add_ons == True and index.product_id.is_trial == False) or index.product_id.is_subscription_plans == True:
                texts += Markup('<tr style="text-align:center;">') + Markup('<td style="padding:10px;">') \
                         + str(i) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.name) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.product_uom_qty) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_unit)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_subtotal)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td></tr>')
                total_next_bill += index.price_subtotal
            if (index.product_id.recurring_invoice == False and index.product_id.is_recurring == False and index.product_id.is_add_ons == False and index.product_id.is_trial == False and index.product_id.is_subscription_plans == False):
                texts += Markup('<tr style="text-align:center;">') + Markup('<td style="padding:10px;">') \
                         + str(i) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.name) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str(index.product_uom_qty) + Markup('</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_unit)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td>') + Markup('<td style="padding:10px;">') \
                         + str("{:,.2f}".format(index.price_subtotal)) + ' ' + str(index.currency_id.name) + Markup(
                    '</td></tr>')
                total_next_bill += index.price_subtotal
            i += 1
            if index.product_id.is_recurring == False and index.product_id.is_add_ons == True:
                break

        values = {
            'total': total_next_bill,
            'row': texts
        }
        return values