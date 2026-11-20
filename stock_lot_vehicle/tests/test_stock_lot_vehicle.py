from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStockLotVehicle(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Vehicle",
                "is_storable": True,
                "tracking": "serial",
                "is_vehicle": True,
            }
        )
        cls.plate_product = cls.env["product.product"].create(
            {
                "name": "Plate",
                "is_storable": True,
                "tracking": "serial",
                "is_plate": True,
            }
        )

    def test_plate_is_another_lot(self):
        plate = self.env["stock.lot"].create(
            {"name": "AA123BB", "product_id": self.plate_product.id}
        )
        vehicle = self.env["stock.lot"].create(
            {
                "name": "CHASIS-1",
                "product_id": self.product.id,
                "motor_serial": "MOTOR-9",
                "plate_lot_id": plate.id,
            }
        )
        self.assertEqual(vehicle.plate_lot_id, plate)
        description = self.env["account.move.line"].new(
            {
                "product_id": self.product.id,
                "vehicle_lot_id": vehicle.id,
                "plate_lot_id": plate.id,
                "display_type": "product",
            }
        )._get_vehicle_description()
        lines = description.split("\n")
        self.assertEqual(
            [column.strip() for column in lines[0].split("|")],
            ["SERIAL CHASIS", "SERIAL MOTOR", "MATRICULA"],
        )
        self.assertEqual(
            [column.strip() for column in lines[1].split("|")],
            ["CHASIS-1", "MOTOR-9", "AA123BB"],
        )
        self.assertIn(vehicle, plate.vehicle_lot_ids)
        self.assertIn("MOTOR-9", vehicle.display_name)

    def test_motor_serial_required_for_vehicle(self):
        with self.assertRaises(ValidationError):
            self.env["stock.lot"].create(
                {"name": "CHASIS-3", "product_id": self.product.id}
            )

    def test_receipt_copies_motor_serial_to_lot(self):
        picking_type = self.env.ref("stock.picking_type_in")
        supplier = self.env.ref("stock.stock_location_suppliers")
        stock = self.env.ref("stock.stock_location_stock")
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": supplier.id,
                "location_dest_id": stock.id,
            }
        )
        move = self.env["stock.move"].create(
            {
                "name": self.product.name,
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": 1,
                "picking_id": picking.id,
                "location_id": supplier.id,
                "location_dest_id": stock.id,
            }
        )
        picking.action_confirm()
        line = move.move_line_ids[:1]
        if not line:
            line = self.env["stock.move.line"].create(
                {
                    "move_id": move.id,
                    "product_id": self.product.id,
                    "product_uom_id": self.product.uom_id.id,
                    "quantity": 1,
                    "location_id": supplier.id,
                    "location_dest_id": stock.id,
                    "picking_id": picking.id,
                }
            )
        line.write(
            {
                "lot_name": "CHASIS-4",
                "motor_serial": "MOTOR-4",
                "quantity": 1,
                "picked": True,
            }
        )
        move.picked = True
        picking.button_validate()
        lot = self.env["stock.lot"].search(
            [("name", "=", "CHASIS-4"), ("product_id", "=", self.product.id)]
        )
        self.assertEqual(lot.motor_serial, "MOTOR-4")

    def test_plate_cannot_be_the_same_lot(self):
        vehicle = self.env["stock.lot"].create(
            {
                "name": "CHASIS-2",
                "product_id": self.product.id,
                "motor_serial": "MOTOR-2",
            }
        )
        with self.assertRaises(ValidationError):
            vehicle.plate_lot_id = vehicle
