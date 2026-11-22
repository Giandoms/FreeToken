# 23 strategie per spendere meno token (molte vanno contro il buon senso)

Prima una cosa sola da capire, poi le strategie diventano ovvie.

**Ogni volta che scrivi un messaggio, l'IA rilegge tutta la chat.** Proprio tutta: le tue istruzioni, i documenti caricati, i log incollati, le sue risposte di prima, le descrizioni dei connettori accesi. Non rilegge solo l'ultima riga: rilegge tutto, a ogni messaggio. Più la chat è pesante, più paghi ogni singola risposta, e più le risposte peggiorano.

C'è uno sconto: la **cache**, una memoria rapida che fa pagare circa un decimo la parte già letta. Ma dura poco (di solito 5 minuti, in alcuni casi un'ora) e si rompe se cambi qualcosa all'inizio della chat. Quando scade, il messaggio successivo rilegge tutto a prezzo pieno, anzi un po' di più.

Su ChatGPT in abbonamento non vedi i token in fattura, ma li paghi lo stesso: in limiti raggiunti prima, risposte più lente e una chat che "dimentica" e sbaglia.

Legenda: **[CC]** Claude Code · **[C]** Claude.ai · **[G]** ChatGPT · 🪙 = FreeToken ti avvisa da solo.

---

## Parte 1. La conversazione

### 1. Butta via la chat, non tenerla [CC] [C] [G] 🪙
Viene naturale pensare «tengo la chat così si ricorda tutto». È il modo più caro.
- **Prima:** una chat da 150 messaggi (~100.000 token) che si trascina tre lavori diversi. Ogni domanda nuova rilegge tutto.
- **Dopo:** una chat per lavoro. Quando cambi argomento, chiudi. Le cose da ricordare in una nota di 20 righe (~400 token) che riparte con te.
- **Quanto:** da ~100.000 a ~400 token rimandati a ogni messaggio.
- **Dipende:** vale quando cambi lavoro. Se stai ancora sullo stesso file e la chat è sotto metà, tenerla conviene: la cache è calda e rifare il contesto costerebbe di più.
- **Come:** in Claude Code `/nota` poi `/clear` poi `/riparti`. In ChatGPT e Claude.ai scrivi «nota» e incolla la nota in una chat nuova.

### 2. La pausa caffè costa più del caffè [CC] [C] 🪙
Lasci una sessione grande per 6 minuti, torni e scrivi «continua». La cache è scaduta: quel «continua» rilegge 140.000 token a prezzo pieno.
- **Prima:** riprendi la sessione enorme dopo la pausa. ~175.000 token equivalenti per una parola.
- **Dopo:** prima di staccare fai `/nota`. Quando torni: `/clear` e `/riparti`. ~1.000 token.
- **Il controcorrente:** se stacchi, stacca davvero. O torni entro pochi minuti, o riparti da zero con la nota. La via di mezzo è la più cara di tutte.
- 🪙 La barra ti mostra il conto alla rovescia della cache (`⏳ cache 3:12`). Se scade con la chat piena, il messaggio viene fermato una volta e ti dice quanto costerebbe.

### 3. Il «grazie» da 15.000 token [CC] [C] [G] 🪙
Con una chat da 150.000 token, anche «ok perfetto» rimanda tutta la chat. Con la cache calda costa circa un decimo: 15.000 token per una cortesia.
- **Dopo:** il grazie mettilo nel messaggio del prossimo comando. «Perfetto. Ora fai lo stesso sul file prezzi.»
- **Dipende:** a chat leggera (sotto 20-30.000 token) è un'inezia. Diventa uno spreco solo a chat piena, ed è lì che ti avvisiamo.

### 4. Non correggere: torna indietro [CC] [C] [G]
L'IA sbaglia, tu scrivi «no, non così», lei si scusa e riprova. Ora nella chat ci sono la risposta sbagliata, la tua correzione e le scuse: le rileggi per tutta la sessione, e l'errore continua a influenzarla.
- **Dopo:** torna al messaggio prima dell'errore e riscrivilo meglio. In Claude Code `Esc Esc` o `/rewind`. In ChatGPT e Claude.ai modifica il tuo messaggio precedente (l'icona della matita).
- **Quanto:** due o tre giri tolti dalla chat, e una risposta migliore perché l'errore non c'è più.

### 5. Un messaggio lungo e preciso vale più di dieci corti [CC] [C] [G] 🪙
Ogni giro di domande e risposte rilegge tutto. Cinque giri per arrivare al punto sono cinque riletture.
- **Prima:** «c'è un problema col login» → «quale?» → «non entra» → «che errore?» → ...
- **Dopo:** «In `src/auth.py` riga 88 il login fallisce con errore 401 quando la password ha un accento. Correggi e lancia le prove.»
- **Regola:** indica sempre file e riga. Niente «guarda tu nel codice»: costringe l'IA a esplorare tutto il progetto e a riempire la chat.

