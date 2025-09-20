"""Barcode Manager GUI application.

Consente di creare, salvare, importare e decodificare barcode partendo da un
set di dati anagrafici (ID prodotto, lotto, scadenza, note). Supporta Code128,
QR e PDF417 attraverso le librerie python-barcode, qrcode e pdf417gen.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Dict, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

try:  # pragma: no cover - librerie opzionali in fase di runtime
    import barcode
    from barcode.writer import ImageWriter
    import pdf417gen
    import qrcode
    from PIL import Image
    from pyzbar.pyzbar import decode as decode_barcode
except ImportError as exc:  # pragma: no cover
    missing = str(exc).split("(")[0].strip()
    raise SystemExit(
        f"Dipendenza mancante ({missing}). Assicurati di aver installato le librerie richieste."
    ) from exc


@dataclass
class ProductData:
    """Rappresenta le informazioni memorizzate nel barcode."""

    product_id: str
    lot_number: str
    expiration_date: str
    notes: str

    def to_payload(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_payload(cls, payload: str) -> "ProductData":
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            parts = [segment.split(":", 1) for segment in payload.split(";") if ":" in segment]
            data = {key.strip(): value.strip() for key, value in parts}
        return cls(
            product_id=data.get("product_id") or data.get("ID", ""),
            lot_number=data.get("lot_number") or data.get("LOT", ""),
            expiration_date=data.get("expiration_date") or data.get("EXP", ""),
            notes=data.get("notes") or data.get("NOTE", ""),
        )


class BarcodeWindow(QtWidgets.QMainWindow):
    """Interfaccia grafica per la gestione dei barcode."""

    def __init__(self) -> None:
        super().__init__()
        self.generated_image: Optional[Image.Image] = None

        self.setWindowTitle("Barcode Manager")
        self.resize(800, 600)

        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QVBoxLayout(central_widget)

        form_layout = QtWidgets.QFormLayout()
        self.product_id_edit = QtWidgets.QLineEdit()
        self.lot_edit = QtWidgets.QLineEdit()
        self.expiration_edit = QtWidgets.QLineEdit()
        self.notes_edit = QtWidgets.QLineEdit()

        form_layout.addRow("ID prodotto", self.product_id_edit)
        form_layout.addRow("Lotto", self.lot_edit)
        form_layout.addRow("Scadenza", self.expiration_edit)
        form_layout.addRow("Note", self.notes_edit)

        main_layout.addLayout(form_layout)

        # Barcode options
        options_layout = QtWidgets.QHBoxLayout()
        self.barcode_type_combo = QtWidgets.QComboBox()
        self.barcode_type_combo.addItems(["Code128", "QR", "PDF417"])
        options_layout.addWidget(QtWidgets.QLabel("Formato:"))
        options_layout.addWidget(self.barcode_type_combo)
        options_layout.addStretch(1)

        self.generate_button = QtWidgets.QPushButton("Genera barcode")
        self.save_button = QtWidgets.QPushButton("Salva immagine")
        self.import_button = QtWidgets.QPushButton("Importa barcode")

        options_layout.addWidget(self.generate_button)
        options_layout.addWidget(self.save_button)
        options_layout.addWidget(self.import_button)

        main_layout.addLayout(options_layout)

        # Preview area
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFrameShape(QtWidgets.QFrame.Shape.Box)
        self.preview_label.setMinimumSize(400, 250)
        main_layout.addWidget(self.preview_label, 1)

        # Status bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

        # Signals
        self.generate_button.clicked.connect(self.handle_generate)
        self.save_button.clicked.connect(self.handle_save)
        self.import_button.clicked.connect(self.handle_import)

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------
    def collect_data(self) -> ProductData:
        return ProductData(
            product_id=self.product_id_edit.text().strip(),
            lot_number=self.lot_edit.text().strip(),
            expiration_date=self.expiration_edit.text().strip(),
            notes=self.notes_edit.text().strip(),
        )

    def apply_data(self, data: ProductData) -> None:
        self.product_id_edit.setText(data.product_id)
        self.lot_edit.setText(data.lot_number)
        self.expiration_edit.setText(data.expiration_date)
        self.notes_edit.setText(data.notes)

    # ------------------------------------------------------------------
    # Barcode generation
    # ------------------------------------------------------------------
    def handle_generate(self) -> None:
        data = self.collect_data()
        if not data.product_id:
            QtWidgets.QMessageBox.warning(self, "Dati mancanti", "Inserisci almeno l'ID prodotto.")
            return
        try:
            payload = data.to_payload()
            image = self.create_barcode_image(payload)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Errore generazione", str(exc))
            return
        self.generated_image = image
        pixmap = self.pil_to_pixmap(image)
        self.preview_label.setPixmap(pixmap.scaled(
            self.preview_label.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        ))
        self.show_status("Barcode generato con successo", 3000)

    def create_barcode_image(self, payload: str) -> Image.Image:
        barcode_type = self.barcode_type_combo.currentText()
        if barcode_type == "Code128":
            code = barcode.get("code128", payload, writer=ImageWriter())
            buffer = BytesIO()
            code.write(buffer, options={"module_height": 15.0, "text_distance": 1.0})
            buffer.seek(0)
            return Image.open(buffer).convert("RGB")
        if barcode_type == "QR":
            qr = qrcode.QRCode(version=None, box_size=10, border=2)
            qr.add_data(payload)
            qr.make(fit=True)
            return qr.make_image(fill_color="black", back_color="white").convert("RGB")
        if barcode_type == "PDF417":
            codes = pdf417gen.encode(payload, columns=6, security_level=2)
            img = pdf417gen.render_image(codes, scale=2)
            return img.convert("RGB")
        raise ValueError(f"Formato barcode non supportato: {barcode_type}")

    # ------------------------------------------------------------------
    # File handling
    # ------------------------------------------------------------------
    def handle_save(self) -> None:
        if not self.generated_image:
            QtWidgets.QMessageBox.information(self, "Nessun barcode", "Genera un barcode prima di salvarlo.")
            return
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Salva barcode", "barcode.png", "Immagini PNG (*.png)"
        )
        if not filename:
            return
        try:
            self.generated_image.save(filename, format="PNG")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Errore salvataggio", str(exc))
            return
        self.show_status(f"Barcode salvato in {filename}", 3000)

    def handle_import(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Importa barcode", "", "Immagini (*.png *.jpg *.jpeg *.bmp)"
        )
        if not filename:
            return
        try:
            image = Image.open(filename)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Errore apertura", str(exc))
            return

        decoded = decode_barcode(image)
        if not decoded:
            QtWidgets.QMessageBox.warning(self, "Decodifica fallita", "Nessun barcode riconosciuto.")
            return
        payload = decoded[0].data.decode("utf-8")
        data = ProductData.from_payload(payload)
        self.apply_data(data)
        self.generated_image = image.convert("RGB")
        pixmap = self.pil_to_pixmap(self.generated_image)
        self.preview_label.setPixmap(pixmap.scaled(
            self.preview_label.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        ))
        self.show_status("Barcode importato e decodificato", 3000)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def pil_to_pixmap(self, image: Image.Image) -> QtGui.QPixmap:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        qt_image = QtGui.QImage()
        qt_image.loadFromData(buffer.getvalue())
        return QtGui.QPixmap.fromImage(qt_image)

    def show_status(self, message: str, timeout: int = 0) -> None:
        self.statusBar().showMessage(message, timeout)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = BarcodeWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
