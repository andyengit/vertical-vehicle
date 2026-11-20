from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = "stock.lot"

    motor_serial = fields.Char(string="Serial de motor")
    plate_lot_id = fields.Many2one(
        "stock.lot",
        string="Matrícula",
        check_company=True,
        index=True,
        help="La matrícula es otro lote. Su número es el nombre de ese lote.",
    )
    vehicle_lot_ids = fields.One2many(
        "stock.lot",
        "plate_lot_id",
        string="Lotes del vehículo",
    )

    @api.constrains("plate_lot_id")
    def _check_plate_lot_id(self):
        for lot in self:
            if lot.plate_lot_id and lot.plate_lot_id == lot:
                raise ValidationError(
                    _("La matrícula tiene que ser otro lote, distinto de este.")
                )
