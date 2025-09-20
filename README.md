# Strumenti Hydra FUS C6000

Repository contenente i due tool desktop richiesti per la gestione delle
smartcard e dei barcode del sistema Hydra FUS C6000. Ogni applicazione è
contenuta in una cartella dedicata con il proprio codice, i requisiti e gli
script per la creazione dell'eseguibile standalone.

## Struttura

```
strumenti_hydra_fus_c6000/
├── smartcard_manager/
│   ├── smartcard_gui.py
│   ├── requirements.txt
│   ├── setup.py
│   └── README.md
├── barcode_manager/
│   ├── barcode_gui.py
│   ├── requirements.txt
│   ├── setup.py
│   └── README.md
└── README.md
```

## Workflow consigliato

1. Entrare nella cartella dell'applicazione (`smartcard_manager/` oppure
   `barcode_manager/`).
2. Installare le dipendenze Python indicate nel rispettivo `requirements.txt`.
3. Avviare lo script principale con `python <nome>_gui.py` per avviare la GUI.
4. Facoltativo: creare l'eseguibile con `python setup.py build` oppure usando
   direttamente il comando PyInstaller mostrato nei README specifici.

## Distribuzione

Per creare i pacchetti `.zip` finali, dopo aver generato gli eseguibili con
PyInstaller, raccogliere i file presenti nella cartella `dist/` insieme ad
un eventuale file `README` e comprimere ciascuna applicazione separatamente.

## Supporto

- **SmartCard Manager:** PyQt5 + pyscard con emulatore software incluso.
- **Barcode Manager:** PyQt5 + python-barcode + qrcode + pdf417gen + Pillow +
  pyzbar per lettura da immagini.

Entrambe le applicazioni sono compatibili con PyInstaller (`--onefile --windowed`).
