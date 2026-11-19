"""Orquesta hilos de vehículos y su ciclo de entrada/salida."""

from queue import Queue
from random import Random
from threading import Event, Lock, Thread
from typing import Optional

from src.models.vehicle import Vehicle, VehicleStatus
from src.services.parking_service import ParkingService


class ParkingController:
    """Controla una simulación de ejecución única por instancia."""

    def __init__(
        self,
        capacity: int = 6,
        arrival_range: tuple[float, float] = (0.01, 0.10),
        parking_range: tuple[float, float] = (0.10, 0.25),
        seed: Optional[int] = 42,
    ) -> None:
        if arrival_range[0] < 0 or arrival_range[0] > arrival_range[1]:
            raise ValueError("Rango de llegada inválido.")
        if parking_range[0] < 0 or parking_range[0] > parking_range[1]:
            raise ValueError("Rango de estacionamiento inválido.")
        self.events: Queue = Queue()
        self.parking = ParkingService(capacity, events=self.events)
        self.stop_event = Event()
        self.vehicles: list[Vehicle] = []
        self._threads: list[Thread] = []
        self._state_lock = Lock()
        self._started = False
        self._arrival_range = arrival_range
        self._parking_range = parking_range
        self._seed = seed

    def start(self, vehicle_count: int = 10) -> None:
        """Crea un hilo por vehículo y comienza la simulación."""
        if vehicle_count < 0:
            raise ValueError("vehicle_count no puede ser negativo.")
        with self._state_lock:
            if self._started:
                raise RuntimeError("Esta simulación ya fue iniciada.")
            self._started = True
            self.vehicles = [Vehicle(i) for i in range(1, vehicle_count + 1)]
            for vehicle in self.vehicles:
                rng = Random(None if self._seed is None else self._seed + vehicle.vehicle_id)
                thread = Thread(
                    target=self._run_vehicle,
                    args=(vehicle, rng.uniform(*self._arrival_range), rng.uniform(*self._parking_range)),
                    name=f"vehicle-{vehicle.vehicle_id}",
                )
                self._threads.append(thread)
                thread.start()

    def _run_vehicle(self, vehicle: Vehicle, arrival_delay: float, parking_delay: float) -> None:
        # El evento permite detener incluso durante la espera inicial.
        if self.stop_event.wait(arrival_delay):
            self.parking.cancel(vehicle)
            return
        self.parking.register(vehicle)
        entered = self.parking.enter(vehicle, self.stop_event)
        if not entered:
            self.parking.cancel(vehicle)
            return
        try:
            # La salida se adelanta cuando se solicita detener.
            self.stop_event.wait(parking_delay)
        finally:
            self.parking.leave(vehicle)

    def stop(self) -> None:
        """Solicita una finalización cooperativa (no bloquea el hilo GUI)."""
        self.stop_event.set()

    def join(self, timeout: Optional[float] = None) -> bool:
        """Espera hilos fuera del hilo de interfaz; devuelve si terminaron todos."""
        from time import monotonic

        deadline = None if timeout is None else monotonic() + timeout
        for thread in self._threads:
            remaining = None if deadline is None else max(0.0, deadline - monotonic())
            thread.join(remaining)
        return all(not thread.is_alive() for thread in self._threads)

    def summary(self) -> dict:
        """Obtiene métricas al finalizar (o parciales durante ejecución)."""
        snapshot = self.parking.snapshot()
        completed = [v for v in self.vehicles if v.status == VehicleStatus.FINISHED]
        return {
            **snapshot,
            "total_vehicles": len(self.vehicles),
            "completed": len(completed),
            "cancelled": sum(v.status == VehicleStatus.CANCELLED for v in self.vehicles),
            "average_wait_seconds": (
                sum(v.wait_time for v in completed) / len(completed) if completed else 0.0
            ),
        }
