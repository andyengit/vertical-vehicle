from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMoveAssignPlate(models.TransientModel):
    _name = "account.move.assign.plate"
    _description = "Asignar matrícula por lote"

    move_line_id = fields.Many2one("account.move.line", required=True)
    line_ids = fields.One2many(
        "account.move.assign.plate.line",
        "wizard_id",
        string="Lotes",
    )
    taken_plate_ids = fields.Char(compute="_compute_taken_plate_ids")

    @api.depends("line_ids.plate_lot_id")
    def _compute_taken_plate_ids(self):
        for wizard in self:
            wizard.taken_plate_ids = ",".join(
                str(plate_id) for plate_id in wizard.line_ids.plate_lot_id.ids if plate_id
            )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        move_line = self.env["account.move.line"].browse(
            values.get("move_line_id") or self.env.context.get("default_move_line_id")
        )
        if move_line:
            values["move_line_id"] = move_line.id
            values["line_ids"] = move_line._prepare_plate_wizard_lines()
        return values

    def action_assign(self):
        self.ensure_one()
        chosen = self.line_ids.filtered("plate_lot_id")
        if len(chosen.plate_lot_id) != len(chosen):
            raise UserError(_("Una matrícula solo puede asignarse a un lote."))
        for line in self.line_ids:
            if line.plate_lot_id and (
                line.plate_lot_id.vehicle_lot_ids - line.lot_id
            ):
                raise UserError(
                    _(
                        "La matrícula %s ya está asignada a otro lote.",
                        line.plate_lot_id.display_name,
                    )
                )
            line.lot_id.plate_lot_id = line.plate_lot_id
        self.move_line_id._apply_vehicle_description()
        return {"type": "ir.actions.act_window_close"}


class AccountMoveAssignPlateLine(models.TransientModel):
    _name = "account.move.assign.plate.line"
    _description = "Lote a matricular"

    wizard_id = fields.Many2one(
        "account.move.assign.plate",
        required=True,
        ondelete="cascade",
    )
    lot_id = fields.Many2one("stock.lot", string="Serial chasis", required=True)
    motor_serial = fields.Char(related="lot_id.motor_serial")
    product_id = fields.Many2one(related="lot_id.product_id")
    plate_lot_id = fields.Many2one(
        "stock.lot",
        string="Matrícula",
        domain="[('id', 'in', available_plate_ids)]",
    )
    available_plate_ids = fields.Many2many(
        "stock.lot",
        "account_move_assign_plate_line_available_rel",
        "wizard_line_id",
        "available_lot_id",
        string="Matrículas disponibles",
    )
