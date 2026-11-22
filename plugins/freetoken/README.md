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

## Cosa esegue e cosa tocca (trasparenza)
In Claude Code e Cowork il plugin contiene controlli automatici (hook) scritti in Python, solo libreria standard, con il codice leggibile nella cartella `scripts/`. Ecco tutto quello che fanno:
- **leggono** il testo del messaggio che stai per inviare e la risposta degli strumenti, per stimarne la dimensione;
- **leggono** il file della conversazione che Claude Code tiene sul tuo computer, solo per sapere quanto è grande la sessione e quando è arrivata l'ultima risposta;
- **leggono** la dimensione dei file che Claude sta per aprire, per evitare letture intere di file enormi;
- **leggono** i nomi dei connettori configurati (`~/.claude.json`, `.mcp.json`) e la lunghezza di `CLAUDE.md`, solo per contarli nel check-up giornaliero;
- **scrivono** un registro dei risparmi e lo stato delle sessioni nella cartella `~/.freetoken/` del tuo computer. Il registro contiene numeri e nomi di file, mai il testo dei tuoi messaggi;
- **possono fermare** una volta un'azione sprecona (un incolla enorme, la lettura intera di un file gigante, un messaggio dopo una pausa lunga con la chat piena). Se ripeti l'azione, passa.

**Niente esce dal tuo computer.** I controlli non fanno chiamate di rete, non inviano dati a nessun server e non modificano le impostazioni di Claude.

Nelle chat sul web e nelle app, e in ChatGPT e Codex, FreeToken è solo una skill: istruzioni in testo, senza codice eseguito.

## Privacy
FreeToken non raccoglie, non conserva e non trasmette dati personali. Tutto quello che salva resta sul tuo computer, in `~/.freetoken/`, e puoi cancellarlo quando vuoi. Informativa completa: https://giandoms.github.io/FreeToken/privacy.html

## Limiti
In chat l'IA non vede il contatore reale dei consumi: le cifre degli avvisi sono stime. La skill la attiva il modello quando riconosce i segnali, quindi succede quasi sempre ma non sempre.

## Autore e supporto
Giando Santamaria, il Facilitatore IA delle PMI · https://www.giandosantamaria.it
Segnalazioni e domande: https://github.com/Giandoms/FreeToken/issues
Licenza MIT.
