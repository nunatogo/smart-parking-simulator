# Smart Parking Simulator

Proyecto final de **Arquitectura de Computadores y Sistemas Operativos** (Universidad EAN).

Simulador de parqueadero inteligente con hilos de Python, sincronizacion mediante semaforos y locks e interfaz grafica Tkinter.

## Estado del proyecto

**Etapa 4: metricas, exportacion CSV y pruebas de carga implementadas; pendientes de validacion local.** La interfaz Tkinter fue ejecutada correctamente por la estudiante y las 10 pruebas de la etapa 3 pasaron en Windows.

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
├── main.py                   # Simulacion concurrente por consola
├── src/
│   ├── models/               # Vehiculos y estados
│   ├── services/             # Cupos, semaforos, locks, eventos
│   ├── controllers/          # Coordinacion de la simulacion
│   └── views/                # GUI Tkinter (parking_gui.py)
├── scripts/
│   └── check_environment.py  # Diagnostico de Python y Tkinter
├── tests/                    # Pruebas de capacidad y concurrencia
├── docs/                     # Informe y capturas
├── logs/                     # Archivos de eventos generados (ignorados por Git)
├── requirements.txt          # Sin dependencias externas en etapa 1
└── .gitignore
```

## Actualizar y ejecutar la etapa 2 (Windows / PowerShell)

Abre la terminal de **Visual Studio Code** en la raiz del repositorio. Si ya clonaste el proyecto, no es necesario volver a ejecutar `git clone`.

**1. Actualizar los archivos desde GitHub:**

```powershell
git pull origin main
```

**2. Ejecutar la simulacion por consola:**

```powershell
.\.venv\Scripts\python.exe main.py
```

**3. Abrir el parqueadero con interfaz Tkinter:**

```powershell
.\.venv\Scripts\python.exe main.py --gui
```

**4. Ejecutar todas las pruebas automatizadas:**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Estos comandos usan directamente el Python del entorno virtual; no necesitas activar `.venv`. Si aun no existe, crealo con `py -3.13 -m venv .venv` (o utiliza `-3.14` si esa es tu version instalada).

La simulacion por consola crea **10 hilos de vehiculos que compiten por 6 cupos**. La salida muestra eventos de entrada y salida y un resumen con la ocupacion maxima, los vehiculos finalizados y el tiempo promedio de espera. La GUI presenta el mismo concepto visualmente. Los tiempos de llegada y estacionamiento son mayores en la GUI para poder observar los cambios.

### Clases de la etapa 2

| Archivo | Responsabilidad |
| --- | --- |
| `src/models/vehicle.py` | Modelo `Vehicle`: identificador, estado, horas de llegada/ingreso/salida y tiempo de espera. Enum `VehicleStatus`. |
| `src/services/parking_service.py` | `ParkingService`: capacidad, asignacion y liberacion de cupos; `BoundedSemaphore` limita entradas y `Lock` protege el estado. Publica `ParkingEvent` en una cola. |
| `src/controllers/parking_controller.py` | `ParkingController`: crea un `Thread` por vehiculo, coordina llegadas y salidas, solicita detencion con `Event` y calcula indicadores. |
| `main.py` | Punto de entrada: consola por defecto o GUI con `--gui`. |\n| `src/views/parking_gui.py` | Panel Tkinter con ocupacion, cupos, registros, botones y lectura de `queue.Queue` con `after()` en el hilo principal. |

### Pruebas automatizadas

- `tests/test_parking_service.py`: valida capacidad positiva, cupos y liberacion, proteccion contra doble salida y vehiculos duplicados.
- `tests/test_concurrency.py`: simula 10 vehiculos en 6 cupos, comprueba la liberacion despues de detener y evita iniciar dos veces el mismo controlador.\n- `tests/test_dynamic_vehicles.py`: comprueba agregar vehiculos en una sesion activa, impedir adiciones despues de detener y permitir sesiones nuevas con otro controlador.
- `tests/test_metrics.py`: valida estadisticas de ocupacion, espera, liberacion, carga de 50 vehiculos y detencion concurrente.

**Importante:** que los archivos de prueba existan en GitHub no garantiza que hayan pasado en tu computador. Comprueba el resultado del comando `unittest` y revisa cualquier error antes de avanzar con la GUI.

## Proximas etapas

1. [Completada] Logica de capacidad y vehiculos con estados.
2. [Completada] Concurrencia segura usando `threading.BoundedSemaphore`, `threading.Lock`, `threading.Event` y `queue.Queue`.
3. [Validacion inicial correcta en Windows] GUI Tkinter actualizada solo desde el hilo principal con `after()`.
4. [Implementada, pendiente de pruebas nuevas en Windows] Metricas en vivo, alerta visual de lleno, exportacion CSV y pruebas de carga.
5. Informe PDF de dos paginas, captura y video explicativo de 3–5 minutos.

## Nota

Nunca subir `.venv/`, archivos temporales ni datos personales al repositorio.

## Uso de los controles de la GUI

- **Iniciar simulacion:** crea 10 vehiculos que intentan ocupar 6 espacios.
- **Agregar vehiculo:** crea un nuevo hilo en la sesion activa, incluso si los primeros vehiculos ya finalizaron.
- **Detener:** solicita cancelacion cooperativa; los vehiculos estacionados liberan sus cupos antes de terminar.
- **Reiniciar:** detiene y espera la salida de todos los hilos antes de recrear el controlador y limpiar los indicadores.
- **Cerrar ventana:** solicita una salida segura antes de destruir la GUI.
- **Exportar CSV:** guarda eventos de la sesion actual; el archivo incluye fecha/hora, tipo, vehiculo, espacio y ocupacion.

Los hilos secundarios no modifican directamente widgets de Tkinter. Publican eventos y el hilo principal los consume con `after()`. El boton de reinicio no debe ejecutarse hasta que se liberen todos los cupos.

## Validacion pendiente

Las **10 pruebas de la etapa 3** fueron ejecutadas correctamente por la estudiante en Windows y la GUI se abrio bien. Las **4 pruebas nuevas** de la etapa 4 y sus interacciones visuales requieren nueva comprobacion local. Al informar incidencias, copia el error de la terminal o adjunta una captura.

## Etapa 4: estadisticas e historial

- **Atendidos:** vehiculos que completaron su estancia y salieron.
- **Espera promedio:** segundos transcurridos entre la llegada registrada y la entrada, calculados para vehiculos finalizados.
- **Ocupacion:** porcentaje de espacios ocupados en el momento de consulta.
- **Maxima ocupacion:** mayor cantidad simultanea de vehiculos estacionados.
- **Alerta de lleno:** mensaje en el registro cuando se alcanza la capacidad.
- **Exportacion CSV:** boton **Exportar CSV**, habilitado si existen eventos de la sesion actual. Usa el selector de archivos de Windows y codificacion UTF-8 con BOM para mejorar la lectura en Excel.

### Comprobaciones manuales sugeridas

1. Ejecuta `.\.venv\Scripts\python.exe main.py --gui` y selecciona **Iniciar simulacion**.
2. Comprueba que los contadores cambian, que ocupados + libres = 6 y que la ocupacion nunca supera 100%.
3. Agrega vehiculos mientras la simulacion esta activa y comprueba los eventos de entrada y salida.
4. Haz clic en **Exportar CSV** y abre el resultado en Excel; comprueba encabezados y registros.
5. Selecciona **Detener** y luego **Reiniciar**; verifica que todos los espacios queden libres y se limpien los eventos.
6. Ejecuta todas las pruebas: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`.

No se ha validado aun el renderizado de la nueva version en Windows. No se necesita instalar bibliotecas externas.
