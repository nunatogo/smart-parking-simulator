"""Pruebas de estadísticas e invariantes bajo concurrencia elevada."""

import unittest
from threading import Event

from src.controllers.parking_controller import ParkingController
from src.models.vehicle import Vehicle
from src.services.parking_service import ParkingService


class MetricsTest(unittest.TestCase):
    def test_initial_snapshot_has_consistent_statistics(self) -> None:
        service = ParkingService(6)
        state = service.snapshot()
        self.assertEqual(state["completed"], 0)
        self.assertEqual(state["cancelled"], 0)
        self.assertEqual(state["average_wait_seconds"], 0)
        self.assertEqual(state["occupancy_percent"], 0)
        self.assertEqual(state["max_occupancy"], 0)

    def test_full_occupancy_and_completed_metrics(self) -> None:
        service = ParkingService(2)
        first, second = Vehicle(1), Vehicle(2)
        service.register(first)
        service.register(second)
        self.assertTrue(service.enter(first, Event()))
        self.assertTrue(service.enter(second, Event()))
        full = service.snapshot()
        self.assertEqual(full["occupancy_percent"], 100)
        self.assertEqual(full["max_occupancy"], 2)

        service.leave(first)
        service.leave(second)
        ended = service.snapshot()
        self.assertEqual(ended["occupied"], 0)
        self.assertEqual(ended["completed"], 2)
        self.assertGreaterEqual(ended["average_wait_seconds"], 0)

    def test_heavy_load_never_exceeds_capacity(self) -> None:
        controller = ParkingController(
            capacity=3, arrival_range=(0.0, 0.0), parking_range=(0.001, 0.003)
        )
        controller.start(50)
        self.assertTrue(controller.join(timeout=10))
        metrics = controller.summary()
        self.assertEqual(metrics["completed"], 50)
        self.assertEqual(metrics["occupied"], 0)
        self.assertLessEqual(metrics["max_occupancy"], 3)
        self.assertEqual(metrics["available"], 3)

    def test_stop_during_high_load_leaves_no_occupied_spaces(self) -> None:
        controller = ParkingController(
            capacity=2, arrival_range=(0.0, 0.0), parking_range=(0.1, 0.2)
        )
        controller.start(20)
        controller.stop()
        self.assertTrue(controller.join(timeout=10))
        state = controller.parking.snapshot()
        self.assertEqual(state["occupied"], 0)
        self.assertEqual(state["available"], 2)
        self.assertLessEqual(state["max_occupancy"], 2)


if __name__ == "__main__":
    unittest.main()
