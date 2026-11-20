from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_is_vehicle = fields.Boolean(related="product_id.is_vehicle")
    motor_serial = fields.Char(string="Serial de motor")

    @api.onchange("lot_id")
    def _onchange_lot_id_motor_serial(self):
        if self.lot_id and self.product_id.is_vehicle:
            self.motor_serial = self.lot_id.motor_serial

    @api.constrains("motor_serial", "lot_name", "lot_id", "product_id")
    def _check_vehicle_motor_serial(self):
        for line in self:
            motor = line.motor_serial or line.lot_id.motor_serial
            if (
                line.product_id.is_vehicle
                and (line.lot_name or line.lot_id)
                and not motor
            ):
                raise ValidationError(
                    _("El serial de motor es obligatorio en un producto de vehículo.")
                )

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        if self.motor_serial:
            vals["motor_serial"] = self.motor_serial
        return vals

    def _fill_motor_serial_from_lot(self):
        for line in self.filtered(
            lambda item: item.lot_id and not item.motor_serial and item.lot_id.motor_serial
        ):
            line.motor_serial = line.lot_id.motor_serial

    def _sync_vehicle_motor_serial(self):
        for line in self.filtered(
            lambda item: item.lot_id
            and item.motor_serial
            and item.lot_id.motor_serial != item.motor_serial
        ):
            line.lot_id.motor_serial = line.motor_serial

    def _action_done(self):
        result = super()._action_done()
        self._sync_vehicle_motor_serial()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._fill_motor_serial_from_lot()
        lines._sync_vehicle_motor_serial()
        return lines

    def write(self, vals):
        result = super().write(vals)
        if {"motor_serial", "lot_id"} & set(vals):
            self._fill_motor_serial_from_lot()
            self._sync_vehicle_motor_serial()
        return result
