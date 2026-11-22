# FreeToken su Claude (chat, app e Cowork)

## Il modo più veloce: sempre acceso (1 minuto)
1. Apri Claude, clicca le tue iniziali in basso a sinistra, poi **Impostazioni → La tua Claude (Your Claude) → Istruzioni**.
2. Incolla tutto il testo di `INCOLLA-QUESTO.txt` (nella cartella principale).
3. Salva. Vale per tutte le chat, anche quelle in Cowork.

Puoi anche incollarlo solo nelle istruzioni di un Progetto, se vuoi FreeToken solo lì.

## La versione completa: la skill FreeToken
La skill aggiunge tutte le parole magiche (`nota`, `quanto`, `comprimi`, `dieta`, `pagella`, `preventivo`, `regole`).

1. Scarica la skill già pronta: **[freetoken-skill.zip](https://github.com/Giandoms/FreeToken/raw/main/scarica/freetoken-skill.zip)**. Dentro c'è anche il calcolatore.
2. In Claude: **Personalizza (Customize) → Skill**, poi il pulsante **+**, **Crea skill** e **Carica una skill**. Scegli lo zip.
   Serve che sia attiva l'esecuzione del codice (Impostazioni → Funzionalità).
3. Attivala. Funziona nelle chat, nei Progetti e in Cowork.

Consiglio: tieni il blocco sempre acceso **e** la skill. Il blocco avvisa sempre, la skill entra in gioco quando serve fare di più.

## In Cowork, il risparmio più grande
In Cowork il consumo più alto spesso non è nelle chat ma nelle **attività programmate** che girano da sole. Un'attività che ogni ora controlla la posta e trova zero novità consuma ogni volta come se avesse lavorato.

FreeToken te lo segnala quando ne crei una. La regola è semplice: ogni attività programmata deve iniziare con

> Prima controlla se c'è qualcosa di nuovo. Se non c'è niente, fermati qui e scrivi solo «niente di nuovo».

E chiediti se deve girare davvero ogni ora: due volte al giorno spesso bastano.

## Da sapere
In chat Claude non vede il contatore vero dei consumi: le cifre degli avvisi sono stime. Se usi Claude Code, la cartella `claude-code` fa tutto da sola, con i numeri veri.
