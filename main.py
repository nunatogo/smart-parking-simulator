"""Demostración por consola del simulador (etapa 2)."""

from queue import Empty

from src.controllers.parking_controller import ParkingController


def main() -> None:
    controller = ParkingController(capacity=6)
    print("Smart Parking Simulator | 6 espacios | 10 vehículos")
    print("Iniciando simulación concurrente...\n")
    controller.start(vehicle_count=10)

    # La cola también será consumida por Tkinter en la siguiente etapa.
    # join se usa aquí porque se trata de una aplicación de consola.
    controller.join()
    while True:
        try:
            event = controller.events.get_nowait()
        except Empty:
            break
        print(f"[{event.occupied}/{event.capacity}] {event.message}")

    metrics = controller.summary()
    print("\nResumen:")
    print(f"  Vehículos completados: {metrics['completed']}")
    print(f"  Máxima ocupación: {metrics['max_occupancy']}/{metrics['capacity']}")
    print(f"  Cupos ocupados al terminar: {metrics['occupied']}")
    print(f"  Espera promedio: {metrics['average_wait_seconds']:.3f} s")


if __name__ == "__main__":
    main()
