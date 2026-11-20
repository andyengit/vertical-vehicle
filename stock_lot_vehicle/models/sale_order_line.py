from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        vals = super()._prepare_invoice_line(**optional_values)
        if not self.product_id.is_vehicle:
            return vals
        lots = self.move_ids.move_line_ids.filtered(
            lambda line: line.state == "done" and line.lot_id
        ).lot_id
        if len(lots) == 1:
            vals["vehicle_lot_id"] = lots.id
            if lots.plate_lot_id:
                vals["plate_lot_id"] = lots.plate_lot_id.id
        return vals
