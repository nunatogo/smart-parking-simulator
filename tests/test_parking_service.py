"""Pruebas de capacidad, validaciones y liberación de espacios."""

import unittest
from threading import Event

from src.models.vehicle import Vehicle, VehicleStatus
from src.services.parking_service import ParkingService


class ParkingServiceTest(unittest.TestCase):
    def test_capacity_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            ParkingService(0)

    def test_entry_never_exceeds_capacity_and_release_frees_space(self) -> None:
        service = ParkingService(1)
        first = Vehicle(1)
        second = Vehicle(2)
        service.register(first)
        service.register(second)

        self.assertTrue(service.enter(first, Event(), poll_interval=0.001))
        self.assertEqual(service.occupied, 1)
        self.assertEqual(first.status, VehicleStatus.PARKED)

        cancelled = Event()
        cancelled.set()
        self.assertFalse(service.enter(second, cancelled, poll_interval=0.001))
        self.assertEqual(service.occupied, 1)

        service.leave(first)
        self.assertEqual(service.occupied, 0)
        self.assertTrue(service.enter(second, Event(), poll_interval=0.001))
        service.leave(second)
        self.assertEqual(service.max_occupancy, 1)
        self.assertEqual(service.available, 1)

    def test_cannot_release_twice(self) -> None:
        service = ParkingService(1)
        vehicle = Vehicle(1)
        service.register(vehicle)
        service.enter(vehicle, Event(), poll_interval=0.001)
        service.leave(vehicle)
        with self.assertRaises(ValueError):
            service.leave(vehicle)

    def test_duplicate_vehicle_rejected(self) -> None:
        service = ParkingService(2)
        service.register(Vehicle(1))
        with self.assertRaises(ValueError):
            service.register(Vehicle(1))


if __name__ == "__main__":
    unittest.main()
