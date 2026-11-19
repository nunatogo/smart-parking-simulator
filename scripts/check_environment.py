"""Verifica la version de Python y la disponibilidad de Tkinter.

Ejecutar desde la raiz del proyecto:
    python scripts/check_environment.py
"""

import platform
import sys


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")
    print(f"Sistema: {platform.platform()}")
    print(f"Ejecutable: {sys.executable}")
    try:
        import tkinter
        import _tkinter
    except ImportError as exc:
        print(f"ERROR: Tkinter no esta disponible: {exc}")
        return 1

    print(f"Tkinter: disponible (Tcl/Tk {_tkinter.TK_VERSION})")
    print("Para comprobar la ventana grafica ejecuta: python -m tkinter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
