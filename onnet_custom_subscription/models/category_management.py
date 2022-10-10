# -*- coding: utf-8 -*-
from odoo import api, fields, models

class CategoryManagement(models.Model):
    _name = "category.management"
    _description = "Category Management"
    _order = "sequence asc, id desc"

    name = fields.Char('Category Name', required=True)
    modules = fields.Many2many(comodel_name='modules.management',
                                   string="Related Modules",
                                   relation='category_modules',
                                   column1='category_id',
                                   column2='modules_id')
    sequence = fields.Integer("Sequence")