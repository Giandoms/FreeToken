# FreeToken su Codex

## Il plugin (consigliato)
```bash
codex plugin marketplace add Giandoms/FreeToken
codex plugin add freetoken@freetoken
```
Riavvia Codex. La skill FreeToken è disponibile e Codex la apre da solo quando la sessione si allunga, quando incolli output enormi o quando chiedi di riscrivere file interi. Puoi anche richiamarla con `$freetoken`. I comandi `nota`, `riparti` e `asciutto` diventano skill.

## In più: le regole sempre presenti
Copia il contenuto di [`AGENTS.md`](AGENTS.md) in fondo al file `~/.codex/AGENTS.md`, che Codex legge a ogni sessione:
```bash
mkdir -p ~/.codex && curl -s https://raw.githubusercontent.com/Giandoms/FreeToken/main/codex/AGENTS.md >> ~/.codex/AGENTS.md
```

## I tre comandi di Codex che FreeToken ti suggerirà
| Comando | A cosa serve |
|---|---|
| `/status` | vedi quanto hai consumato e quanto spazio resta |
| `/compact` | riassume la sessione per liberare spazio, quando il lavoro continua |
| `/new` | chat nuova nello stesso progetto, quando cambi lavoro |

## Da sapere
Codex non vede il proprio contatore mentre risponde: il semaforo si basa su quanto è lunga la sessione, e le cifre sono stime. I numeri veri li trovi con `/status`.
