from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_is_vehicle = fields.Boolean(related="product_id.is_vehicle")
    vehicle_lot_id = fields.Many2one(
        "stock.lot",
        string="Serial chasis",
        check_company=True,
        domain="[('product_id', '=', product_id)]",
    )
    plate_lot_id = fields.Many2one(
        "stock.lot",
        string="Matrícula",
        check_company=True,
        domain="[('product_id.is_plate', '=', True), ('id', '!=', vehicle_lot_id)]",
    )

    def _get_vehicle_lots(self):
        self.ensure_one()
        lots = self.vehicle_lot_id
        lots |= self.sale_line_ids.move_ids.move_line_ids.filtered(
            lambda move_line: move_line.lot_id
            and move_line.product_id == self.product_id
        ).lot_id
        return lots

    def _prepare_plate_wizard_lines(self):
        self.ensure_one()
        lots = self._get_vehicle_lots()
        commands = []
        for lot in lots:
            taken = (lots - lot).plate_lot_id
            available = lot._available_plate_lots() - taken
            commands.append(
                (
                    0,
                    0,
                    {
                        "lot_id": lot.id,
                        "plate_lot_id": lot.plate_lot_id.id,
                        "available_plate_ids": [(6, 0, available.ids)],
                    },
                )
            )
        return commands

    def action_assign_vehicle_plates(self):
        self.ensure_one()
        if not self.product_id.is_vehicle:
            return False
        if not self._get_vehicle_lots():
            raise UserError(
                _(
                    "Esta línea no tiene seriales de vehículo. "
                    "Asigna el lote en la entrega antes de elegir la matrícula."
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Asignar matrículas"),
            "res_model": "account.move.assign.plate",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_line_id": self.id},
        }

    def _get_vehicle_description(self):
        self.ensure_one()
        headers = ("SERIAL CHASIS", "SERIAL MOTOR", "MATRICULA")
        rows = []
        for lot in self._get_vehicle_lots():
            plate = lot.plate_lot_id
            if lot == self.vehicle_lot_id and self.plate_lot_id:
                plate = self.plate_lot_id
            rows.append(
                (
                    lot.name or "",
                    lot.motor_serial or "",
                    plate.name or "",
                )
            )
        if not rows:
            return ""
        widths = [
            max([len(header)] + [len(row[index]) for row in rows])
            for index, header in enumerate(headers)
        ]
        header_line = " | ".join(
            header.ljust(width) for header, width in zip(headers, widths)
        )
        value_lines = [
            " | ".join(value.ljust(width) for value, width in zip(row, widths))
            for row in rows
        ]
        return "\n".join([header_line] + value_lines)

    def _apply_vehicle_description(self):
        for line in self.filtered(
            lambda item: item.display_type == "product"
            and item.product_id.is_vehicle
            and item._get_vehicle_lots()
        ):
            product_name = line.product_id.display_name
            line.with_context(skip_vehicle_description=True).name = "%s\n%s" % (
                product_name,
                line._get_vehicle_description(),
            )

    @api.onchange("vehicle_lot_id")
    def _onchange_vehicle_lot_id(self):
        if self.vehicle_lot_id:
            self.plate_lot_id = self.vehicle_lot_id.plate_lot_id
        self._onchange_vehicle_description()

    @api.onchange("plate_lot_id", "product_id")
    def _onchange_vehicle_description(self):
        if self.product_id.is_vehicle and self.display_type == "product" and self._get_vehicle_lots():
            self.name = "%s\n%s" % (
                self.product_id.display_name,
                self._get_vehicle_description(),
            )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if not self.env.context.get("skip_vehicle_description"):
            lines._apply_vehicle_description()
        return lines

    def write(self, vals):
        result = super().write(vals)
        if not self.env.context.get("skip_vehicle_description") and {
            "vehicle_lot_id",
            "plate_lot_id",
            "product_id",
        } & set(vals):
            self._apply_vehicle_description()
        return result
