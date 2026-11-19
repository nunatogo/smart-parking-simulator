"""Pruebas del controlador al agregar vehículos durante la simulación."""

import unittest

from src.controllers.parking_controller import ParkingController


class DynamicVehicleTest(unittest.TestCase):
    def test_add_vehicle_during_simulation(self) -> None:
        controller = ParkingController(
            capacity=2, arrival_range=(0.0, 0.0), parking_range=(0.01, 0.02)
        )
        controller.start(vehicle_count=3)
        extra = controller.add_vehicle()
        self.assertEqual(extra.vehicle_id, 4)
        self.assertTrue(controller.join(timeout=5))
        result = controller.summary()
        self.assertEqual(result["total_vehicles"], 4)
        self.assertEqual(result["completed"], 4)
        self.assertEqual(result["occupied"], 0)
        self.assertLessEqual(result["max_occupancy"], 2)

    def test_cannot_add_before_start_or_after_stop(self) -> None:
        controller = ParkingController(capacity=2)
        with self.assertRaises(RuntimeError):
            controller.add_vehicle()
        controller.start(0)
        controller.stop()
        with self.assertRaises(RuntimeError):
            controller.add_vehicle()

    def test_new_controller_allows_new_session(self) -> None:
        first = ParkingController(capacity=1, arrival_range=(0, 0), parking_range=(0, 0))
        first.start(1)
        self.assertTrue(first.join(timeout=5))
        another = ParkingController(capacity=1, arrival_range=(0, 0), parking_range=(0, 0))
        another.start(1)
        self.assertTrue(another.join(timeout=5))
        self.assertEqual(another.summary()["completed"], 1)


if __name__ == "__main__":
    unittest.main()
