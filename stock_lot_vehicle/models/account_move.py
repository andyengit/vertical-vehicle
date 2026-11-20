from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_vehicle_plates(self):
        errors = []
        for line in self.invoice_line_ids.filtered(
            lambda item: item.display_type == "product"
            and item.product_id.is_vehicle
            and item.quantity
        ):
            needed = int(abs(line.quantity))
            plated = line._get_vehicle_lots().filtered("plate_lot_id")
            missing = needed - len(plated)
            if missing > 0:
                errors.append(
                    _("%s: faltan %s matrícula(s).")
                    % (line.product_id.display_name, missing)
                )
        if errors:
            raise UserError(
                _(
                    "No se puede confirmar la factura. "
                    "Cada vehículo debe tener matrícula.\n%s"
                )
                % "\n".join(errors)
            )

    def action_post(self):
        self._check_vehicle_plates()
        return super().action_post()
