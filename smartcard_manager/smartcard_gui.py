"""Interfaccia minimale per la gestione delle smart card."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from PyQt5 import QtCore, QtWidgets

try:  # pragma: no cover - optional dependency for runtime use only
    from smartcard.Exceptions import CardConnectionException, NoCardException
    from smartcard.System import readers
    from smartcard.util import toBytes, toHexString
except ImportError:  # pragma: no cover - allow the GUI to start without pyscard
    readers = None

    class CardConnectionException(Exception):
        """Fallback exception used when :mod:`pyscard` is unavailable."""

    class NoCardException(CardConnectionException):
        """Raised when no card is present in the reader."""

    def toBytes(value: str) -> List[int]:
        clean = value.replace(" ", "")
        if len(clean) % 2:
            raise ValueError("Hex string must contain an even number of characters")
        return [int(clean[i : i + 2], 16) for i in range(0, len(clean), 2)]

    def toHexString(data: Sequence[int]) -> str:
        return " ".join(f"{byte:02X}" for byte in data)


LOG_FILE = Path(__file__).with_name("logs.txt")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("smartcard_manager")
if not logger.handlers:
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


ATR_FALLBACK = "3B 13 00 81 31 FE 45 80 31 C0 64 B0 01 00"


class SmartCardBackend(QtCore.QObject):
    """Incapsula la logica di basso livello e registra i dettagli su file."""

    def __init__(self) -> None:
        super().__init__()
        self.connection = None
        self.connected_reader = None

    def available_readers(self) -> List[str]:
        if readers is None:
            logger.warning("pyscard non disponibile: impossibile elencare i lettori")
            return []
        try:
            reader_list = [str(reader) for reader in readers()]
            logger.info("Lettori trovati: %s", reader_list)
            return reader_list
        except Exception as exc:  # pragma: no cover - runtime safeguard
            logger.exception("Errore durante l'elenco dei lettori: %s", exc)
            return []

    def connect(self, reader_name: str) -> Optional[str]:
        if readers is None:
            raise RuntimeError("pyscard non disponibile")
        for reader in readers():
            if str(reader) == reader_name:
                connection = reader.createConnection()
                try:
                    connection.connect()
                except Exception as exc:
                    logger.exception("Connessione al lettore %s fallita", reader_name)
                    raise
                self.connection = connection
                self.connected_reader = reader
                atr = getattr(connection, "getATR", lambda: None)()
                if atr:
                    atr_text = toHexString(atr)
                    logger.info("ATR letto: %s", atr_text)
                    return atr_text
                logger.info("ATR non disponibile per il lettore %s", reader_name)
                return None
        raise RuntimeError("lettore non trovato")

    def disconnect(self) -> None:
        if self.connection:
            try:
                self.connection.disconnect()
                logger.info("Connessione al lettore chiusa")
            except Exception:  # pragma: no cover - best effort cleanup
                logger.exception("Errore in fase di disconnessione")
        self.connection = None
        self.connected_reader = None

    def transmit_apdu(self, apdu_hex: str) -> Sequence[int]:
        if not self.connection:
            raise RuntimeError("nessuna connessione attiva")
        apdu_bytes = toBytes(apdu_hex)
        logger.info("APDU inviata: %s", toHexString(apdu_bytes))
        try:
            response = self.connection.transmit(apdu_bytes)
        except NoCardException as exc:
            logger.exception("Nessuna card presente durante la trasmissione")
            raise
        except CardConnectionException as exc:
            logger.exception("Errore di connessione durante la trasmissione APDU")
            raise
        data, sw1, sw2 = response
        logger.info("Risposta APDU: dati=%s SW=%02X %02X", toHexString(data), sw1, sw2)
        return response

    def read_card_dump(self, length: int = 256, block_size: int = 16) -> List[List[int]]:
        if not self.connection:
            raise RuntimeError("nessuna connessione attiva")
        dump: List[List[int]] = []
        for offset in range(0, length, block_size):
            apdu = [0x00, 0xB0, (offset >> 8) & 0xFF, offset & 0xFF, block_size]
            logger.info("Lettura blocco offset %04X con APDU %s", offset, toHexString(apdu))
            data, sw1, sw2 = self.connection.transmit(apdu)
            if (sw1, sw2) != (0x90, 0x00):
                logger.error(
                    "Errore lettura offset %04X: status %02X %02X", offset, sw1, sw2
                )
                raise RuntimeError("lettura fallita")
            logger.info("Blocco %04X letto: %s", offset, toHexString(data))
            dump.append(data)
        return dump

    def write_card_dump(self, dump: Sequence[Sequence[int]]) -> None:
        if not self.connection:
            raise RuntimeError("nessuna connessione attiva")
        offset = 0
        for block in dump:
            length = len(block)
            apdu = [0x00, 0xD0, (offset >> 8) & 0xFF, offset & 0xFF, length, *block]
            logger.info("Scrittura blocco %04X con APDU %s", offset, toHexString(apdu))
            data, sw1, sw2 = self.connection.transmit(apdu)
            if (sw1, sw2) != (0x90, 0x00):
                logger.error(
                    "Errore scrittura offset %04X: status %02X %02X", offset, sw1, sw2
                )
                raise RuntimeError("scrittura fallita")
            logger.info("Blocco %04X scritto, risposta %s", offset, toHexString(data))
            offset += length


class VirtualCardDialog(QtWidgets.QDialog):
    """Finestra di supporto per l'emulazione software."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Emulazione Smart Card")
        self.setModal(True)

        logger.info("Emulazione software avviata con ATR %s", ATR_FALLBACK)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)

        info_label = QtWidgets.QLabel(
            "L'emulazione è attiva con impostazioni predefinite. "
            "I dettagli tecnici sono disponibili nel file logs.txt."
        )
        info_label.setWordWrap(True)

        ok_button = QtWidgets.QPushButton("Chiudi")
        ok_button.setMinimumHeight(40)
        ok_button.clicked.connect(self.accept)

        layout.addStretch(1)
        layout.addWidget(info_label, alignment=QtCore.Qt.AlignCenter)
        layout.addStretch(1)
        layout.addWidget(ok_button, alignment=QtCore.Qt.AlignCenter)

    def generate_response(self, apdu: Sequence[int]) -> str:
        """Mantiene la logica di risposta per eventuali estensioni future."""

        if len(apdu) < 4:
            return "APDU troppo corta\n"
        cla, ins, p1, p2 = apdu[:4]
        if cla == 0x00 and ins == 0xA4:
            return "Selezione file riuscita (SW=9000)\n"
        if cla == 0x00 and ins == 0xB0:
            length = apdu[4] if len(apdu) > 4 else 0
            data = [((p1 << 8) + p2 + i) & 0xFF for i in range(length)]
            return f"Dati emulati: {toHexString(data)} (SW=9000)\n"
        return "Comando non riconosciuto (SW=6D00)\n"


