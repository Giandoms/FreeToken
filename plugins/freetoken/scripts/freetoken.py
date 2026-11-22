#!/usr/bin/env python3
"""
FreeToken: il guardiano dei token per Claude Code.

Un solo script per tutto:
  python3 freetoken.py hook          <- lo chiama Claude Code (legge l'evento da stdin)
  python3 freetoken.py conto         <- quanto hai risparmiato e dove sprechi
  python3 freetoken.py audit         <- lavori automatici che girano a vuoto
  python3 freetoken.py pagella [dir] <- check-up del progetto (CLAUDE.md, connettori, cartelle pesanti)
  python3 freetoken.py misura FILE   <- quanto pesa un file nella chat
  python3 freetoken.py modello       <- quale modello conviene e quanti euro risparmi
  python3 freetoken.py calcolatore   <- apre il calcolatore nel browser

Solo libreria standard di Python 3.8+. Nessun dato esce dal tuo computer.
"""
import glob
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent
DATI = Path(os.environ.get("FREETOKEN_HOME", "~/.freetoken")).expanduser()

PREDEFINITI = {
    "caratteri_per_token": 3.6,          # stima prudente per testi in italiano
    "finestra_contesto": 200000,
    "prefisso_forza": "!!",              # inizia il messaggio con !! per saltare i controlli
    "incolla_blocco_token": 6000,        # sopra questa soglia un incolla viene fermato
    "lettura_blocco_token": 12000,       # file letti interi sopra questa soglia vengono fermati
    "lettura_righe_consigliate": 300,
    "uscita_pesante_token": 10000,
    "cache_fredda_soglia_token": 50000,
    "durata_sconto_secondi": 300,       # quanto resta valido lo sconto dopo l'ultima risposta
    "nota_token": 3000,                 # peso di una nota di ripartenza  # sotto questa soglia riscrivere la cache costa poco
    "grazie_soglia_token": 60000,
    "soglie_chat_percento": [50, 70, 85],
    "claude_md_righe_max": 120,
    "connettori_max": 5,
    "richieste_medie_dopo": 25,          # se non sappiamo quante richieste seguiranno
    "moltiplicatore_scrittura_cache": 1.25,
    "moltiplicatore_lettura_cache": 0.1,
    "moltiplicatore_output": 5.0,
    "prezzo_input_per_milione_usd": 4.0, # usato se il modello non si riconosce (Opus 5.5)
    "cambio_usd_eur": 0.90,             # 1 dollaro in euro (Banca d'Italia, novembre 2026)
    "consiglio_modello": True,          # suggerisce il modello adatto al lavoro
    "stima_richieste_sessione": 25,     # base dei risparmi in euro sul modello
    "stima_ingresso_per_richiesta": 10000,  # token equivalenti a prezzo pieno per richiesta
    "stima_uscita_per_richiesta": 1500,
    "cartelle_pesanti": ["node_modules", "dist", "build", ".next", "vendor", ".venv",
                          "__pycache__", "coverage", ".git/"],
    "file_pesanti": [r"\.lock$", r"package-lock\.json$", r"\.min\.(js|css)$", r"\.map$",
                     r"\.(csv|tsv|parquet|sqlite|db)$"],
    "statusline_precedente": "",
    "modalita": "rigida",               # "rigida" blocca, "morbida" avvisa soltanto
    "regole_sempre_attive": True,       # mette le regole FreeToken nel contesto a ogni avvio
}

REGOLE_SEMPRE_ATTIVE = (
    "FreeToken è attivo in questa sessione. Regole per l'assistente: rispondi sempre prima alla richiesta. "
    "Se la sessione consuma troppo, aggiungi in fondo un avviso in tre righe: "
    "'[🟡/🟠/🔴] FreeToken · cosa succede' / 'Perché: ...' / 'Cosa fare: ...'. "
    "🟡 sessione a metà; 🟠 sessione lunga o cambio di argomento; 🔴 quasi piena: proponi /nota, /clear e /riparti. "
    "Avvisa anche se l'utente incolla testi enormi, chiede di riscrivere file interi per piccole modifiche, "
    "chiede di cercare senza dire dove, o crea attività ripetute (devono partire controllando se c'è qualcosa di nuovo). "
    "Un avviso al massimo per risposta, nessuno se va tutto bene, linguaggio semplice. "
    "Per lavorare leggero: cerca prima di leggere file grandi, leggi solo le righe utili, fai modifiche mirate. "
    "Se il lavoro è semplice e il modello è potente, o il contrario, suggerisci all'inizio il modello adatto "
    "con il risparmio stimato in euro."
)

RISPARMI = {
    "incolla_bloccato": "Incolla enormi fermati",
    "lettura_bloccata": "File letti interi evitati",
    "cat_bloccato": "Output di cat evitati",
    "cache_fredda_evitata": "Ripartenze a cache fredda evitate",
}
SPRECHI = {
    "uscita_pesante": "Risultati pesanti entrati nella chat",
    "grazie_costoso": "Messaggi di cortesia a chat piena",
    "ripresa_fredda": "Sessioni riprese a cache scaduta",
    "compattazione_auto": "Auto-compattazioni al limite",
    "cambio_modello": "Cambi di modello a metà sessione",
}
PERSISTENTI = {"incolla_bloccato", "lettura_bloccata", "cat_bloccato", "uscita_pesante"}


# ---------------------------------------------------------------- utilità

