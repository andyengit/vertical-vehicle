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
            }
        )

    def test_plate_is_another_lot(self):
        plate = self.env["stock.lot"].create(
            {"name": "AA123BB", "product_id": self.product.id}
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
        self.assertIn(vehicle, plate.vehicle_lot_ids)

    def test_plate_cannot_be_the_same_lot(self):
        vehicle = self.env["stock.lot"].create(
            {"name": "CHASIS-2", "product_id": self.product.id}
        )
        with self.assertRaises(ValidationError):
            vehicle.plate_lot_id = vehicle
