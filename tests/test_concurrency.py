"""Pruebas concurrentes del simulador."""

import unittest

from src.controllers.parking_controller import ParkingController


class ConcurrencyTest(unittest.TestCase):
    def test_ten_vehicles_six_spaces(self) -> None:
        controller = ParkingController(
            capacity=6, arrival_range=(0.0, 0.0), parking_range=(0.002, 0.005)
        )
        controller.start(vehicle_count=10)
        self.assertTrue(controller.join(timeout=5))
        summary = controller.summary()
        self.assertEqual(summary["completed"], 10)
        self.assertEqual(summary["occupied"], 0)
        self.assertLessEqual(summary["max_occupancy"], 6)
        self.assertEqual(summary["cancelled"], 0)

    def test_stop_releases_all_spaces(self) -> None:
        controller = ParkingController(
            capacity=2, arrival_range=(0.0, 0.0), parking_range=(1.0, 1.0)
        )
        controller.start(vehicle_count=12)
        controller.stop()
        self.assertTrue(controller.join(timeout=5))
        self.assertEqual(controller.parking.occupied, 0)
        self.assertLessEqual(controller.parking.max_occupancy, 2)

    def test_start_only_once(self) -> None:
        controller = ParkingController(
            capacity=1, arrival_range=(0.0, 0.0), parking_range=(0.0, 0.0)
        )
        controller.start(1)
        self.assertTrue(controller.join(timeout=5))
        with self.assertRaises(RuntimeError):
            controller.start(1)


if __name__ == "__main__":
    unittest.main()
