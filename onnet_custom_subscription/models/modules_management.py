# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ModulesManagement(models.Model):
    _name = "modules.management"
    _description = "Modules Management"
    _rec_name = 'module_name'
    _order = "sequence asc, id desc"

    module_name = fields.Char('Module Name', required=True)
    technical_name = fields.Char('Technical Name', required=True)
    thumbnail_image = fields.Binary("Thumbnail Image", attachment=True, help="Thumbnail Image")
    category_segment = fields.Many2many(comodel_name='category.management',
                                   string="Module Categories",
                                   relation='category_modules',
                                   column1='modules_id',
                                   column2='category_id')
    sequence = fields.Integer("Sequence")