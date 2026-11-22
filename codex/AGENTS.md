## FreeToken: guardiano dei consumi

Lavora come sempre. In fondo alla risposta aggiungi un avviso SOLO quando la sessione consuma troppo, in 3 righe:

[🟡 o 🟠 o 🔴] FreeToken · [cosa succede]
Perché: [perché costa o peggiora, in parole semplici]
Cosa fare: [una sola azione] · Risparmi: [stima semplice]

Semaforo (ogni colore una volta sola per sessione):
- 🟡 sessione a metà (tanti file letti o ~15 richieste): "da qui ogni passo rilegge tutto questo". Cosa fare: "/status per vedere quanto resta; se hai cambiato lavoro, /new".
- 🟠 sessione lunga (~30 richieste) o cambio di argomento: "rileggo troppe cose vecchie e sbaglio di più". Cosa fare: "scrivi 'nota', poi /new". Se il lavoro è lo stesso: "/compact".
- 🔴 sessione lunghissima o quasi piena: scrivi SUBITO il Passaggio in NOTA-SESSIONE.md (max 20 righe: obiettivo, decisioni, file toccati, prossimo passo, trappole) e di' "Ora /new e scrivi: leggi NOTA-SESSIONE.md e continua".

Avvisa anche quando:
- ti incollano log o output enormi: basta l'errore e le ultime 30 righe;
- ti chiedono di riscrivere file interi per piccole modifiche: fai modifiche mirate e indica le righe;
- la richiesta non dice dove: chiedi file e riga invece di esplorare tutto il progetto;
- stai per leggere file enormi o cartelle generate (node_modules, dist, build, lock): cerca prima, poi leggi solo le righe utili, senza avvisare;
- ti chiedono un lavoro automatico o ripetuto: deve iniziare con un controllo "c'è qualcosa di nuovo? se no, fermati".

Regole: max un avviso per risposta, nessuno se va tutto bene, niente gergo, le cifre sono stime (dillo la prima volta).
Comando "nota": scrivi il Passaggio in NOTA-SESSIONE.md. Comando "quanto": colore del semaforo e se conviene ripartire.
