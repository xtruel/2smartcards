# Barcode Manager

Barcode Manager è una GUI PyQt5 per creare, salvare, importare e decodificare
codici a barre utilizzati nel processo produttivo Hydra FUS C6000.

## Funzionalità

- Inserimento e gestione dei dati di prodotto (ID, lotto, scadenza, note).
- Generazione di barcode nei formati Code128, QR e PDF417.
- Anteprima dell'immagine generata con possibilità di salvataggio in PNG.
- Importazione di barcode da immagine (scanner o file) e decodifica automatica
  con compilazione dei campi del form.

## Requisiti

Installare le librerie richieste con:

```bash
pip install -r requirements.txt
```

Per utilizzare la decodifica è necessario che il sistema disponga delle
librerie native richieste da `pyzbar`/`zbar`.

## Avvio dell'applicazione

```bash
python barcode_gui.py
```

## Creazione dell'eseguibile

Lo script `setup.py` permette di costruire un eseguibile standalone con
PyInstaller:

```bash
python setup.py build
```

Oppure eseguire direttamente:

```bash
pyinstaller --onefile --windowed barcode_gui.py
```

L'eseguibile verrà salvato in `dist/`.

## Suggerimenti

- Personalizza il payload JSON editando la classe `ProductData` per aggiungere
  campi specifici del tuo processo.
- Se preferisci un formato testuale personalizzato, modifica i metodi
  `to_payload()` e `from_payload()`.
