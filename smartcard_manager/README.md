# SmartCard Manager

SmartCard Manager è una GUI PyQt5 progettata per interagire con lettori PC/SC
utilizzando la libreria [pyscard](https://pyscard.sourceforge.io/). L'app
permette di eseguire le operazioni più comuni con le smart card utilizzate
nei sistemi Hydra FUS C6000.

## Funzionalità principali

- Rilevamento dinamico dei lettori PC/SC collegati.
- Connessione a una card e visualizzazione dell'ATR.
- Console APDU integrata con log dei comandi inviati e delle risposte.
- Clonazione rapida: lettura dei primi 256 byte della card sorgente e scrittura
  su una card di destinazione compatibile.
- Emulatore software con ATR fisso per simulare rapidamente il flusso APDU.

> **Nota:** i comandi di lettura/scrittura sono generici (READ/WRITE BINARY) e
> potrebbero non funzionare su tutte le tipologie di card. Adattare gli APDU
> alle specifiche del supporto in uso.

## Requisiti

Installare le dipendenze Python con:

```bash
pip install -r requirements.txt
```

Su Windows è necessario installare i driver PC/SC per il lettore e assicurarsi
che PyQt5 sia compatibile con l'ambiente a 64 bit.

## Esecuzione

```bash
python smartcard_gui.py
```

## Creazione dell'eseguibile

Il progetto include uno script `setup.py` che richiama PyInstaller con le
opzioni consigliate. Dal terminale della cartella `smartcard_manager/` eseguire:

```bash
python setup.py build
```

In alternativa, è possibile lanciare direttamente PyInstaller:

```bash
pyinstaller --onefile --windowed smartcard_gui.py
```

L'eseguibile generato sarà disponibile nella directory `dist/`.

## Risoluzione dei problemi

- **Nessun lettore rilevato:** verificare che il servizio PC/SC del sistema sia
  attivo e che il lettore sia riconosciuto dal sistema operativo.
- **Errore di trasmissione APDU:** controllare che la card sia inserita
  correttamente e che supporti gli APDU utilizzati.
- **Dipendenza mancante:** l'interfaccia parte anche senza `pyscard`, ma le
  funzioni hardware richiedono l'installazione della libreria.
