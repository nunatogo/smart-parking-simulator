# Smart Parking Simulator

Proyecto final de **Arquitectura de Computadores y Sistemas Operativos** (Universidad EAN).

Simulador de parqueadero inteligente con hilos de Python, sincronizacion mediante semaforos y locks e interfaz grafica Tkinter.

## Estado del proyecto

**Etapa 1: preparacion del entorno y estructura del repositorio.** La logica del simulador y la interfaz definitiva aun no estan implementadas.

## Requisitos

- Windows 10/11 (tambien puede ejecutarse en otros sistemas con Tkinter).
- Python 3.13 o 3.14, instalado desde https://www.python.org/downloads/windows/
- Visual Studio Code y extension **Python** (Microsoft).
- Git.

El proyecto inicial utiliza solo la biblioteca estandar de Python; **no requiere paquetes externos**.

## Instalar Python en Windows

1. Descarga el instalador de **Python 3.13 o 3.14 para Windows (64-bit)** desde la pagina oficial. Si tu PC es ARM, elige el instalador ARM64.
2. Ejecuta el instalador. Si aparece la opcion **Add python.exe to PATH**, activala. Completa la instalacion.
3. Cierra y vuelve a abrir la terminal de VS Code.
4. Comprueba la instalacion:

   ```powershell
   py --list
   py -3.13 --version
   ```

   Si instalaste la version 3.14, sustituye `3.13` por `3.14`.

> Si `py` no funciona, prueba `python --version` y revisa la instalacion. No necesitas desinstalar otras versiones de Python.

## Clonar y configurar el proyecto

```powershell
git clone https://github.com/nunatogo/smart-parking-simulator.git
cd smart-parking-simulator
py -3.13 -m venv .venv
```

Para Python 3.14 cambia `-3.13` por `-3.14`.

Para evitar problemas de politicas de ejecucion de PowerShell, puedes usar el entorno **sin activarlo**:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m tkinter
.\.venv\Scripts\python.exe scripts\check_environment.py
```

El comando `-m tkinter` debe abrir una ventana de prueba. Si no aparece, revisa que tu instalacion de Python incluya Tcl/Tk.

Abre la carpeta en VS Code (`code .`) y selecciona **Python: Select Interpreter > .venv\\Scripts\\python.exe**.

## Estructura

```text
smart-parking-simulator/
├── main.py                   # Punto de entrada (etapas siguientes)
├── src/
│   ├── models/               # Vehiculos y estados
│   ├── services/             # Cupos, semaforos, locks, eventos
│   ├── controllers/          # Coordinacion de la simulacion
│   └── views/                # GUI Tkinter
├── scripts/
│   └── check_environment.py  # Diagnostico de Python y Tkinter
├── tests/                    # Pruebas del simulador
├── docs/                     # Informe y capturas
├── logs/                     # Archivos de eventos generados (ignorados por Git)
├── requirements.txt          # Sin dependencias externas en etapa 1
└── .gitignore
```

## Proximas etapas

1. Logica de capacidad y vehiculos con estados.
2. Concurrencia segura usando `threading.Semaphore`, `threading.Lock`, `threading.Event` y `queue.Queue`.
3. GUI Tkinter actualizada solo desde el hilo principal con `after()`.
4. Pruebas de concurrencia, indicadores y logs.
5. Informe PDF de dos paginas, captura y video explicativo de 3–5 minutos.

## Nota

Nunca subir `.venv/`, archivos temporales ni datos personales al repositorio.
