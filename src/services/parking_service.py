"""Gestión concurrente de cupos y comunicación de eventos.

Este módulo es el equivalente a la administración de recursos de un
sistema operativo: un semáforo limita la cantidad de accesos simultáneos
y un lock protege las secciones críticas que modifican el estado.
"""

from dataclasses import dataclass
from queue import Queue
from threading import BoundedSemaphore, Lock, Event
from time import monotonic
from typing import Optional

from src.models.vehicle import Vehicle, VehicleStatus


@dataclass(frozen=True)
class ParkingEvent:
    """Registro inmutable de una transición del parqueadero.

    Attributes:
        kind: Tipo de evento (waiting, entered, left, cancelled).
        vehicle_id: Identificador del vehículo involucrado.
        occupied: Cantidad de cupos ocupados al emitir el evento.
        capacity: Capacidad total del parqueadero.
        timestamp: Instante monotónico del evento.
        message: Descripción legible para consola o GUI.
        space: Cupo relacionado, cuando aplica.

    Los eventos viajan por Queue para que la GUI no sea modificada
    desde los hilos de vehículos.
    """

    kind: str
    vehicle_id: int
    occupied: int
    capacity: int
    timestamp: float
    message: str
    space: Optional[int] = None


class ParkingService:
    """Fuente central de verdad sobre ocupación y estados.

    BoundedSemaphore(capacity) controla cuántos vehículos pueden
    estacionarse a la vez. Lock serializa la actualización del mapa
    espacio -> vehículo y de los estados; estas operaciones forman
    secciones críticas. Los métodos públicos son utilizados desde hilos
    distintos, por lo que nunca se deben manipular _spaces o _vehicles
    directamente desde el controlador o la interfaz.
    """

    def __init__(self, capacity: int, events: Optional[Queue] = None) -> None:
        """Inicializa cupos, herramientas de sincronización y cola de eventos.

        Args:
            capacity: Número positivo de plazas.
            events: Cola compartida opcional; se crea una si no se recibe.
        Raises:
            ValueError: Si capacity no es positivo.
        """
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
        """Cantidad actual de cupos ocupados, leída bajo exclusión mutua."""
        with self._lock:
            return len(self._spaces)

    @property
    def available(self) -> int:
        """Cupos disponibles calculados a partir de la ocupación segura."""
        return self.capacity - self.occupied

    def snapshot(self) -> dict:
        """Obtiene una fotografía consistente para UI, métricas y pruebas.

        Returns:
            Diccionario con capacidad, ocupación, espacios, estados,
            estadísticas de vehículos terminados y porcentaje de uso.
            La media de espera incluye solo vehículos finalizados.
        """
        with self._lock:
            return {
                "capacity": self.capacity,
                "occupied": len(self._spaces),
                "available": self.capacity - len(self._spaces),
                "spaces": dict(self._spaces),
                "statuses": {vid: v.status.value for vid, v in self._vehicles.items()},
                "max_occupancy": self.max_occupancy,
                "completed": sum(v.status == VehicleStatus.FINISHED for v in self._vehicles.values()),
                "cancelled": sum(v.status == VehicleStatus.CANCELLED for v in self._vehicles.values()),
                "average_wait_seconds": (
                    sum(v.wait_time for v in self._vehicles.values()
                        if v.status == VehicleStatus.FINISHED)
                    / max(1, sum(v.status == VehicleStatus.FINISHED
                                 for v in self._vehicles.values()))
                ),
                "occupancy_percent": 100 * len(self._spaces) / self.capacity,
            }

    def register(self, vehicle: Vehicle) -> None:
        """Registra la llegada e inicia el estado WAITING.

        Args:
            vehicle: Instancia aún no registrada.
        Raises:
            ValueError: Si el identificador ya está registrado.
        """
        with self._lock:
            if vehicle.vehicle_id in self._vehicles:
                raise ValueError("ID de vehículo duplicado.")
            self._vehicles[vehicle.vehicle_id] = vehicle
            vehicle.arrival_time = monotonic()
            vehicle.status = VehicleStatus.WAITING
            self._emit_locked("waiting", vehicle, "está esperando un cupo")

    def enter(self, vehicle: Vehicle, stop: Event, poll_interval: float = 0.05) -> bool:
        """Solicita un cupo sin perder capacidad de cancelación.

        El semáforo autoriza la entrada antes de asignar un espacio.
        Tras adquirirlo, el lock impide que dos hilos asignen el mismo
        espacio. Si se solicita detener, se devuelve el permiso obtenido.

        Args:
            vehicle: Vehículo registrado con estado WAITING.
            stop: Evento que solicita la detención cooperativa.
            poll_interval: Tiempo máximo, en segundos, por intento acquire.
        Returns:
            True si se asignó el cupo; False si llegó la detención.
        Raises:
            ValueError: Si el intervalo o el estado del vehículo es inválido.
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
        """Finaliza el estacionamiento y devuelve un permiso al semáforo.

        Dentro del lock elimina la asignación, marca al vehículo como
        FINISHED y emite un evento. Evita una doble liberación, que
        desconfiguraría el control de capacidad.
        Raises:
            ValueError: Si el vehículo no está estacionado.
            RuntimeError: Si la asignación interna es inconsistente.
        """
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
        """Cancela una solicitud antes de ingresar.

        Los vehículos estacionados deben salir usando leave(), porque
        solamente ese método devuelve el cupo que ocuparon.
        """
        with self._lock:
            if vehicle.status in (VehicleStatus.CREATED, VehicleStatus.WAITING):
                vehicle.status = VehicleStatus.CANCELLED
                self._emit_locked("cancelled", vehicle, "cancelado")

    def _emit_locked(self, kind: str, vehicle: Vehicle, message: str, space: Optional[int] = None) -> None:
        """Publica un evento en Queue mientras el estado está protegido.

        Uso interno: quien invoque este método debe mantener _lock.
        Así la ocupación incluida en el evento es consistente con el
        cambio de estado que acaba de producirse.
        """
        self.events.put(ParkingEvent(
            kind=kind,
            vehicle_id=vehicle.vehicle_id,
            occupied=len(self._spaces),
            capacity=self.capacity,
            timestamp=monotonic(),
            message=f"{vehicle.label} {message}",
            space=space if space is not None else vehicle.assigned_space,
        ))
