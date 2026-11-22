# FreeToken su ChatGPT

> I GPT personalizzati verranno ritirati l'11 dicembre 2026 e sostituiti dai **plugin**, che funzionano sia in ChatGPT sia in Codex. FreeToken è già un plugin.

## Il modo più veloce: sempre acceso (30 secondi)
1. ChatGPT → **Impostazioni → Personalizzazione → Istruzioni personalizzate**.
2. Incolla tutto il testo di [`INCOLLA-QUESTO.txt`](../INCOLLA-QUESTO.txt) nel campo su come vuoi che ChatGPT risponda (sta sotto i 1.500 caratteri).
3. Salva.

Da ora il semaforo è attivo in ogni chat, senza richiamarlo. Hai già `nota` e `quanto`.

## La versione completa: il plugin FreeToken
Il plugin aggiunge la skill che interviene da sola e tutte le parole magiche (`comprimi`, `dieta`, `pagella`, `preventivo`, `calcolatore`, `regole`).

**Se usi l'app desktop di ChatGPT o Codex:**
1. Nel Terminale: `codex plugin marketplace add Giandoms/FreeToken`
2. Poi: `codex plugin add freetoken@freetoken`
3. Apri l'app desktop di ChatGPT: FreeToken compare tra i plugin. Aprilo, premi **+** e inizia una chat nuova.

**Se lavori in un'azienda con ChatGPT Business o Enterprise:** l'amministratore può importare il marketplace da GitHub (`Giandoms/FreeToken`) e renderlo disponibile a tutti, senza Terminale.

## Come interviene da solo
ChatGPT tiene sempre a portata di mano il nome e la descrizione di FreeToken. Quando riconosce un segnale (chat lunga, testo enorme incollato, cambio di argomento, correzione di un suo errore) apre la skill da sola e aggiunge l'avviso in fondo alla risposta. Decide il modello, quindi succede quasi sempre ma non è garantito: per questo conviene tenere acceso anche il blocco nelle istruzioni personalizzate.

## Le parole magiche
| Scrivi | Ottieni |
|---|---|
| `nota` | il Passaggio: 10 righe da incollare in una chat nuova, anche su un'altra IA |
| `quanto` | il colore del semaforo e se conviene ripartire |
| `comprimi` | il tuo testo più corto senza perdere niente |
| `dieta` | le tue istruzioni personalizzate dimagrite |
| `pagella` | un voto a come usi l'IA e le 3 cose da cambiare |
| `preventivo` | prima di un lavoro grande: come dividerlo |
| `calcolatore` | il calcolatore gratuito |

## Da sapere
ChatGPT non mostra il contatore vero dei consumi nemmeno a se stesso: le cifre degli avvisi sono stime. Da dicembre, su Plus, Pro e Business, il saldo vero lo trovi in **Impostazioni → Utilizzo**.
