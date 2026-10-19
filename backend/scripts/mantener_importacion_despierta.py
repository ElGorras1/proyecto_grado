"""Evita suspensión automática mientras vive un importador concreto (Windows).

No modifica el plan de energía ni mantiene la pantalla encendida. Al terminar el
proceso libera la solicitud; apagar/suspender manualmente sigue siendo posible.
"""

import argparse
import ctypes
from ctypes import wintypes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    args = parser.parse_args()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.SetThreadExecutionState.argtypes = [wintypes.DWORD]
    kernel.SetThreadExecutionState.restype = wintypes.DWORD
    handle = kernel.OpenProcess(0x100000, False, args.pid)  # SYNCHRONIZE; sin modificar el proceso
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not kernel.SetThreadExecutionState(0x80000001):
            raise ctypes.WinError(ctypes.get_last_error())
        print("Solicitud temporal de energía activa para el importador", flush=True)
        while True:
            resultado = kernel.WaitForSingleObject(handle, 10000)
            if resultado == 0:
                break
            if resultado != 258:
                raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.SetThreadExecutionState(0x80000000)
        kernel.CloseHandle(handle)
    print("Importador terminó; solicitud de energía liberada", flush=True)


if __name__ == "__main__":
    main()