def config():
    cfg = dict(PREDEFINITI)
    for f in (QUI.parent / "config.json", DATI / "config.json"):
        try:
            cfg.update(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return cfg


CFG = config()


def tok(testo_o_caratteri):
    n = testo_o_caratteri if isinstance(testo_o_caratteri, int) else len(testo_o_caratteri)
    return int(n / CFG["caratteri_per_token"])


def num(n):
    return f"{int(n):,}".replace(",", ".")


def k(n):
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M".replace(".", ",")
    if n >= 1000:
        return f"{round(n/1000)}k"
    return str(n)


# Listino API in dollari per milione di token (ingresso, uscita), novembre 2026.
LISTINO = {
    "opus": (4.0, 20.0, "Claude Opus"), "sonnet": (2.0, 10.0, "Claude Sonnet"),
    "haiku": (0.10, 0.50, "Claude Haiku"), "astra": (8.0, 40.0, "GPT Astra"),
    "sol": (2.0, 10.0, "GPT Sol"), "terra": (1.0, 5.0, "GPT Terra"), "luna": (0.10, 0.50, "GPT Luna"),
}
PIU_LEGGERO = {"opus": "sonnet", "astra": "sol"}
PIU_POTENTE = {"haiku": "sonnet", "sonnet": "opus", "luna": "sol", "terra": "sol", "sol": "astra"}
MODELLO = {"famiglia": None}   # il modello della sessione, quando lo conosciamo


def famiglia(modello):
    if isinstance(modello, dict):
        modello = modello.get("id") or modello.get("display_name") or ""
    m = str(modello or "").lower()
    for nome in LISTINO:
        if nome in m:
            return nome
    return None


def eur(equivalenti):
    """Euro dei token equivalenti (a prezzo d'ingresso) col modello della sessione."""
    prezzo = LISTINO[MODELLO["famiglia"]][0] if MODELLO["famiglia"] else CFG["prezzo_input_per_milione_usd"]
    return equivalenti / 1_000_000 * prezzo * CFG["cambio_usd_eur"]


def euro(valore):
    if valore < 0.01:
        return "meno di 1 centesimo"
    return f"{valore:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def risparmio(equivalenti):
    """La riga 'Risparmi' di ogni avviso: token e euro insieme."""
    return f"circa {k(equivalenti)} token, cioè circa {euro(eur(equivalenti))}"


def costo_sessione(fam, richieste=None):
    """Euro di una sessione tipica con quel modello (stima a listino API)."""
    pi, po, _ = LISTINO[fam]
    n = richieste or CFG["stima_richieste_sessione"]
    return n * (CFG["stima_ingresso_per_richiesta"] * pi + CFG["stima_uscita_per_richiesta"] * po) \
        / 1_000_000 * CFG["cambio_usd_eur"]


LAVORO_SEMPLICE = re.compile(
    r"\b(riscriv\w*|tradu\w*|riassum\w*|sintetizz\w*|riassunto|refus\w*|ortografi\w*|formatt\w*|"
    r"impagin\w*|e-?mail|mail|elenco puntato|titol\w*|rinomin\w*|accorcia\w*|semplifica\w*|"
    r"rendi\s+più\s+(chiaro|breve|formale)|messaggio|didascali\w*|sottotitol\w*)\b", re.I)
LAVORO_DIFFICILE = re.compile(
    r"(architettur\w*|strategi\w*|progett\w+ (il|la|un|una)|refactor\w*|rifattorizz\w*|migra\w*|"
    r"debug\w*|bug\b|analizz\w+ (il|la|i|le|tutt)|contratt\w*|business plan|piano (aziendale|di)|"
    r"algoritm\w*|vulnerabil\w*|sicurezza|più file|tutto il progetto|dimostra\w*|decision\w*)", re.I)
TENTATIVO_FALLITO = re.compile(
    r"(ancora (non|sbagliat|lo stesso)|di nuovo (sbagliat|non)|non funziona (ancora|più)|"
    r"stesso errore|non hai capito|riprova|è sbagliato)", re.I)


def consiglio_modello(p, st, sit):
    """Suggerisce il modello adatto al lavoro, con il risparmio in euro. Un consiglio per sessione."""
    fam = MODELLO["famiglia"]
    if not CFG["consiglio_modello"] or not fam or st.get("consiglio_modello"):
        return None
    if TENTATIVO_FALLITO.search(p):
        st["fallimenti"] = st.get("fallimenti", 0) + 1
    inizio = st.get("turni", 0) <= 3 and (sit.get("contesto") or 0) < 40000
    semplice = len(p) < 1500 and LAVORO_SEMPLICE.search(p) and not LAVORO_DIFFICILE.search(p)
    difficile = LAVORO_DIFFICILE.search(p) and not semplice
    nome = LISTINO[fam][2]

    if inizio and semplice and fam in PIU_LEGGERO:
        alt = PIU_LEGGERO[fam]
        risparmio = costo_sessione(fam) - costo_sessione(alt)
        extra = ""
        if fam == "opus":
            extra = (f" Se è un lavoro ripetitivo, con Haiku il risparmio sale a circa "
                     f"{euro(costo_sessione(fam) - costo_sessione('haiku'))}.")
        st["consiglio_modello"] = "leggero"
        return (f"🟡 Per questo basta il modello più leggero.\n"
                f"   Perché: {nome} costa circa {round(LISTINO[fam][0] / LISTINO[alt][0])} volte "
                f"{LISTINO[alt][2]} e per riscrivere, tradurre o riassumere non serve tanta potenza.\n"
                f"   Cosa fare: apri il lavoro con /model {alt} (adesso, non a metà chat), oppure passalo "
                f"a un subagent con model: {alt}.{extra}\n"
                f"   Risparmi: circa {euro(risparmio)} ogni {CFG['stima_richieste_sessione']} richieste "
                f"(listino API; in abbonamento i limiti durano di più).")

    if fam in PIU_POTENTE and ((inizio and difficile) or st.get("fallimenti", 0) >= 2):
        alt = PIU_POTENTE[fam]
        piu = costo_sessione(alt) - costo_sessione(fam)
        giro = (sit.get("contesto") or CFG["stima_ingresso_per_richiesta"]) * CFG["moltiplicatore_lettura_cache"] \
            + CFG["stima_ingresso_per_richiesta"]
        perche = ("hai già detto due volte che il risultato è sbagliato: ogni nuovo tentativo rilegge la chat"
                  if st.get("fallimenti", 0) >= 2 else
                  "è un lavoro con tanti passaggi e decisioni: un modello leggero rischia due o tre giri di correzione")
        st["consiglio_modello"] = "potente"
        return (f"🟠 Qui serve il modello più potente.\n"
                f"   Perché: {perche}.\n"
                + (f"   Cosa fare: /model {alt} adesso, finché la chat è corta.\n"
                   if (sit.get("contesto") or 0) < 20000 else
                   f"   Cosa fare: /nota, /clear, poi /model {alt} e /riparti (cambiare modello a metà chat "
                   f"la fa rileggere tutta).\n") +
                f"   Conto onesto: in euro spendi circa {euro(piu)} in più ogni {CFG['stima_richieste_sessione']} "
                f"richieste; in token risparmi i giri a vuoto (circa {k(giro)} token l'uno).")
    return None


def peso(token, richieste_dopo):
    """Token equivalenti (a prezzo input) che un contenuto costa restando nella chat."""
    return token * CFG["moltiplicatore_scrittura_cache"] + \
        token * CFG["moltiplicatore_lettura_cache"] * max(richieste_dopo, 0)


def file_stato(sid):
    p = DATI / "sessioni" / f"{re.sub(r'[^A-Za-z0-9_-]', '_', sid or 'senza-id')}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def leggi_stato(sid):
    try:
        return json.loads(file_stato(sid).read_text(encoding="utf-8"))
    except Exception:
        return {}


def scrivi_stato(sid, st):
    try:
        file_stato(sid).write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def registra(sid, tipo, token=0, equivalenti=0, dettaglio="", richieste=None):
    DATI.mkdir(parents=True, exist_ok=True)
    voce = {"ts": int(time.time()), "sid": sid, "tipo": tipo, "token": int(token),
            "equivalenti": int(equivalenti), "richieste_al_momento": richieste,
            "dettaglio": dettaglio[:200]}
    with open(DATI / "registro.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(voce, ensure_ascii=False) + "\n")
    if tipo in RISPARMI:
        tot = DATI / "totale.json"
        try:
            t = json.loads(tot.read_text())
        except Exception:
            t = {"equivalenti": 0}
        t["equivalenti"] = t.get("equivalenti", 0) + int(equivalenti)
        tot.write_text(json.dumps(t))


def esci(obj=None):
    if obj:
        print(json.dumps(obj, ensure_ascii=False))
    sys.exit(0)


def avvisa(testi):
    if testi:
        esci({"systemMessage": "🪙 FreeToken\n" + "\n".join("• " + t for t in testi)})
    esci()


def ultimo_uso_da_transcript(percorso):
    """Fallback se la barra di stato non è installata: contesto attuale e ora dell'ultima risposta."""
    try:
        with open(percorso, "rb") as f:
            f.seek(0, 2)
            dim = f.tell()
            f.seek(max(0, dim - 3_000_000))
            righe = f.read().decode("utf-8", "ignore").splitlines()
    except Exception:
        return None
    for r in reversed(righe):
        try:
            e = json.loads(r)
        except Exception:
            continue
        u = (e.get("message") or {}).get("usage")
        if e.get("type") == "assistant" and u:
            ctx = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + \
                u.get("cache_read_input_tokens", 0)
            ts = e.get("timestamp")
            quando = None
            if ts:
                try:
                    from datetime import datetime
                    quando = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
                except Exception:
                    pass
            return {"contesto": ctx, "ultima_risposta": quando,
                    "modello": (e.get("message") or {}).get("model")}
    return None


def situazione(dati, st):
    """Contesto, scadenza cache e token da riscrivere, dalla barra di stato o dal transcript."""
    s = st.get("sensore") or {}
    MODELLO["famiglia"] = famiglia(s.get("modello")) or famiglia(dati.get("model")) or \
        famiglia(st.get("modello")) or MODELLO["famiglia"]
    adesso = time.time()
    # L'ultima risposta vera dell'IA, dal registro della chat. Serve anche quando la barra di stato
    # esiste: nell'app desktop la barra non si aggiorna a ogni risposta e il suo dato può essere
    # vecchio di ore (era il bug del "pausa di 126 minuti" a chat appena usata).
    u = ultimo_uso_da_transcript(dati.get("transcript_path", "")) or {}
    MODELLO["famiglia"] = MODELLO["famiglia"] or famiglia(u.get("modello"))
    ultima = u.get("ultima_risposta")
    durata = CFG["durata_sconto_secondi"]
    if s and adesso - s.get("aggiornato", 0) < 6 * 3600:
        pc = s.get("prompt_cache") or {}
        scade = pc.get("expires_at")
        if scade and scade - s.get("aggiornato", 0) > 600:
            durata = 3600  # la sessione usa lo sconto da un'ora
        if ultima and (not scade or ultima + durata > scade):
            scade = ultima + durata  # l'IA ha risposto dopo l'ultima lettura della barra
        return {
            "contesto": max(s.get("contesto", 0), u.get("contesto", 0)),
            "finestra": s.get("finestra") or CFG["finestra_contesto"],
            "scade": scade,
            "ultima_risposta": ultima,
            "riscrittura": pc.get("recache_tokens_if_cold") or s.get("contesto", 0),
            "richieste": pc.get("requests"),
            "fonte": "barra",
        }
    scade = (ultima + durata) if ultima else None
    return {"contesto": u.get("contesto", 0), "finestra": CFG["finestra_contesto"],
            "scade": scade, "ultima_risposta": ultima, "riscrittura": u.get("contesto", 0),
            "richieste": None, "fonte": "transcript"}


def sembra_log(testo):
    righe = testo.splitlines()
    if len(righe) < 40:
        return False
    segni = re.compile(r"(\d{2}:\d{2}:\d{2}|ERROR|WARN|INFO|DEBUG|Traceback|^\s+at |Exception|\[\d+\])")
    return sum(1 for r in righe if segni.search(r)) > len(righe) * 0.3


def pesante(percorso):
    p = percorso.replace("\\", "/")
    if any(f"/{c.strip('/')}/" in f"/{p}" for c in CFG["cartelle_pesanti"]):
        return True
    return any(re.search(rx, p) for rx in CFG["file_pesanti"])


def token_file(percorso, max_righe=2000):
    """Token stimati di un file letto per intero (Read si ferma a circa 2000 righe)."""
    try:
        caratteri, righe = 0, 0
        with open(percorso, "r", encoding="utf-8", errors="ignore") as f:
            for riga in f:
                righe += 1
                if righe <= max_righe:
                    caratteri += len(riga)
        return tok(caratteri), righe
    except Exception:
        return 0, 0


# ---------------------------------------------------------------- eventi

def evento_prompt(d):
    sid = d.get("session_id", "")
    st = leggi_stato(sid)
    st["turni"] = st.get("turni", 0) + 1
    p = d.get("prompt", "") or ""
    if p.lstrip().startswith(CFG["prefisso_forza"]):
        scrivi_stato(sid, st)
        esci()

    sit = situazione(d, st)
    rigida = CFG["modalita"] == "rigida"
    avvisi = []

    # 1. Incolla enorme (log, documenti, codice intero)
    t = tok(p)
    if t >= CFG["incolla_blocco_token"]:
        righe = p.count("\n") + 1
        cosa = "un log" if sembra_log(p) else "un testo"
        costo = peso(t, CFG["richieste_medie_dopo"])
        if cosa == "un log":
            utile = peso(int(t * min(30, righe) / max(righe, 1)), CFG["richieste_medie_dopo"])
            battuta = f"All'IA ne bastano 30: le altre {num(max(righe - 30, 0))} sono soprammobili."
            consiglio = "incolla solo l'errore e le ultime 30 righe."
        else:
            utile = costo / 5
            battuta = "L'IA lo rileggerà a ogni risposta, come chi racconta sempre la stessa storia a cena."
            consiglio = "incolla solo la parte che ti serve, oppure salvalo in un file e chiedi di leggerne un pezzo."
        testo = (f"Stai incollando {cosa} di {num(righe)} righe. {battuta}\n"
                 f"   Perché: resta nella chat fino alla fine e lo paghi a ogni risposta "
                 f"(circa {k(costo)} token, circa {euro(eur(costo))}).\n"
                 f"   Cosa fare: {consiglio}\n"
                 f"   Risparmi: {risparmio(costo - utile)}.\n"
                 f"   Ti serve davvero tutto? Premi \"Modifica prompt\" e rimandalo iniziando con "
                 f"{CFG['prefisso_forza']}")
        if rigida:
            registra(sid, "incolla_bloccato", t, costo, cosa, sit.get("richieste"))
            scrivi_stato(sid, st)
            esci({"decision": "block", "reason": "🪙 FreeToken: " + testo})
        avvisi.append(testo)

    # 2. Cache scaduta con chat piena: il messaggio costerebbe una riscrittura completa
    adesso = time.time()
    scade = sit.get("scade")
    riscr = sit.get("riscrittura") or 0
    if scade and adesso > scade and riscr >= CFG["cache_fredda_soglia_token"] \
            and st.get("cache_avvisata") != scade:
        st["cache_avvisata"] = scade
        ultima = sit.get("ultima_risposta")
        minuti = int((adesso - ultima) / 60) if ultima else int((adesso - scade) / 60) + 5
        costo = riscr * CFG["moltiplicatore_scrittura_cache"]
        dopo = CFG["nota_token"] * CFG["moltiplicatore_scrittura_cache"]
        testo = (f"Pausa di {minuti} min: lo sconto sulla chat è scaduto. Il caffè l'hai pagato tu, "
                 f"la rilettura la paga questo messaggio.\n"
                 f"   Perché: mentre lavori la chat costa circa un decimo; dopo una pausa questo messaggio "
                 f"la rilegge tutta a prezzo pieno (circa {k(riscr)} token, circa {euro(eur(costo))}).\n"
                 f"   Cosa fare: /clear e poi /riparti, così riparti dalla nota e non da tutta la chat. "
                 f"Nessuna nota? Dopo /clear scrivi tu in 5 righe dove eri.\n"
                 f"   Risparmi: {risparmio(costo - dopo)} su questo solo messaggio.\n"
                 f"   Vuoi continuare qui lo stesso? Premi \"Modifica prompt\" e invia di nuovo: "
                 f"il secondo invio passa.")
        Path(DATI / "in_attesa").mkdir(parents=True, exist_ok=True)
        marcatore = DATI / "in_attesa" / (hashlib.md5(d.get("cwd", "").encode()).hexdigest() + ".json")
        marcatore.write_text(json.dumps({"ts": int(adesso), "riscrittura": riscr, "sid": sid}))
        scrivi_stato(sid, st)
        if rigida:
            esci({"decision": "block", "reason": "🪙 FreeToken: " + testo})
        avvisi.append(testo)

    # 3. Soglie di riempimento
    ctx, fin = sit.get("contesto") or 0, sit.get("finestra") or CFG["finestra_contesto"]
    pct = int(ctx * 100 / fin) if fin else 0
    fatte = set(st.get("soglie", []))
    for s in sorted(CFG["soglie_chat_percento"], reverse=True):
        if pct >= s and s not in fatte:
            fatte.update(x for x in CFG["soglie_chat_percento"] if x <= s)
            n = CFG["richieste_medie_dopo"]
            leggero = risparmio(max(ctx - CFG["nota_token"], 0) * CFG["moltiplicatore_lettura_cache"] * n)
            if s >= 85:
                avvisi.append(f"🔴 Chat piena all'{pct}%. Tra poco Claude la riassume da solo, in fretta, "
                              f"come un verbale scritto all'ultimo minuto.\n"
                              f"   Perché: nel riassunto si perdono pezzi, e intanto ogni messaggio costa il massimo.\n"
                              f"   Cosa fare adesso: /nota, poi /clear, poi /riparti.\n"
                              f"   Risparmi: {leggero} nei prossimi {n} messaggi.")
            elif s >= 70:
                avvisi.append(f"🟠 Chat al {pct}%. Claude ora rilegge più storia che lavoro.\n"
                              f"   Perché: le cose vecchie confondono le risposte e ogni messaggio costa di più.\n"
                              f"   Cosa fare: hai cambiato lavoro? /nota, /clear, /riparti. "
                              f"Stesso lavoro? /compact tieni solo decisioni, file aperti e prossimo passo.\n"
                              f"   Risparmi ripartendo: {leggero} nei prossimi {n} messaggi.")
            else:
                avvisi.append(f"🟡 Chat a metà ({pct}%). Da qui ogni messaggio si porta dietro tutto, "
                              f"come uno zaino che nessuno svuota.\n"
                              f"   Cosa fare: stesso lavoro? Continua pure. Lavoro nuovo? /nota e /clear.\n"
                              f"   Risparmi ripartendo: {leggero} nei prossimi {n} messaggi.")
            break
    st["soglie"] = sorted(fatte)

    # 4. Il "grazie" da migliaia di token
    corto = p.strip().lower()
    if len(corto) <= 30 and ctx >= CFG["grazie_soglia_token"] and \
            re.fullmatch(r"(grazie|ok|okay|perfetto|bene|ottimo|top|va bene|si|sì|👍|🙏)[\s!.,👍🙏]*.*", corto):
        equivalente = ctx * CFG["moltiplicatore_lettura_cache"]
        registra(sid, "grazie_costoso", ctx, equivalente, corto, sit.get("richieste"))
        avvisi.append(f"Hai scritto solo \"{p.strip()[:20]}\". Gentile, ma è il galateo più caro d'Italia.\n"
                      f"   Perché: per leggerlo Claude rilegge tutta la chat.\n"
                      f"   Cosa fare: il grazie mettilo nel messaggio con la prossima richiesta.\n"
                      f"   Risparmi: {risparmio(equivalente)} ogni volta.")

    # 5. Richieste di file interi
    if re.search(r"(riscriv\w*|dammi|mostra\w*|rigenera\w*|stampa\w*)\s+(tutto\s+)?(il\s+|l')?"
                 r"(file|codice|documento)\s+(completo|intero|per intero|da capo)|"
                 r"(tutto|intero)\s+il\s+file", p, re.I):
        uscita_evitata = 2400 * CFG["moltiplicatore_output"]  # 8 righe su 10 di un file medio
        avvisi.append("Rifare tutto il file per una modifica piccola è come ristampare il libro per un refuso.\n"
                      "   Perché: le risposte costano 5 volte le domande e poi restano nella chat.\n"
                      "   Cosa fare: chiedi \"applica solo le modifiche e dimmi le righe toccate\".\n"
                      f"   Risparmi: {risparmio(uscita_evitata)} a risposta, su un file medio.")

    # 6. Richieste vaghe che fanno esplorare tutto
    if re.search(r"\b(guarda tu|vedi tu|controlla tutto|cerca nel progetto|dove sta|da qualche parte|"
                 r"non so dove)\b", p, re.I) and not re.search(r"[\w/-]+\.\w{1,5}", p):
        avvisi.append("Senza dire dove, Claude parte per una caccia al tesoro pagata a token.\n"
                      "   Perché: apre file su file per trovare il punto, e tutto quello che legge resta nella chat.\n"
                      "   Cosa fare: se lo sai, indica il file e la riga (es. src/app.py riga 120).\n"
                      f"   Risparmi: di solito {risparmio(peso(30000, CFG['richieste_medie_dopo']))}.")

    # 7. Il modello giusto per il lavoro (una volta per sessione, con il risparmio in euro)
    if not avvisi:
        c = consiglio_modello(p, st, sit)
        if c:
            avvisi.append(c)

    scrivi_stato(sid, st)
    avvisa(avvisi)


def evento_pre_strumento(d):
    sid = d.get("session_id", "")
    st = leggi_stato(sid)
    nome = d.get("tool_name", "")
    inp = d.get("tool_input", {}) or {}
    sit = None

    def nega(motivo_claude, avviso_utente, tipo, token, equiv, dettaglio):
        chiave = f"{tipo}:{dettaglio}"
        gia = set(st.get("negati", []))
        if chiave in gia or CFG["modalita"] != "rigida":
            esci({"systemMessage": "🪙 FreeToken\n• " + avviso_utente})  # seconda volta: lascia passare
        gia.add(chiave)
        st["negati"] = sorted(gia)[-200:]
        scrivi_stato(sid, st)
        registra(sid, tipo, token, equiv, dettaglio, (sit or {}).get("richieste"))
        esci({"systemMessage": "🪙 FreeToken\n• " + avviso_utente,
              "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                     "permissionDecision": "deny",
                                     "permissionDecisionReason": motivo_claude}})

    if nome == "Read":
        percorso = inp.get("file_path", "")
        if inp.get("limit") or inp.get("offset") or not percorso:
            esci()
        if re.search(r"\.(png|jpe?g|gif|webp|pdf)$", percorso, re.I):
            esci()
        sit = situazione(d, st)
        if pesante(percorso):
            t, _ = token_file(percorso)
            nega(f"Il file {percorso} è un file generato o pesante (dipendenze, build, lock, dati). "
                 f"Leggerlo intero riempie il contesto. Usa Grep per cercare ciò che serve, oppure Read "
                 f"con offset e limit sulle righe utili.",
                 f"Fermata la lettura di {Path(percorso).name} (file pesante, ~{k(t)} token): Claude stava "
                 f"per leggersi l'elenco telefonico per trovare un numero. Ora cerca solo la parte che serve. "
                 f"Risparmi: {risparmio(peso(t, CFG['richieste_medie_dopo']))}.",
                 "lettura_bloccata", t, peso(t, CFG["richieste_medie_dopo"]), percorso)
        t, righe = token_file(percorso)
        if t >= CFG["lettura_blocco_token"]:
            consigliati = tok(int(CFG["lettura_righe_consigliate"] * (t * CFG["caratteri_per_token"] / max(min(righe, 2000), 1))))
            risparmio_t = max(t - consigliati, 0)
            nega(f"{percorso} ha {righe} righe (~{t} token). Prima usa Grep per trovare la sezione "
                 f"rilevante, poi Read con offset e limit (circa {CFG['lettura_righe_consigliate']} righe). "
                 f"Se ti serve davvero tutto, rileggilo: la seconda richiesta passa.",
                 f"Fermata la lettura intera di {Path(percorso).name}: {num(righe)} righe per trovarne "
                 f"una manciata. Claude leggerà solo la parte utile. "
                 f"Risparmi: {risparmio(peso(risparmio_t, CFG['richieste_medie_dopo']))}.",
                 "lettura_bloccata", risparmio_t, peso(risparmio_t, CFG["richieste_medie_dopo"]), percorso)
        esci()

    if nome == "Bash":
        cmd = (inp.get("command") or "").strip()
        m = re.fullmatch(r"cat\s+(['\"]?)([^|;&<>'\"]+)\1", cmd)
        if m:
            percorso = os.path.join(d.get("cwd", ""), m.group(2).strip())
            t, righe = token_file(percorso, max_righe=10**9)
            if t >= CFG["lettura_blocco_token"]:
                sit = situazione(d, st)
                nega(f"cat di {righe} righe (~{t} token) riempie il contesto. Usa grep -n, head, tail "
                     f"o sed -n 'A,Bp' sulle righe utili.",
                     f"Fermato un cat da ~{k(t)} token su {Path(percorso).name}: tutto il file per vederne "
                     f"un pezzo. Risparmi: {risparmio(peso(t, CFG['richieste_medie_dopo']))}.",
                     "cat_bloccato", t, peso(t, CFG["richieste_medie_dopo"]), percorso)
    esci()


def evento_post_strumento(d):
    sid = d.get("session_id", "")
    risposta = d.get("tool_response")
    try:
        testo = risposta if isinstance(risposta, str) else json.dumps(risposta, ensure_ascii=False)
    except Exception:
        testo = str(risposta)
    t = tok(testo)
    if t < CFG["uscita_pesante_token"]:
        esci()
    nome = d.get("tool_name", "")
    st = leggi_stato(sid)
    sit = situazione(d, st)
    registra(sid, "uscita_pesante", t, peso(t, CFG["richieste_medie_dopo"]), nome, sit.get("richieste"))
    dove = ("di un connettore: chiedi meno risultati (limite, filtri, date)" if nome.startswith("mcp__")
            else "filtra alla fonte: grep, head, --limit, --quiet")
    avvisa([f"{nome} ha rovesciato nella chat circa {k(t)} token, che ora restano lì come ospiti "
            f"che non se ne vanno.\n"
            f"   Perché: li rileggi a ogni risposta fino alla fine della chat.\n"
            f"   Cosa fare la prossima volta: {dove}.\n"
            f"   Risparmi: {risparmio(peso(t, CFG['richieste_medie_dopo']) * 0.8)} filtrando alla fonte."])


def evento_inizio(d):
    sid = d.get("session_id", "")
    fonte = d.get("source", "")
    cwd = d.get("cwd", os.getcwd())
    avvisi = []
    if famiglia(d.get("model")):
        st0 = leggi_stato(sid)
        st0["modello"] = d.get("model") if isinstance(d.get("model"), str) else (d.get("model") or {}).get("id")
        scrivi_stato(sid, st0)

    # Ripresa di una sessione con cache scaduta
    if fonte in ("resume", "fork") and d.get("prompt_cache_likely_expired"):
        ctx = d.get("context_tokens") or 0
        if ctx >= CFG["cache_fredda_soglia_token"]:
            minuti = int((d.get("seconds_since_last_response") or 0) / 60)
            costo = d.get("estimated_cache_write_usd")
            costo_eur = (costo * CFG['cambio_usd_eur'] if isinstance(costo, (int, float))
                         else eur(ctx * CFG["moltiplicatore_scrittura_cache"]))
            costo_txt = f"~{euro(costo_eur)}"
            nota_eur = eur(CFG["nota_token"] * CFG["moltiplicatore_scrittura_cache"])
            registra(sid, "ripresa_fredda", ctx, ctx * CFG["moltiplicatore_scrittura_cache"], fonte)
            avvisi.append(f"Stai riprendendo una sessione da ~{k(ctx)} token ferma da {minuti} min: "
                          f"il primo messaggio la riscrive tutta ({costo_txt}). Se c'è la nota: /clear e /riparti. "
                          f"Risparmi: circa {euro(max(costo_eur - nota_eur, 0))} su questo messaggio.")

    # Ripartenza pulita dopo un nostro avviso: risparmio misurato
    marcatore = DATI / "in_attesa" / (hashlib.md5(cwd.encode()).hexdigest() + ".json")
    if fonte in ("clear", "startup") and marcatore.exists():
        try:
            m = json.loads(marcatore.read_text())
            if time.time() - m.get("ts", 0) < 3600:
                nota = Path(cwd) / "NOTA-SESSIONE.md"
                t_nota = tok(nota.read_text(encoding="utf-8", errors="ignore")) if nota.exists() else 1000
                evitati = max(m.get("riscrittura", 0) - t_nota, 0)
                registra(sid, "cache_fredda_evitata", evitati,
                         evitati * CFG["moltiplicatore_scrittura_cache"], cwd)
                avvisi.append(f"Ripartenza pulita. Hai appena risparmiato "
                              f"{risparmio(evitati * CFG['moltiplicatore_scrittura_cache'])}. "
                              f"Usa /riparti per caricare la nota.")
        except Exception:
            pass
        try:
            marcatore.unlink()
        except Exception:
            pass

    # Regole sempre attive: entrano nel contesto all'avvio, così l'IA avvisa anche senza chiamare la skill
    contesto = REGOLE_SEMPRE_ATTIVE if fonte in ("startup", "clear", "resume", "compact", "fork") else ""

    # Check-up leggero, al massimo una volta al giorno per progetto
    if fonte == "startup":
        timbro = DATI / "timbri" / (hashlib.md5(cwd.encode()).hexdigest() + ".txt")
        timbro.parent.mkdir(parents=True, exist_ok=True)
        oggi = time.strftime("%Y-%m-%d")
        if not timbro.exists() or timbro.read_text() != oggi:
            timbro.write_text(oggi)
            avvisi.extend(diagnosi(cwd, breve=True))

    uscita = {}
    if avvisi:
        uscita["systemMessage"] = "🪙 FreeToken\n" + "\n".join("• " + t for t in avvisi)
    if contesto and CFG.get("regole_sempre_attive", True):
        uscita["hookSpecificOutput"] = {"hookEventName": "SessionStart", "additionalContext": contesto}
    esci(uscita or None)


def evento_compattazione(d):
    if d.get("trigger") == "auto":
        registra(d.get("session_id", ""), "compattazione_auto", 0, 0, "")
        avvisa(["Riassunto automatico al limite: Claude ha fatto le valigie in fretta e qualcosa è "
                "rimasto nell'armadio.\n   Perché: il riassunto d'emergenza perde dettagli e decisioni.\n"
                "   Cosa fare la prossima volta: /compact con istruzioni verso metà chat, oppure /nota e /clear.\n"
                "   Risparmi: ripartendo dalla nota rileggi 20 righe invece della chat intera."])
    esci()


def evento_cambio_modello(d):
    sid = d.get("session_id", "")
    sit = situazione(d, leggi_stato(sid))
    ctx = sit.get("contesto") or 0
    if ctx >= 20000:
        registra(sid, "cambio_modello", ctx, ctx * CFG["moltiplicatore_scrittura_cache"], "")
        situazione(d, leggi_stato(sid))
        avvisa([f"Cambiare modello a metà chat è come cambiare cuoco a metà cena: il nuovo riassaggia tutto. "
                f"Lo sconto vale per un solo modello, quindi il prossimo messaggio riscrive "
                f"~{k(ctx)} token (circa {euro(eur(ctx * CFG['moltiplicatore_scrittura_cache']))}). Meglio: tieni il modello e passa i lavori semplici a un subagent "
                f"con il modello piccolo."])
    esci()


def evento_fine(d):
    sid = d.get("session_id", "")
    st = leggi_stato(sid)
    finali = ((st.get("sensore") or {}).get("prompt_cache") or {}).get("requests")
    DATI.mkdir(parents=True, exist_ok=True)
    with open(DATI / "registro.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": int(time.time()), "sid": sid, "tipo": "chiusura",
                            "richieste_finali": finali}) + "\n")
    esci()


