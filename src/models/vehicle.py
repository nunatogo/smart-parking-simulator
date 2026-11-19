"""Modelo del vehículo y estados de la simulación."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VehicleStatus(str, Enum):
    CREATED = "creado"
    WAITING = "esperando"
    PARKED = "estacionado"
    FINISHED = "finalizado"
    CANCELLED = "cancelado"


@dataclass
class Vehicle:
    """Representa un vehículo atendido por un hilo independiente."""

    vehicle_id: int
    status: VehicleStatus = VehicleStatus.CREATED
    arrival_time: Optional[float] = None
    entry_time: Optional[float] = None
    exit_time: Optional[float] = None
    wait_time: float = 0.0
    assigned_space: Optional[int] = None

    @property
    def label(self) -> str:
        return f"V{self.vehicle_id:03d}"
