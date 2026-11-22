# FreeToken su Claude (web, app e Cowork)

## 1. Installa il plugin (2 minuti, una volta sola)
1. Apri Claude e clicca **Personalizza** nella barra a sinistra.
2. Apri la scheda **Plugin**.
3. Premi **+** e scegli **Aggiungi marketplace da GitHub**.
4. Scrivi `Giandoms/FreeToken` e conferma.
5. Nell'elenco compare **FreeToken**: premi **Aggiungi**.

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