def hook():
    try:
        d = json.load(sys.stdin)
    except Exception:
        esci()
    ev = d.get("hook_event_name", "")
    try:
        {"UserPromptSubmit": evento_prompt,
         "PreToolUse": evento_pre_strumento,
         "PostToolUse": evento_post_strumento,
         "SessionStart": evento_inizio,
         "PreCompact": evento_compattazione,
         "PreModelSwitch": evento_cambio_modello,
         "SessionEnd": evento_fine}.get(ev, lambda _d: esci())(d)
    except SystemExit:
        raise
    except Exception:
        esci()  # il guardiano non deve mai bloccare il lavoro per un suo errore


# ---------------------------------------------------------------- diagnosi

def connettori(cwd):
    nomi = set()
    for f, chiavi in ((Path.home() / ".claude.json", None), (Path(cwd) / ".mcp.json", None)):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        nomi.update((j.get("mcpServers") or {}).keys())
        progetto = (j.get("projects") or {}).get(str(cwd)) or {}
        nomi.update((progetto.get("mcpServers") or {}).keys())
    return sorted(nomi)


def diagnosi(cwd, breve=False):
    out = []
    for f in (Path(cwd) / "CLAUDE.md", Path.home() / ".claude" / "CLAUDE.md"):
        if f.exists():
            testo = f.read_text(encoding="utf-8", errors="ignore")
            righe = testo.count("\n") + 1
            if righe > CFG["claude_md_righe_max"]:
                out.append(f"{f.name} in {f.parent.name}: {righe} righe (~{k(tok(testo))} token) pagati "
                           f"a ogni richiesta. Tienilo sotto {CFG['claude_md_righe_max']} righe; "
                           f"il resto spostalo in skill o file da leggere solo quando servono.")
    c = connettori(cwd)
    if len(c) > CFG["connettori_max"]:
        out.append(f"{len(c)} connettori MCP attivi ({', '.join(c[:6])}{'...' if len(c) > 6 else ''}). "
                   f"Ognuno porta le sue istruzioni nel contesto: spegni quelli che questo progetto non usa.")
    if not breve:
        impost = Path(cwd) / ".claude" / "settings.json"
        negati = ""
        try:
            negati = json.dumps(json.loads(impost.read_text()).get("permissions", {}).get("deny", []))
        except Exception:
            pass
        presenti = [c for c in CFG["cartelle_pesanti"] if (Path(cwd) / c.strip("/")).exists()
                    and c.strip("/") not in negati]
        if presenti:
            regole = ", ".join(f'"Read(./{c.strip("/")}/**)"' for c in presenti)
            out.append(f"Cartelle pesanti leggibili: {', '.join(presenti)}. Aggiungi in .claude/settings.json "
                       f"→ permissions.deny: [{regole}]")
        if not (Path(cwd) / "NOTA-SESSIONE.md").exists():
            out.append("Nessuna NOTA-SESSIONE.md: a fine lavoro usa /nota, così domani riparti da 20 righe "
                       "e non da 150 messaggi.")
    return out


