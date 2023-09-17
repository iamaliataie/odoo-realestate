# -*- coding: utf-8 -*-
from random import randint
from odoo import models, fields, api
from datetime import timedelta, date
from odoo.exceptions import ValidationError, UserError


class Property(models.Model):
    _name = 'realestate.property'
    _description = 'realestate.property'
    _order = 'name'

    name = fields.Char(string='Title')
    description = fields.Text(string='Description', help='Property Description')
    address = fields.Text(string='Address', help='Address')
    postcode =  fields.Char(string='Postcode')
    date_availability = fields.Date('availability')
    expected_price = fields.Float()
    selling_price = fields.Float()
    bedrooms = fields.Integer()
    living_area = fields.Integer()
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()
    garden_orientations = fields.Selection([
        ('North', 'North'),
        ('South', 'South'),
        ('East', 'East'),
        ('West', 'West'),
    ])
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('cancelled', 'Cancelled'),
        ('sold', 'Sold'),
    ], default='new')

    property_type_id = fields.Many2one('realestate.property.type', string='Property Type')
    property_tags_ids = fields.Many2many('realestate.property.tag', string='Property Tags')
    salesman = fields.Many2one('res.users', default=lambda self: self.env.user)
    buyer = fields.Many2one('res.partner', default='')

    offers_ids = fields.One2many('realestate.property.offer', 'property_id', string='Offer')


    best_price = fields.Float(compute='_compute_best_price')
    total_area = fields.Float(compute='_compute_total_area')
    sequence = fields.Integer()

    # image = fields.Image(string='Image')

    _sql_constraints = [
        ('positive_expected_price', 'CHECK(expected_price > 0)', 'Expected price must be greater than 0'),
    ]


    @api.depends('offers_ids')
    def _compute_best_price(self):
        for property in self:
            property.best_price = max(property.offers_ids.mapped(lambda x: x.price)) if property.offers_ids else 0


    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for property in self:
            property.total_area = property.living_area + property.garden_area


    @api.onchange('garden')
    def _onchange_garden(self):
        for property in self:
            if property.garden:
                property.garden_area = 10
                property.garden_orientations = 'North'
            else:
                property.garden_area = 0
                property.garden_orientations = ''


    def action_cancel(self):
        for rec in self:
            if rec.state == 'cancelled':
                raise ValidationError('Property state is already cancelled')
            else:
                rec.state = 'cancelled'

    def action_sold(self):
        for rec in self:
            if rec.state == 'cancelled':
                raise ValidationError('Cancelled property cannot be sold')
            else:
                rec.state = 'sold'


class PropertyType(models.Model):
    _name = "realestate.property.type"
    _description = "realestate.property.type"

    name = fields.Char(string='Title')
    property_ids = fields.One2many('realestate.property', 'property_type_id', string="Properties")
    property_type_offers = fields.One2many('realestate.property.offer', 'property_type_id', string='Type offer')
    offers_count = fields.Integer(compute='_compute_type_offers')

    def type_offers(self):
        for rec in self:
            return {
                'name': 'Type offers',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'realestate.property.offer',
                'domain': [('property_type_id', '=', rec.id)]
            }

    @api.depends('property_type_offers')
    def _compute_type_offers(self):
        for rec in self:
            rec.offers_count = len(rec.property_type_offers)


class PropertyTag(models.Model):
    _name = "realestate.property.tag"
    _description = "realestate.property.tag"
    
    
    def _default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Title')
    color = fields.Integer(default=_default_color)


class PropertyOffer(models.Model):
    _name = "realestate.property.offer"
    _description = "realestate.property.offer"
    _rec_name = 'property_id'

    property_id = fields.Many2one('realestate.property', string='Property')
    partner_id = fields.Many2one('res.partner', string='Partner')
    price = fields.Float(string='Price', default=0)
    validity = fields.Integer()
    deadline_date = fields.Date(compute='_compute_deadline_date', inverse='_inverse_deadline_date')
    state = fields.Selection([
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], default='')
    property_type_id = fields.Many2one(related='property_id.property_type_id', store=True)


    @api.model
    def create(self, values):
        property = self.env['realestate.property'].browse(values.get('property_id'))
        if property.state == 'offer_accepted':
            raise ValidationError('This property is already sold.')
        elif values.get('price') <= property.best_price:
            raise ValidationError(f'Only offers greater than {property.best_price} are accepted')
        property.state = 'offer_received'
        return super(PropertyOffer, self).create(values)

    @api.depends('validity', 'create_date')
    def _compute_deadline_date(self):
        for offer in self:
            offer.deadline_date = offer.create_date + timedelta(days=offer.validity) if offer.create_date else False

    def _inverse_deadline_date(self):
        for offer in self:
            if offer.deadline_date:
                offer.validity = (self.deadline_date - self.create_date.date()).days
            else:
                offer.deadline_date = offer.create_date + timedelta(days=offer.validity) if offer.create_date else False

    def action_accepted(self):
        for rec in self:
            rec.state = 'accepted'
            rec.property_id.selling_price = rec.price
            rec.property_id.best_price = rec.price
            rec.property_id.state = 'offer_accepted'

    def action_refused(self):
        for rec in self:
            rec.state = 'rejected'