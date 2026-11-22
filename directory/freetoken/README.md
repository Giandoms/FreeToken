# FreeToken

FreeToken ti avvisa quando la chat con l'IA consuma troppo e ti dice cosa fare. Funziona in italiano su Claude (chat, app, Cowork), Claude Code, ChatGPT e Codex.

## Cosa fa
- **Si attiva da sola.** Quando la conversazione diventa lunga, cambia argomento, contiene testi enormi incollati, richieste di rifare tutto per una piccola modifica o correzioni di errori, aggiunge in fondo alla risposta un avviso a semaforo in tre righe: cosa succede, perché ti costa, cosa fare. Se va tutto bene, non dice niente.
- **Al rosso scrive il Passaggio**: dieci righe con obiettivo, decisioni, materiali e prossimo passo, da incollare in una chat nuova per ripartire leggeri, anche su un'altra IA.
- **Parole da scrivere quando servono:** `nota`, `quanto`, `comprimi`, `dieta`, `pagella`, `preventivo`, `calcolatore`, `regole`.
- **Comandi in Cowork e Claude Code:** `/nota`, `/riparti`, `/asciutto`.

## Installazione
- **Claude (web, app, Cowork):** Personalizza → Plugin → Aggiungi → Aggiungi marketplace → Aggiungi da un repository → `Giandoms/FreeToken`.
- **Claude Code:** `/plugin install freetoken --marketplace Giandoms/FreeToken`
- **Codex e ChatGPT desktop:** `codex plugin marketplace add Giandoms/FreeToken` e poi `codex plugin add freetoken@freetoken`.

## Cosa contiene (trasparenza)
Questa versione contiene solo testo: la skill FreeToken, i comandi `/nota`, `/riparti` e `/asciutto`, il link al calcolatore online e le immagini. Non esegue codice, non fa chiamate di rete e non salva niente sul tuo computer.

La versione completa per Claude Code, con il pilota automatico che legge i consumi veri e ferma gli sprechi prima che partano, si installa dal progetto GitHub: https://github.com/Giandoms/FreeToken

## Privacy
FreeToken non raccoglie, non conserva e non trasmette dati personali. Questa versione non salva niente. Informativa completa: https://giandoms.github.io/FreeToken/privacy.html

## Limiti
In chat l'IA non vede il contatore reale dei consumi: le cifre degli avvisi sono stime. La skill la attiva il modello quando riconosce i segnali, quindi succede quasi sempre ma non sempre.

## Autore e supporto
Giando Santamaria, il Facilitatore IA delle PMI · https://www.giandosantamaria.it
Segnalazioni e domande: https://github.com/Giandoms/FreeToken/issues
Licenza MIT.