# ---------------------------------------------------------------- comandi

def leggi_registro():
    voci = []
    try:
        with open(DATI / "registro.jsonl", encoding="utf-8") as f:
            for r in f:
                try:
                    voci.append(json.loads(r))
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    return voci


def ricalcola(voci):
    finali = {v["sid"]: v.get("richieste_finali") for v in voci if v.get("tipo") == "chiusura"}
    for v in voci:
        if v.get("tipo") in PERSISTENTI and v.get("richieste_al_momento") is not None \
                and finali.get(v["sid"]) is not None:
            dopo = finali[v["sid"]] - v["richieste_al_momento"]
            v["equivalenti"] = int(peso(v["token"], dopo))
            v["misurato"] = True
    return [v for v in voci if v.get("tipo") != "chiusura"]


def cmd_conto(args):
    voci = ricalcola(leggi_registro())
    if not voci:
        print("🪙 FreeToken: ancora nessun dato. Lavora qualche sessione e riprova.")
        return
    inizio = time.strftime("%d/%m/%Y", time.localtime(min(v["ts"] for v in voci)))
    sessioni = len({v["sid"] for v in voci})
    righe = lambda gruppo: [(et, [v for v in voci if v["tipo"] == t]) for t, et in gruppo.items()]
    if "--json" in args:
        print(json.dumps(voci, ensure_ascii=False, indent=1))
        return
    print(f"\n🪙 FREETOKEN · il tuo conto dal {inizio} · {sessioni} sessioni\n")
    print("RISPARMIATI (stima prudente, in token equivalenti a prezzo di input)")
    tot = 0
    for et, vv in righe(RISPARMI):
        if vv:
            e = sum(v["equivalenti"] for v in vv)
            tot += e
            print(f"  {et:<38} {len(vv):>4} volte   {k(e):>7}   ≈ {euro(eur(e)):>10}")
    print(f"  {'TOTALE':<38} {'':>10}   {k(tot):>7}   ≈ {euro(eur(tot)):>10}")
    misurati = sum(1 for v in voci if v.get("misurato"))
    if misurati:
        print(f"  ({misurati} voci ricalcolate sulle richieste reali delle sessioni)")
    print("\nSPRECHI RILEVATI (qui c'è ancora da guadagnare)")
    sp_tot, classifica = 0, []
    for et, vv in righe(SPRECHI):
        if vv:
            e = sum(v["equivalenti"] for v in vv)
            sp_tot += e
            classifica.append((e, et, len(vv)))
            print(f"  {et:<38} {len(vv):>4} volte   {k(e):>7}   ≈ {euro(eur(e)):>10}")
    if not classifica:
        print("  nessuno. Bel lavoro.")
    consigli = {
        "Risultati pesanti entrati nella chat": "filtra gli output alla fonte (grep, head, limiti nei connettori)",
        "Messaggi di cortesia a chat piena": "metti il grazie insieme al prossimo comando",
        "Sessioni riprese a cache scaduta": "chiudi con /nota e riparti con /clear + /riparti",
        "Auto-compattazioni al limite": "/compact con istruzioni verso metà chat",
        "Cambi di modello a metà sessione": "decidi il modello all'inizio, i lavori semplici ai subagent",
    }
    if classifica:
        print("\nLE TUE ABITUDINI PIÙ CARE")
        for i, (e, et, n) in enumerate(sorted(classifica, reverse=True)[:3], 1):
            print(f"  {i}. {et}: {consigli.get(et, '')}")
    print(f"\nPrezzo usato: {CFG['prezzo_input_per_milione_usd']} dollari per milione di token in ingresso, "
          f"cambio {CFG['cambio_usd_eur']} € per dollaro (cambiali in {DATI / 'config.json'}).\n")


