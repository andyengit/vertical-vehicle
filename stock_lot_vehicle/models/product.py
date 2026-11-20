from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_vehicle = fields.Boolean(string="Producto de vehículo")
    is_plate = fields.Boolean(string="Matrícula")


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_vehicle = fields.Boolean(
        related="product_tmpl_id.is_vehicle",
        store=True,
        readonly=False,
    )
    is_plate = fields.Boolean(
        related="product_tmpl_id.is_plate",
        store=True,
        readonly=False,
    )
