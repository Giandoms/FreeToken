# FreeToken su Codex

Codex legge da solo le istruzioni scritte in un file chiamato `AGENTS.md`.

## Per tutti i tuoi progetti (consigliato)
Copia il contenuto di `AGENTS.md` (in questa cartella) in fondo al file `~/.codex/AGENTS.md` sul tuo computer. Se il file non esiste, crealo.

Dal Terminale, dalla cartella di FreeToken:
```bash
mkdir -p ~/.codex && cat codex/AGENTS.md >> ~/.codex/AGENTS.md
```

## Solo per un progetto
Copia il contenuto in fondo al file `AGENTS.md` nella cartella principale del progetto.

## I tre comandi di Codex che FreeToken ti suggerirà
| Comando | A cosa serve |
|---|---|
| `/status` | vedi quanto hai consumato e quanto spazio resta |
| `/compact` | riassume la sessione per liberare spazio, quando il lavoro continua |
| `/new` | chat nuova nello stesso progetto, quando cambi lavoro |

Con FreeToken in più hai `nota` (salva il Passaggio in `NOTA-SESSIONE.md`) e `quanto` (il semaforo della sessione).

## Da sapere
Codex non vede il proprio contatore mentre risponde: il semaforo si basa su quanto è lunga la sessione, e le cifre sono stime. I numeri veri li trovi con `/status`.