def testo_messaggio(m):
    c = (m or {}).get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return " ".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")
    return ""


def cmd_audit(args):
    giorni = 30
    if "--giorni" in args:
        try:
            giorni = int(args[args.index("--giorni") + 1])
        except Exception:
            pass
    limite = time.time() - giorni * 86400
    vuoto = re.compile(r"(nessun|nessuna|niente di nuovo|0 risultati|zero|nothing|no new|"
                       r"nulla da|tutto in ordine|non ci sono|non ho trovato)", re.I)
    gruppi = {}
    for f in glob.glob(str(Path.home() / ".claude" / "projects" / "*" / "*.jsonl")):
        if os.path.getmtime(f) < limite:
            continue
        primo, ultimo, visti, eq = None, "", set(), 0.0
        try:
            with open(f, encoding="utf-8", errors="ignore") as fh:
                for r in fh:
                    try:
                        e = json.loads(r)
                    except Exception:
                        continue
                    m = e.get("message") or {}
                    if e.get("type") == "user" and primo is None:
                        t = testo_messaggio(m).strip()
                        if t and not t.startswith("<"):
                            primo = t
                    if e.get("type") == "assistant":
                        u = m.get("usage")
                        mid = m.get("id")
                        if u and mid not in visti:
                            visti.add(mid)
                            eq += u.get("input_tokens", 0) + \
                                u.get("cache_creation_input_tokens", 0) * CFG["moltiplicatore_scrittura_cache"] + \
                                u.get("cache_read_input_tokens", 0) * CFG["moltiplicatore_lettura_cache"] + \
                                u.get("output_tokens", 0) * CFG["moltiplicatore_output"]
                        t = testo_messaggio(m).strip()
                        if t:
                            ultimo = t
        except Exception:
            continue
        if not primo:
            continue
        chiave = re.sub(r"\d+", "#", re.sub(r"\s+", " ", primo.lower()))[:160]
        g = gruppi.setdefault(chiave, {"giri": 0, "vuoti": 0, "eq": 0.0, "esempio": primo[:90]})
        g["giri"] += 1
        g["eq"] += eq
        if len(ultimo) < 300 and vuoto.search(ultimo) or not ultimo:
            g["vuoti"] += 1
    ripetuti = sorted((g for g in gruppi.values() if g["giri"] >= 5), key=lambda g: -g["eq"])
    print(f"\n🪙 FREETOKEN · audit dei lavori ripetuti (ultimi {giorni} giorni)\n")
    if not ripetuti:
        print("Nessun lavoro ripetuto almeno 5 volte nelle sessioni locali di Claude Code.\n"
              "Nota: le attività programmate nel cloud non lasciano file qui; controlla il loro storico.\n")
        return
    print(f"{'giri':>5} {'a vuoto':>8} {'token eq.':>10} {'≈ €':>10}  lavoro")
    for g in ripetuti[:15]:
        print(f"{g['giri']:>5} {g['vuoti']:>8} {k(g['eq']):>10} {euro(eur(g['eq'])):>10}  {g['esempio']}")
    peggiore = max(ripetuti, key=lambda g: g["vuoti"])
    if peggiore["vuoti"]:
        quota = peggiore["eq"] * peggiore["vuoti"] / peggiore["giri"]
        print(f"\nIl più sprecone: \"{peggiore['esempio'][:60]}\" · {peggiore['vuoti']} giri su "
              f"{peggiore['giri']} senza risultati · ~{k(quota)} token buttati.\n"
              f"Rimedio: una guardia a costo zero che sveglia l'IA solo se c'è lavoro "
              f"(vedi claude-code/esempi/guardia.sh), oppure meno giri al giorno.\n")


