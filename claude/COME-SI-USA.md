# FreeToken su Claude (web, app e Cowork)

## 1. Installa il plugin (2 minuti, una volta sola)
1. Apri Claude e vai su **Personalizza → Plugin**.
2. Premi **Aggiungi** e scegli **Aggiungi marketplace**.
3. Scegli **Aggiungi da un repository**, scrivi `Giandoms/FreeToken` e premi **Sincronizza**. Lascia acceso *Sincronizza automaticamente*: così ricevi gli aggiornamenti da solo.
4. Compare **Freetoken**: premi **+**.
5. Claude ti avvisa che il plugin contiene componenti che eseguono codice: sono i controlli automatici di FreeToken, che lavorano solo sul tuo computer e il cui codice è pubblico in questa pagina. Premi **Continua**.

Il plugin vale per tutto il tuo account: chat sul web, app desktop, Cowork e anche Claude Code, se accedi con lo stesso account.

## 2. Cosa succede dopo
Non devi richiamarlo. Lavori come sempre e FreeToken interviene da solo:

- **in chat** (web e app): Claude conosce la skill FreeToken e la apre da sola quando la chat si allunga, quando incolli testi enormi, quando cambi argomento o correggi un suo errore. In fondo alla risposta trovi il semaforo: cosa succede, perché ti costa, cosa fare;
- **in Cowork**: oltre alla skill partono i controlli automatici, che mettono le regole FreeToken in ogni sessione e fermano gli sprechi più grossi. Hanno bisogno di Python nell'ambiente di Cowork: se non parte nessun avviso automatico, la skill continua comunque a funzionare.

## 3. Rendilo sempre acceso (consigliato, 30 secondi)
La skill la attiva Claude quando riconosce un segnale, quindi quasi sempre ma non sempre. Per avere l'avviso garantito in ogni chat:

1. Clicca le tue iniziali in basso a sinistra, poi **Impostazioni → La tua Claude → Istruzioni**.
2. Incolla il testo di [`INCOLLA-QUESTO.txt`](../INCOLLA-QUESTO.txt).

## Le parole magiche
`nota` · `quanto` · `comprimi` · `dieta` · `pagella` · `preventivo` · `calcolatore` · `regole`. Scrivile in chat quando ti servono. In Cowork e Claude Code hai anche `/nota`, `/riparti` e `/asciutto`.

## Non puoi usare i plugin?
Carica solo la skill: scarica [freetoken-skill.zip](https://github.com/Giandoms/FreeToken/raw/main/scarica/freetoken-skill.zip), poi **Personalizza → Skill → + → Crea skill → Carica una skill**. Serve l'esecuzione del codice attiva (Impostazioni → Funzionalità).

## Da sapere
In chat Claude non vede il contatore vero dei consumi: le cifre degli avvisi sono stime. Bastano per decidere cosa fare.
