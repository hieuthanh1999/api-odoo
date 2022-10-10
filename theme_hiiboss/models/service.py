# -*- coding: utf-8 -*-

import string
from odoo import fields, models


class CustomerServices(models.Model):
	_name = "customer.services"
	_description = "Customer Services"

	name = fields.Char(string="Service", required=True)
	icon = fields.Binary(string="Icon")
	bg_color = fields.Char(string="Backgound-color")
	description = fields.Text(string="Description")
	link = fields.Char(string="Link")
	service_id = fields.Many2one('service.collections', string="Collection")


class ServiceCollection(models.Model):
	_name = "service.collections"
	_description = "Service Collections"

	name = fields.Char(string="Collection name", required=True)
	active = fields.Boolean(string="active", default=True)
	services = fields.One2many('service.collections.configuration', 'collection_id', string="Services")


class ServiceCollectionConfiguration(models.Model):
	_name = "service.collections.configuration"
	_description = "Service Collections Configuration"
	_order = 'sequence'

	collection_id = fields.Many2one('service.collections')
	sequence = fields.Integer(string="Sequence", store=True)
	service_id = fields.Many2one('customer.services', string="Services")

class FeatureSliderCollection(models.Model):
	_name = "feature.slider.collection"
	_description = "Feature Slider Collection"

	name =fields.Char(string="Name")
	tag = fields.Char(string="Tag")
	description = fields.Char(string="Description")
	components = fields.Many2many('feature.slider.component', string="Components")


class FeatureSliderComponent(models.Model):
	_name = "feature.slider.component"
	_description = "Feature Slider Component"

	name = fields.Char(string="Name")
	description = fields.Char(string="Description")
	link = fields.Char(string="Link")
	image = fields.Image(string="Image")
