from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = "stock.lot"

    product_is_vehicle = fields.Boolean(related="product_id.is_vehicle")
    product_is_plate = fields.Boolean(
        related="product_id.is_plate",
        string="Producto matrícula",
    )
    motor_serial = fields.Char(string="Serial de motor")
    plate_lot_id = fields.Many2one(
        "stock.lot",
        string="Matrícula",
        check_company=True,
        index=True,
        domain="[('product_id.is_plate', '=', True), ('id', '!=', id)]",
        help="La matrícula es un lote de un producto marcado como matrícula.",
    )
    vehicle_lot_ids = fields.One2many(
        "stock.lot",
        "plate_lot_id",
        string="Lotes del vehículo",
    )
    available_plate_lot_ids = fields.Many2many(
        "stock.lot",
        compute="_compute_available_plate_lot_ids",
    )

    @api.depends("company_id", "vehicle_lot_ids", "plate_lot_id")
    def _compute_available_plate_lot_ids(self):
        for lot in self:
            lot.available_plate_lot_ids = lot._available_plate_lots()

    def _available_plate_lots(self):
        self.ensure_one()
        plates = self.env["stock.lot"].search(
            [
                ("product_id.is_plate", "=", True),
                ("id", "!=", self.id or 0),
            ]
        )
        if self.company_id:
            plates = plates.filtered(
                lambda plate: not plate.company_id or plate.company_id == self.company_id
            )
        return plates.filtered(lambda plate: not (plate.vehicle_lot_ids - self))

    def _search(self, domain, offset=0, limit=None, order=None):
        exclude = self.env.context.get("assign_plate_exclude")
        if exclude:
            keep = self.env.context.get("assign_plate_keep") or 0
            try:
                keep = int(keep)
            except (TypeError, ValueError):
                keep = 0
            excluded_ids = [
                int(plate_id)
                for plate_id in str(exclude).split(",")
                if str(plate_id).isdigit() and int(plate_id) != keep
            ]
            if excluded_ids:
                domain = list(domain) + [("id", "not in", excluded_ids)]
        return super()._search(domain, offset=offset, limit=limit, order=order)

    @api.depends("name", "motor_serial", "product_id.is_vehicle")
    def _compute_display_name(self):
        super()._compute_display_name()
        for lot in self:
            if lot.product_id.is_vehicle and lot.motor_serial:
                lot.display_name = "%s / %s" % (lot.display_name, lot.motor_serial)

    @api.constrains("plate_lot_id")
    def _check_plate_lot_id(self):
        for lot in self:
            if lot.plate_lot_id and lot.plate_lot_id == lot:
                raise ValidationError(
                    _("La matrícula tiene que ser otro lote, distinto de este.")
                )
            if lot.plate_lot_id and not lot.plate_lot_id.product_id.is_plate:
                raise ValidationError(
                    _("La matrícula tiene que ser un lote de un producto matrícula.")
                )

    @api.constrains("motor_serial", "product_id")
    def _check_motor_serial(self):
        for lot in self:
            if (
                lot.product_id.is_vehicle
                and not lot.product_id.is_plate
                and not lot.motor_serial
            ):
                raise ValidationError(
                    _("El serial de motor es obligatorio en un producto de vehículo.")
                )
