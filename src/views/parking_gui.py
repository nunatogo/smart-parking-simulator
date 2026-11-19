"""Interfaz gráfica Tkinter del simulador de parqueadero.

Todos los widgets se actualizan exclusivamente desde el hilo principal.
Los hilos de vehículos publican eventos a una Queue.
"""

import tkinter as tk
from datetime import datetime
from queue import Empty
from tkinter import messagebox, scrolledtext, ttk

from src.controllers.parking_controller import ParkingController


class ParkingGUI:
    """Tablero del parqueadero y controles de simulación concurrente."""

    CAPACITY = 6
    INITIAL_VEHICLES = 10
    POLL_MS = 100

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Smart Parking Simulator | Universidad EAN")
        self.root.geometry("940x700")
        self.root.minsize(760, 610)
        self.root.configure(bg="#eff3f9")

        self.controller = self._new_controller()
        self._closing = False
        self._reset_pending = False
        self._space_labels: dict[int, tk.Label] = {}

        self._build_interface()
        self._refresh_view()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(self.POLL_MS, self._poll_events)

    def _new_controller(self) -> ParkingController:
        # Tiempos deliberadamente visibles para la demostración de la GUI.
        return ParkingController(
            capacity=self.CAPACITY,
            arrival_range=(0.5, 2.0),
            parking_range=(3.0, 6.0),
            seed=42,
        )

    def _build_interface(self) -> None:
        header = tk.Frame(self.root, bg="#183153", padx=22, pady=18)
        header.pack(fill="x")
        tk.Label(
            header, text="SMART PARKING", font=("Segoe UI", 22, "bold"),
            bg="#183153", fg="white",
        ).pack(anchor="w")
        tk.Label(
            header, text="Simulador de concurrencia • Python + Tkinter",
            font=("Segoe UI", 10), bg="#183153", fg="#d9e7fa",
        ).pack(anchor="w")

        content = tk.Frame(self.root, bg="#eff3f9", padx=20, pady=14)
        content.pack(fill="both", expand=True)

        metrics = tk.Frame(content, bg="#eff3f9")
        metrics.pack(fill="x", pady=(0, 12))
        self.capacity_text = tk.StringVar()
        self.occupied_text = tk.StringVar()
        self.available_text = tk.StringVar()
        self.waiting_text = tk.StringVar()
        for title, variable in (
            ("CAPACIDAD", self.capacity_text),
            ("OCUPADOS", self.occupied_text),
            ("LIBRES", self.available_text),
            ("EN ESPERA", self.waiting_text),
        ):
            card = tk.Frame(metrics, bg="white", padx=15, pady=12, highlightthickness=1,
                            highlightbackground="#dce3ee")
            card.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(card, text=title, bg="white", fg="#53657b",
                     font=("Segoe UI", 9, "bold")).pack()
            tk.Label(card, textvariable=variable, bg="white", fg="#183153",
                     font=("Segoe UI", 22, "bold")).pack()

        tk.Label(content, text="Espacios del parqueadero",
                 font=("Segoe UI", 14, "bold"), bg="#eff3f9",
                 fg="#183153").pack(anchor="w", pady=(3, 8))

        spaces_frame = tk.Frame(content, bg="#eff3f9")
        spaces_frame.pack(fill="x")
        for index in range(1, self.CAPACITY + 1):
            label = tk.Label(
                spaces_frame, text="", font=("Segoe UI", 12, "bold"),
                width=17, height=4, bg="#d9f5e8", fg="#12674b",
                relief="groove", bd=1,
            )
            label.grid(row=(index - 1) // 3, column=(index - 1) % 3,
                       padx=6, pady=6, sticky="nsew")
            self._space_labels[index] = label
        for column in range(3):
            spaces_frame.columnconfigure(column, weight=1)

        control_frame = tk.Frame(content, bg="#eff3f9")
        control_frame.pack(fill="x", pady=(15, 10))

        self.start_button = ttk.Button(
            control_frame, text="Iniciar simulación", command=self._start
        )
        self.add_button = ttk.Button(
            control_frame, text="Agregar vehículo", command=self._add_vehicle
        )
        self.stop_button = ttk.Button(
            control_frame, text="Detener", command=self._stop
        )
        self.reset_button = ttk.Button(
            control_frame, text="Reiniciar", command=self._reset
        )
        for button in (self.start_button, self.add_button, self.stop_button, self.reset_button):
            button.pack(side="left", padx=(0, 9))

        self.status_text = tk.StringVar(value="Lista para iniciar")
        tk.Label(content, textvariable=self.status_text, bg="#eff3f9",
                 fg="#42526a", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 9))

        tk.Label(content, text="Registro de eventos",
                 font=("Segoe UI", 13, "bold"), bg="#eff3f9",
                 fg="#183153").pack(anchor="w", pady=(0, 5))
        self.log_box = scrolledtext.ScrolledText(
            content, height=9, state="disabled", wrap="word",
            font=("Consolas", 10), bg="white", fg="#27394d",
        )
        self.log_box.pack(fill="both", expand=True)
        self._update_buttons()

    def _log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{timestamp}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _start(self) -> None:
        try:
            self.controller.start(vehicle_count=self.INITIAL_VEHICLES)
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("No se pudo iniciar", str(error))
            return
        self.status_text.set("Simulación en ejecución")
        self._log(f"Simulación iniciada: {self.INITIAL_VEHICLES} vehículos, {self.CAPACITY} cupos.")
        self._update_buttons()

    def _add_vehicle(self) -> None:
        try:
            vehicle = self.controller.add_vehicle()
        except RuntimeError as error:
            messagebox.showwarning("No se puede agregar", str(error))
            return
        self._log(f"{vehicle.label} creado y agregado a la simulación.")
        self._update_buttons()

    def _stop(self) -> None:
        self.controller.stop()
        self.status_text.set("Deteniendo vehículos de forma segura...")
        self._log("Detención solicitada. Liberando espacios ocupados.")
        self._update_buttons()

    def _reset(self) -> None:
        if self._reset_pending:
            return
        self._reset_pending = True
        self.status_text.set("Reiniciando de manera segura...")
        if self.controller.started:
            self.controller.stop()
        self._update_buttons()

    def _finish_reset(self) -> None:
        self.controller = self._new_controller()
        self._reset_pending = False
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self.status_text.set("Lista para iniciar")
        self._refresh_view()
        self._update_buttons()

    def _poll_events(self) -> None:
        # Se ejecuta solo en el hilo Tkinter, nunca desde los hilos de vehículos.
        for _ in range(150):
            try:
                event = self.controller.events.get_nowait()
            except Empty:
                break
            self._log(f"{event.message} | ocupación: {event.occupied}/{event.capacity}")

        self._refresh_view()
        if self._reset_pending and not self.controller.is_running:
            self._finish_reset()
        elif self._closing and not self.controller.is_running:
            self.root.destroy()
            return
        elif self.controller.started and not self.controller.is_running:
            if self.controller.stop_event.is_set():
                self.status_text.set("Simulación detenida")
            else:
                self.status_text.set("Vehículos iniciales finalizados; puedes agregar más o reiniciar")
        self._update_buttons()
        self.root.after(self.POLL_MS, self._poll_events)

    def _refresh_view(self) -> None:
        state = self.controller.parking.snapshot()
        self.capacity_text.set(str(state["capacity"]))
        self.occupied_text.set(str(state["occupied"]))
        self.available_text.set(str(state["available"]))
        self.waiting_text.set(str(sum(
            status == "esperando" for status in state["statuses"].values()
        )))
        for number, label in self._space_labels.items():
            vehicle_id = state["spaces"].get(number)
            if vehicle_id is None:
                label.configure(text=f"ESPACIO {number}\nLIBRE", bg="#d9f5e8", fg="#12674b")
            else:
                label.configure(
                    text=f"ESPACIO {number}\nV{vehicle_id:03d}\nOCUPADO",
                    bg="#ffdfb1", fg="#8f4a00",
                )

    def _update_buttons(self) -> None:
        started = self.controller.started
        stopping = self.controller.stop_event.is_set()
        busy = self._reset_pending or self._closing
        self.start_button.configure(state="normal" if not started and not busy else "disabled")
        self.add_button.configure(state="normal" if started and not stopping and not busy else "disabled")
        self.stop_button.configure(state="normal" if started and not stopping and not busy else "disabled")
        self.reset_button.configure(state="disabled" if busy else "normal")

    def _on_close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.status_text.set("Cerrando de forma segura...")
        self.controller.stop()
        self._update_buttons()
        # _poll_events cerrará la ventana cuando ya no haya hilos activos.


def launch_gui() -> None:
    root = tk.Tk()
    ParkingGUI(root)
    root.mainloop()