def cmd_pagella(args):
    cwd = args[0] if args else os.getcwd()
    print(f"\n🪙 FREETOKEN · pagella di {cwd}\n")
    problemi = diagnosi(cwd)
    if not problemi:
        print("  Progetto in ordine. Niente da segnalare.\n")
    for i, p in enumerate(problemi, 1):
        print(f"  {i}. {p}\n")


def cmd_misura(args):
    if not args:
        print("uso: freetoken misura FILE [richieste_dopo]")
        return
    testo = sys.stdin.read() if args[0] == "-" else Path(args[0]).read_text(encoding="utf-8", errors="ignore")
    n = int(args[1]) if len(args) > 1 else CFG["richieste_medie_dopo"]
    t = tok(testo)
    e = peso(t, n)
    print(f"~{num(t)} token. Tenuto nella chat per {n} richieste: ~{num(e)} token equivalenti "
          f"(≈ {euro(eur(e))}).")


def cmd_modello(args):
    """Listino in euro e risparmio tra modelli su una sessione tipica."""
    n = int(args[0]) if args and args[0].isdigit() else CFG["stima_richieste_sessione"]
    print(f"\n🪙 FREETOKEN · quale modello conviene (listino API, novembre 2026, in euro)\n")
    print(f"  {'modello':<15} {'ingresso':>9} {'uscita':>8}   sessione da {n} richieste")
    for fam, (pi, po, nome) in LISTINO.items():
        c = CFG["cambio_usd_eur"]
        print(f"  {nome:<15} {euro(pi * c):>9} {euro(po * c):>8}   {euro(costo_sessione(fam, n)):>10}")
    print("  (prezzi per milione di token)\n")
    for grande, piccolo in (("opus", "sonnet"), ("opus", "haiku"), ("astra", "sol"), ("astra", "terra")):
        d = costo_sessione(grande, n) - costo_sessione(piccolo, n)
        print(f"  {LISTINO[grande][2]} → {LISTINO[piccolo][2]}: risparmi circa {euro(d)} a sessione")
    print("\nQuando scendere: riscrivere, tradurre, riassumere, formattare, mail, lavori ripetitivi.\n"
          "Quando salire: strategia, codice su più file, analisi lunghe, dopo due tentativi falliti.\n"
          "Quando cambiare: all'inizio o dopo /nota e /clear, mai a metà di una chat lunga.\n"
          f"Base del calcolo: {num(CFG['stima_ingresso_per_richiesta'])} token in ingresso e "
          f"{num(CFG['stima_uscita_per_richiesta'])} in uscita per richiesta. In abbonamento non paghi "
          f"in euro: risparmi limiti.\n")


def cmd_calcolatore(args):
    import webbrowser
    locale = DATI / "calcolatore.html"
    if not locale.exists():
        locale = QUI.parent / "skills" / "freetoken" / "calcolatore.html"
    print(f"Calcolatore: {locale}\nVersione online: https://giandoms.github.io/FreeToken/strumenti/calcolatore.html" )
    webbrowser.open(locale.resolve().as_uri())


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "aiuto"):
        print(__doc__)
        return
    {"hook": lambda _a: hook(), "conto": cmd_conto, "audit": cmd_audit,
     "pagella": cmd_pagella, "misura": cmd_misura, "modello": cmd_modello, "calcolatore": cmd_calcolatore}.get(a[0], lambda _a: print(__doc__))(a[1:])


if __name__ == "__main__":
    main()