### 6. Più contesto non è più intelligenza [CC] [C] [G] 🪙
Il buon senso dice: più informazioni le do, meglio risponde. Oltre una certa soglia è il contrario. In una conversazione lunghissima l'IA si perde i dettagli in mezzo, confonde versioni vecchie e nuove, ripete errori già corretti.
- **Dopo:** dai solo quello che serve al passo di adesso. Il resto in file che legge quando servono.
- 🪙 Ti avvisiamo al 50%, al 70% e all'85% della chat.

### 7. Compatta tu, a metà, con le istruzioni [CC] 🪙
L'auto-compattazione arriva quando la chat è pieno: riassume tutto in fretta, perde dettagli e costa una chiamata enorme.
- **Dopo:** verso metà chat, `/compact tieni solo decisioni, file aperti e prossimo passo`.
- **Dipende:** se hai cambiato argomento, non compattare: `/nota` e `/clear`. Compattare conviene solo quando il lavoro continua.

---

## Parte 2. Cosa entra nella chat

### 8. Non incollare log interi [CC] [C] [G] 🪙
Un log da 5.000 righe resta nella chat per tutta la sessione e lo paghi a ogni messaggio.
- **Dopo:** le ultime 30 righe, o solo l'errore.
- 🪙 Sopra ~6.000 token l'incolla viene fermato e ti diciamo quanto ti costerebbe tenerlo. Se ti serve davvero, rimandalo iniziando con `!!`.

### 9. Il documento si carica, non si incolla [C] [G]
Incollare un PDF di 40 pagine in chat lo mette tutto nella chat. Caricarlo come file di progetto (Progetti di Claude, Progetti o GPT di ChatGPT) spesso fa leggere solo i pezzi utili.
- **Dipende:** con documenti piccoli può finire tutto nel contesto comunque. Il guadagno vero è con documenti grandi e domande mirate: «cosa dice il contratto sul recesso?».

### 10. Spegni i connettori che non usi [CC] [C] [G] 🪙
Ogni connettore porta con sé la descrizione dei suoi strumenti, e quella descrizione entra nella chat. Un connettore pubblicitario può portarne centinaia.
- **Dopo:** accesi solo nelle attività che li usano davvero. Un progetto per le campagne con il connettore Ads, un progetto per la posta con Gmail.
- **Dipende:** le versioni recenti di alcuni strumenti caricano le descrizioni solo quando servono, e il peso si riduce. Ma ogni connettore acceso resta una tentazione per l'IA di usarlo, e un rischio.
- 🪙 La pagella conta i connettori attivi nel progetto. La barra ti dice se la cache si è rotta perché li hai cambiati.

### 11. Le istruzioni fisse sono una tassa fissa [CC] [C] [G] 🪙
CLAUDE.md, istruzioni del progetto, istruzioni personalizzate di ChatGPT, memoria salvata: si pagano a **ogni** messaggio di **ogni** chat.
- **Prima:** un CLAUDE.md da 400 righe con tutta la storia del progetto.
- **Dopo:** sotto le 60-120 righe, solo le regole che l'IA non può indovinare. Il manuale lungo spostalo in una skill: della skill paghi la descrizione, e il resto solo quando serve. Vedi `claude-code/esempi/CLAUDE.md.esempio`.
- **In ChatGPT:** apri la memoria salvata e cancella quello che non ti serve più. Ogni ricordo inutile viaggia in ogni chat.

### 12. Leggi a pezzi [CC] 🪙
- **Prima:** «leggi `app.js`» su un file da 3.000 righe.
- **Dopo:** cerca prima (Grep), poi leggi solo le righe utili.
- Blocca per sempre le cartelle che non vanno mai lette, in `.claude/settings.json`:
  ```json
  { "permissions": { "deny": ["Read(./node_modules/**)", "Read(./dist/**)"] } }
  ```
- 🪙 Le letture intere di file enormi vengono fermate una volta, e Claude cerca la parte giusta da solo.

### 13. Screenshot ritagliati [CC] [C] [G]
Uno screenshot a schermo intero pesa circa 1.500-1.800 token. Il ritaglio della sola finestra con l'errore, un quinto.
- **Dipende:** se serve vedere tutta l'interfaccia, mandala intera. Se serve leggere un messaggio d'errore, copia il testo: costa ancora meno.

### 14. Dì cosa hai cambiato tu [CC]
Hai modificato a mano un file? Se scrivi «ho sistemato io, ricontrolla», l'IA lo rilegge tutto.
- **Dopo:** «Ho cambiato le righe 40-60 di `prezzi.py`, controlla solo quelle.»

---

## Parte 3. Cosa esce

### 15. Chiedi le modifiche, non i file interi [CC] [C] [G] 🪙
Una risposta di 3.000 righe pesa due volte: nel conto (l'uscita costa di solito 5 volte l'ingresso) e nella chat dei messaggi dopo.
- **Prima:** «riscrivimi tutto il file con la correzione».
- **Dopo:** «applica la modifica e dimmi le righe toccate». In ChatGPT: «dammi solo il paragrafo cambiato».

