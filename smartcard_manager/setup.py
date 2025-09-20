"""Utility per creare l'eseguibile standalone con PyInstaller."""
from __future__ import annotations

import pathlib
import sys

try:
    import PyInstaller.__main__  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyInstaller non è installato. Usa 'pip install pyinstaller'.") from exc

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent


def build() -> None:
    """Esegue PyInstaller con le opzioni consigliate per la GUI."""

    PyInstaller.__main__.run(
        [
            "--name",
            "SmartCardManager",
            "--onefile",
            "--windowed",
            "--clean",
            str(PROJECT_ROOT / "smartcard_gui.py"),
        ]
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in {"build", "pyinstaller"}:
        raise SystemExit("Uso: python setup.py [build]")
    build()
