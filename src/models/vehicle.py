"""Entidades del dominio del parqueadero inteligente.

Cada vehículo es una unidad de trabajo que ejecuta un hilo gestionado por
ParkingController. Este módulo define sus datos y estados; no adquiere
semáforos ni crea widgets de Tkinter.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VehicleStatus(str, Enum):
    """Etapas observables del ciclo de vida de un vehículo.

    CREATED: hilo todavía no registrado en el parqueadero.
    WAITING: registrado y a la espera de un cupo.
    PARKED: ocupa un espacio asignado por ParkingService.
    FINISHED: salió y liberó su espacio.
    CANCELLED: fue cancelado antes de estacionarse.
    """
    CREATED = "creado"
    WAITING = "esperando"
    PARKED = "estacionado"
    FINISHED = "finalizado"
    CANCELLED = "cancelado"


@dataclass
class Vehicle:
    """Datos de una solicitud de estacionamiento.

    Attributes:
        vehicle_id: Identificador numérico único dentro de la simulación.
        status: Estado actual, actualizado desde ParkingService.
        arrival_time: Instante de registro (segundos de reloj monotónico).
        entry_time: Instante de adquisición efectiva del espacio.
        exit_time: Instante de salida del espacio.
        wait_time: Segundos transcurridos entre registro e ingreso.
        assigned_space: Número de cupo; None cuando no está estacionado.

    Los tiempos monotónicos sirven para calcular duraciones, no fechas del
    calendario. El acceso concurrente al estado debe realizarse mediante
    las operaciones protegidas de ParkingService.
    """

    vehicle_id: int
    status: VehicleStatus = VehicleStatus.CREATED
    arrival_time: Optional[float] = None
    entry_time: Optional[float] = None
    exit_time: Optional[float] = None
    wait_time: float = 0.0
    assigned_space: Optional[int] = None

    @property
    def label(self) -> str:
        """Devuelve una etiqueta legible, por ejemplo V001 o V010."""
        return f"V{self.vehicle_id:03d}"