class SmartCardWindow(QtWidgets.QMainWindow):
    """Finestra principale minimale con tre azioni."""

    def __init__(self) -> None:
        super().__init__()
        self.backend = SmartCardBackend()

        self.setWindowTitle("Gestione Smart Card")
        self.setMinimumSize(500, 400)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(24)

        button_layout = QtWidgets.QVBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setAlignment(QtCore.Qt.AlignHCenter)

        self.read_button = self._create_action_button("Leggi Card")
        self.clone_button = self._create_action_button("Clona Card")
        self.emulate_button = self._create_action_button("Emula Card")

        button_layout.addWidget(self.read_button, alignment=QtCore.Qt.AlignCenter)
        button_layout.addWidget(self.clone_button, alignment=QtCore.Qt.AlignCenter)
        button_layout.addWidget(self.emulate_button, alignment=QtCore.Qt.AlignCenter)

        self.message_box = QtWidgets.QTextEdit()
        self.message_box.setReadOnly(True)
        self.message_box.setMinimumHeight(120)
        self.message_box.setAlignment(QtCore.Qt.AlignCenter)
        self.message_box.setStyleSheet("font-size: 16px;")

        main_layout.addStretch(1)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.message_box)
        main_layout.addStretch(1)

        self.read_button.clicked.connect(self.handle_read)
        self.clone_button.clicked.connect(self.handle_clone)
        self.emulate_button.clicked.connect(self.handle_emulate)

    def _create_action_button(self, text: str) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(text)
        button.setMinimumSize(260, 70)
        button.setStyleSheet("font-size: 18px;")
        return button

    def handle_read(self) -> None:
        logger.info("Richiesta operazione di lettura")
        reader_name = self._first_reader()
        if not reader_name:
            self._show_error("Errore: nessun lettore trovato")
            return
        try:
            atr = self.backend.connect(reader_name)
            if atr is None:
                logger.info("ATR non disponibile, proseguo con la lettura")
            self.backend.read_card_dump()
            self._show_success("Operazione completata con successo")
        except NoCardException:
            logger.exception("Lettura fallita: nessuna card presente")
            self._show_error("Errore: nessuna card trovata")
        except Exception:
            logger.exception("Errore generico durante la lettura")
            self._show_warning("Operazione fallita, riprovare")
        finally:
            self.backend.disconnect()

    def handle_clone(self) -> None:
        logger.info("Richiesta operazione di clonazione")
        reader_name = self._first_reader()
        if not reader_name:
            self._show_error("Errore: nessun lettore trovato")
            return
        try:
            QtWidgets.QMessageBox.information(
                self,
                "Clona Card",
                "Inserisci la card da copiare e premi OK per continuare.",
            )
            self.backend.connect(reader_name)
            dump = self.backend.read_card_dump()
            self.backend.disconnect()
            QtWidgets.QMessageBox.information(
                self,
                "Clona Card",
                "Inserisci la card vuota e premi OK per completare la clonazione.",
            )
            self.backend.connect(reader_name)
            self.backend.write_card_dump(dump)
            self._show_success("Operazione completata con successo")
        except NoCardException:
            logger.exception("Clonazione fallita: nessuna card presente")
            self._show_error("Errore: nessuna card trovata")
        except Exception:
            logger.exception("Errore durante la clonazione")
            self._show_warning("Operazione fallita, riprovare")
        finally:
            self.backend.disconnect()

    def handle_emulate(self) -> None:
        logger.info("Richiesta operazione di emulazione")
        dialog = VirtualCardDialog(self)
        dialog.exec_()
        self._show_success("Operazione completata con successo")

    def _first_reader(self) -> Optional[str]:
        readers_list = self.backend.available_readers()
        if not readers_list:
            return None
        return readers_list[0]

    def _show_success(self, message: str) -> None:
        self._update_message(f"✅ {message}")

    def _show_error(self, message: str) -> None:
        self._update_message(f"❌ {message}")

    def _show_warning(self, message: str) -> None:
        self._update_message(f"⚠️ {message}")

    def _update_message(self, message: str) -> None:
        self.message_box.setPlainText(message)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = SmartCardWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
