"""Control del ciclo de vida de hilos y de una sesión de simulación.

Cada Vehicle se ejecuta en un Thread; ParkingService administra recursos.
La interfaz Tkinter no necesita conocer la implementación de los hilos:
consume los eventos desde la cola compartida con este controlador.
"""

from queue import Queue
from random import Random
from threading import Event, Lock, Thread
from typing import Optional

from src.models.vehicle import Vehicle, VehicleStatus
from src.services.parking_service import ParkingService


class ParkingController:
    """Coordina una sesión de vehículos con llegadas y estadías aleatorias.

    Una instancia se inicia una sola vez. Para reiniciar, la GUI espera
    que finalicen los hilos y construye un controlador nuevo.
    _state_lock protege el inicio, IDs y registro de nuevos hilos.
    """

    def __init__(
        self,
        capacity: int = 6,
        arrival_range: tuple[float, float] = (0.01, 0.10),
        parking_range: tuple[float, float] = (0.10, 0.25),
        seed: Optional[int] = 42,
    ) -> None:
        """Configura capacidad y tiempos de simulación.

        Args:
            capacity: Máximo simultáneo de vehículos estacionados.
            arrival_range: Intervalo mínimo/máximo de espera inicial (s).
            parking_range: Intervalo mínimo/máximo de estancia (s).
            seed: Semilla para repetir las duraciones por vehículo.
        Raises:
            ValueError: Si un intervalo es negativo o está invertido.
        """
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
        self._next_vehicle_id = 1
        self._arrival_range = arrival_range
        self._parking_range = parking_range
        self._seed = seed

    def start(self, vehicle_count: int = 10) -> None:
        """Inicia la sesión y crea los hilos iniciales.

        Args:
            vehicle_count: Cantidad inicial no negativa.
        Raises:
            RuntimeError: Si ya se inició esta instancia.
            ValueError: Si la cantidad es negativa.
        """
        if vehicle_count < 0:
            raise ValueError("vehicle_count no puede ser negativo.")
        with self._state_lock:
            if self._started:
                raise RuntimeError("Esta simulación ya fue iniciada.")
            self._started = True
        for _ in range(vehicle_count):
            self.add_vehicle()

    def add_vehicle(self) -> Vehicle:
        """Crea y arranca un hilo adicional durante una sesión activa.

        El lock impide repetir identificadores y protege el registro
        de los hilos. Random con semilla propia por vehículo permite
        reproducir las duraciones sin compartir un generador aleatorio.
        Returns:
            Vehículo creado.
        Raises:
            RuntimeError: Si la sesión aún no comenzó o está deteniéndose.
        """
        with self._state_lock:
            if not self._started or self.stop_event.is_set():
                raise RuntimeError("La simulación no está activa.")
            vehicle = Vehicle(self._next_vehicle_id)
            self._next_vehicle_id += 1
            self.vehicles.append(vehicle)
            rng = Random(None if self._seed is None else self._seed + vehicle.vehicle_id)
            thread = Thread(
                target=self._run_vehicle,
                args=(vehicle, rng.uniform(*self._arrival_range), rng.uniform(*self._parking_range)),
                name=f"vehicle-{vehicle.vehicle_id}",
            )
            self._threads.append(thread)
            thread.start()
            return vehicle

    @property
    def is_running(self) -> bool:
        """Indica si queda algún hilo vivo; útil antes de reiniciar la GUI."""
        with self._state_lock:
            return any(thread.is_alive() for thread in self._threads)

    @property
    def started(self) -> bool:
        """Informa si ya se abrió la sesión, aunque sus hilos hayan terminado."""
        with self._state_lock:
            return self._started

    def _run_vehicle(self, vehicle: Vehicle, arrival_delay: float, parking_delay: float) -> None:
        """Ejecuta el ciclo individual: llegada, espera, ingreso y salida.

        Event.wait() permite interrumpir las esperas cuando se detiene
        la simulación. El bloque finally garantiza la liberación del cupo
        cuando el vehículo logró estacionarse.
        """
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
        """Solicita detención cooperativa sin bloquear Tkinter.

        No mata hilos: activa stop_event para que los vehículos en espera
        cancelen y los estacionados liberen sus cupos de forma ordenada.
        """
        self.stop_event.set()

    def join(self, timeout: Optional[float] = None) -> bool:
        """Espera a los hilos desde consola o pruebas; no usar desde Tkinter.

        Args:
            timeout: Plazo máximo total en segundos, o None sin límite.
        Returns:
            True si todos finalizaron; False si persisten hilos vivos.
        """
        from time import monotonic

        deadline = None if timeout is None else monotonic() + timeout
        for thread in self._threads:
            remaining = None if deadline is None else max(0.0, deadline - monotonic())
            thread.join(remaining)
        return all(not thread.is_alive() for thread in self._threads)

    def summary(self) -> dict:
        """Combina la fotografía del parqueadero con estadísticas de sesión.

        Incluye cantidad creada, completados, cancelados y media de
        espera (en segundos). Preferentemente consultar después de join()
        para obtener métricas finales de la sesión.
        """
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