### 16. Risposte asciutte [CC] [C] [G]
Riepiloghi, spiegazioni non richieste e codice ripetuto costano in uscita e restano nella chat.
- **Dopo:** in Claude Code `/asciutto`. Altrove: «rispondi con fatto / file toccati / cosa devo verificare».
- **Dipende:** quando stai imparando, la spiegazione è il valore. Asciutto vale per i lavori che sai già controllare.

### 17. Pensa di meno quando non serve [CC] [C] [G]
La modalità di ragionamento lungo produce migliaia di token di pensiero. Per rinominare variabili o formattare una tabella è uno spreco.
- **Dopo:** sforzo basso per i lavori meccanici (in Claude Code `/effort`), ragionamento lungo per le decisioni. In ChatGPT: la modalità veloce per eseguire, quella che ragiona per decidere.

---

## Parte 4. Quale modello e come organizzarsi

### 18. Il modello giusto per il lavoro [CC] [C] [G] 🪙
Il modello più economico che sbaglia e ti fa rifare tre volte costa più del grande.
- **Dopo:** il grande per il piano e le decisioni, il piccolo per eseguire lavori chiari e ripetitivi.
- **Il controcorrente:** non cambiare modello a metà sessione. La cache vale per un solo modello: cambiandolo, il messaggio dopo rilegge tutto a prezzo pieno. In Claude Code tieni il grande nella sessione e passa i lavori semplici a un subagent con `model: haiku` nel suo file.
- **Esempio in euro (listino API, novembre 2026, sessione da 25 richieste):** Opus circa 1,57 €, Sonnet circa 0,79 €, Haiku circa 4 centesimi. Riscrivere mail per una settimana con Opus invece che con Sonnet: circa 0,80 € buttati a sessione. Su ChatGPT, Astra contro Sol: circa 2,40 € a sessione.
- **Il contrario vale uguale:** una strategia o un codice su più file fatti con il modello leggero, rifatti tre volte, costano più token del modello potente usato una volta sola.
- 🪙 FreeToken guarda il lavoro che chiedi e il modello che usi, ti suggerisce quello adatto a inizio sessione con il risparmio in euro, e ti avvisa prima di un cambio a metà. Comando: `freetoken modello`.

### 19. Non toccare le istruzioni a metà lavoro [CC] 🪙
Cambiare CLAUDE.md, accendere un connettore o cambiare modello a metà sessione rompe la cache: tutto da rileggere.
- **Dopo:** sistemi l'ambiente all'inizio, poi lavori. Se devi cambiare, fallo subito dopo un `/clear`.
- 🪙 La barra ti dice perché la cache si è rotta: «connettori cambiati», «istruzioni cambiate», «pausa oltre 5 min».

### 20. Il subagent come stanza sporca [CC]
Una ricerca nel codice che legge 40 file riempie la chat di cose che non servono più. Fatta da un subagent, nella chat principale rientra solo la conclusione.
- **Dipende:** il subagent non è gratis, ha la sua chat separata. Conviene per esplorazioni grandi e sporche, non per una domanda da due file.

### 21. Pianifica prima di scrivere [CC] [C] [G]
Un piano sbagliato costa 2.000 token. Codice sbagliato costa 40.000, più quelli per toglierlo.
- **Dopo:** in Claude Code la modalità piano (`Shift+Tab`). Altrove: «prima dimmi il piano in 5 punti, non scrivere niente».

---

## Parte 5. Lavori automatici

### 22. Controlla i lavori automatici che girano a vuoto [CC] 🪙
È il risparmio più grande e il meno visto. Un agente che si sveglia ogni ora, legge tutto, trova zero novità e intanto ha bruciato migliaia di token. Esempio vero: un project manager automatico con 84 giri in 8 giorni, quasi tutti con zero risultati; un report post-call con 66 giri e zero call.
- **Dopo:** `python3 freetoken.py audit` trova i lavori ripetuti e quanti girano a vuoto.

### 23. La guardia a costo zero [CC]
Prima di svegliare l'IA, controlla con un comando che non costa niente se c'è lavoro: ci sono file nuovi? Email non lette? Call registrate?
- **Dopo:** `claude-code/esempi/guardia.sh` sveglia l'IA solo se c'è qualcosa, e le passa solo le novità, non tutto l'archivio.
- **Il controcorrente:** il lavoro automatico migliore è quello che, la maggior parte delle volte, non parte.

---

## Il riassunto da attaccare al monitor

1. Una chat per lavoro. Cambi argomento: nota e chat nuova.
2. Pausa lunga: nota prima, chat nuova dopo.
3. Mai log interi, mai file interi, mai «guarda tu».
4. L'errore si toglie tornando indietro, non correggendo.
5. Istruzioni fisse corte, connettori spenti, memoria pulita.
6. Il grande decide, il piccolo esegue. Mai cambiare a metà.
7. I lavori automatici partono solo se c'è lavoro.
