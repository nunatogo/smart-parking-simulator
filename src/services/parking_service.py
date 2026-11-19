"""Gestión segura de los espacios de un parqueadero concurrente."""

from dataclasses import dataclass
from queue import Queue
from threading import BoundedSemaphore, Lock, Event
from time import monotonic
from typing import Optional

from src.models.vehicle import Vehicle, VehicleStatus


@dataclass(frozen=True)
class ParkingEvent:
    """Evento consumible por consola o por la futura interfaz Tkinter."""

    kind: str
    vehicle_id: int
    occupied: int
    capacity: int
    timestamp: float
    message: str
    space: Optional[int] = None


class ParkingService:
    """Administra cupos con semáforo y protege cambios con Lock.

    Un vehículo solo puede ocupar un cupo después de adquirir el semáforo.
    El lock mantiene consistente el contador, los lugares y los estados.
    """

    def __init__(self, capacity: int, events: Optional[Queue] = None) -> None:
        if capacity <= 0:
            raise ValueError("La capacidad debe ser mayor que cero.")
        self.capacity = capacity
        self.events: Queue = events if events is not None else Queue()
        self._semaphore = BoundedSemaphore(capacity)
        self._lock = Lock()
        self._spaces: dict[int, int] = {}  # espacio -> id de vehículo
        self._vehicles: dict[int, Vehicle] = {}
        self.max_occupancy = 0

    @property
    def occupied(self) -> int:
        with self._lock:
            return len(self._spaces)

    @property
    def available(self) -> int:
        return self.capacity - self.occupied

    def snapshot(self) -> dict:
        """Devuelve un estado seguro para visualizar o comprobar."""
        with self._lock:
            return {
                "capacity": self.capacity,
                "occupied": len(self._spaces),
                "available": self.capacity - len(self._spaces),
                "spaces": dict(self._spaces),
                "statuses": {vid: v.status.value for vid, v in self._vehicles.items()},
                "max_occupancy": self.max_occupancy,
            }

    def register(self, vehicle: Vehicle) -> None:
        with self._lock:
            if vehicle.vehicle_id in self._vehicles:
                raise ValueError("ID de vehículo duplicado.")
            self._vehicles[vehicle.vehicle_id] = vehicle
            vehicle.arrival_time = monotonic()
            vehicle.status = VehicleStatus.WAITING
            self._emit_locked("waiting", vehicle, "está esperando un cupo")

    def enter(self, vehicle: Vehicle, stop: Event, poll_interval: float = 0.05) -> bool:
        """Espera por un cupo; retorna False cuando se solicita detener.

        acquire(timeout=...) evita una espera indefinida al detener.
        """
        if poll_interval <= 0:
            raise ValueError("poll_interval debe ser positivo.")
        while not stop.is_set():
            if not self._semaphore.acquire(timeout=poll_interval):
                continue
            with self._lock:
                if stop.is_set():
                    self._semaphore.release()
                    return False
                if self._vehicles.get(vehicle.vehicle_id) is not vehicle:
                    self._semaphore.release()
                    raise ValueError("El vehículo no está registrado.")
                if vehicle.status != VehicleStatus.WAITING:
                    self._semaphore.release()
                    raise ValueError("El vehículo no está esperando.")
                space = next(i for i in range(1, self.capacity + 1) if i not in self._spaces)
                self._spaces[space] = vehicle.vehicle_id
                vehicle.assigned_space = space
                vehicle.entry_time = monotonic()
                vehicle.wait_time = vehicle.entry_time - (vehicle.arrival_time or vehicle.entry_time)
                vehicle.status = VehicleStatus.PARKED
                self.max_occupancy = max(self.max_occupancy, len(self._spaces))
                self._emit_locked("entered", vehicle, f"ingresó al espacio {space}")
                return True
        return False

    def leave(self, vehicle: Vehicle) -> None:
        """Libera exactamente una vez el cupo ocupado por el vehículo."""
        with self._lock:
            if vehicle.status != VehicleStatus.PARKED or vehicle.assigned_space is None:
                raise ValueError("El vehículo no está estacionado.")
            space = vehicle.assigned_space
            if self._spaces.get(space) != vehicle.vehicle_id:
                raise RuntimeError("Inconsistencia en la asignación de cupos.")
            del self._spaces[space]
            vehicle.exit_time = monotonic()
            vehicle.assigned_space = None
            vehicle.status = VehicleStatus.FINISHED
            self._emit_locked("left", vehicle, f"salió del espacio {space}", space)
            self._semaphore.release()

    def cancel(self, vehicle: Vehicle) -> None:
        """Marca un vehículo no estacionado como cancelado."""
        with self._lock:
            if vehicle.status in (VehicleStatus.CREATED, VehicleStatus.WAITING):
                vehicle.status = VehicleStatus.CANCELLED
                self._emit_locked("cancelled", vehicle, "cancelado")

    def _emit_locked(self, kind: str, vehicle: Vehicle, message: str, space: Optional[int] = None) -> None:
        self.events.put(ParkingEvent(
            kind=kind,
            vehicle_id=vehicle.vehicle_id,
            occupied=len(self._spaces),
            capacity=self.capacity,
            timestamp=monotonic(),
            message=f"{vehicle.label} {message}",
            space=space if space is not None else vehicle.assigned_space,
        ))
