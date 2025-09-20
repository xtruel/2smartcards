"""Utility di supporto per creare l'eseguibile di Barcode Manager."""
from __future__ import annotations

import pathlib
import sys

try:
    import PyInstaller.__main__  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyInstaller non è installato. Esegui 'pip install pyinstaller'.") from exc

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent


def build() -> None:
    PyInstaller.__main__.run(
        [
            "--name",
            "BarcodeManager",
            "--onefile",
            "--windowed",
            "--clean",
            str(PROJECT_ROOT / "barcode_gui.py"),
        ]
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in {"build", "pyinstaller"}:
        raise SystemExit("Uso: python setup.py [build]")
    build()
