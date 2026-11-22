#!/usr/bin/env python3
"""
FreeToken: il guardiano dei token per Claude Code.

Un solo script per tutto:
  python3 freetoken.py hook          <- lo chiama Claude Code (legge l'evento da stdin)
  python3 freetoken.py conto         <- quanto hai risparmiato e dove sprechi
  python3 freetoken.py audit         <- lavori automatici che girano a vuoto
  python3 freetoken.py pagella [dir] <- check-up del progetto (CLAUDE.md, connettori, cartelle pesanti)
  python3 freetoken.py misura FILE   <- quanto pesa un file nella chat
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
    "cache_fredda_soglia_token": 50000,  # sotto questa soglia riscrivere la cache costa poco
    "grazie_soglia_token": 60000,
    "soglie_chat_percento": [50, 70, 85],
    "claude_md_righe_max": 120,
    "connettori_max": 5,
    "richieste_medie_dopo": 25,          # se non sappiamo quante richieste seguiranno
    "moltiplicatore_scrittura_cache": 1.25,
    "moltiplicatore_lettura_cache": 0.1,
    "moltiplicatore_output": 5.0,
    "prezzo_input_per_milione_usd": 5.0, # imposta il prezzo del tuo modello
    "cartelle_pesanti": ["node_modules", "dist", "build", ".next", "vendor", ".venv",
                          "__pycache__", "coverage", ".git/"],
    "file_pesanti": [r"\.lock$", r"package-lock\.json$", r"\.min\.(js|css)$", r"\.map$",
                     r"\.(csv|tsv|parquet|sqlite|db)$"],
    "statusline_precedente": "",
    "modalita": "rigida",               # "rigida" blocca, "morbida" avvisa soltanto
}

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
    for f in (QUI.parent / "config" / "freetoken.json", DATI / "config.json"):
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


def usd(equivalenti):
    return equivalenti / 1_000_000 * CFG["prezzo_input_per_milione_usd"]


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
            return {"contesto": ctx, "ultima_risposta": quando}
    return None


def situazione(dati, st):
    """Contesto, scadenza cache e token da riscrivere, dalla barra di stato o dal transcript."""
    s = st.get("sensore") or {}
    adesso = time.time()
    if s and adesso - s.get("aggiornato", 0) < 6 * 3600:
        pc = s.get("prompt_cache") or {}
        return {
            "contesto": s.get("contesto", 0),
            "finestra": s.get("finestra") or CFG["finestra_contesto"],
            "scade": pc.get("expires_at"),
            "riscrittura": pc.get("recache_tokens_if_cold") or s.get("contesto", 0),
            "richieste": pc.get("requests"),
            "fonte": "barra",
        }
    u = ultimo_uso_da_transcript(dati.get("transcript_path", "")) or {}
    scade = (u["ultima_risposta"] + 300) if u.get("ultima_risposta") else None  # ipotesi: cache 5 minuti
    return {"contesto": u.get("contesto", 0), "finestra": CFG["finestra_contesto"],
            "scade": scade, "riscrittura": u.get("contesto", 0), "richieste": None,
            "fonte": "transcript"}


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
        consiglio = ("incolla solo l'errore e le ultime 30 righe." if cosa == "un log"
                     else "salvalo in un file e chiedi di leggere solo la parte che ti serve.")
        testo = (f"Stai incollando {cosa} di {num(righe)} righe. Resterebbe nella chat fino alla fine "
                 f"e lo pagheresti a ogni risposta (circa {k(costo)} token, {usd(costo):.2f} $).\n"
                 f"   Cosa fare: {consiglio}\n"
                 f"   Ti serve davvero tutto? Rimandalo iniziando con {CFG['prefisso_forza']}")
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
        minuti = int((adesso - scade) / 60) + 1
        costo = riscr * CFG["moltiplicatore_scrittura_cache"]
        testo = (f"Hai fatto una pausa e lo sconto sulla chat è scaduto ({minuti} min fa). "
                 f"Questo messaggio farebbe rileggere tutto a prezzo pieno (circa {k(riscr)} token, "
                 f"{usd(costo):.2f} $).\n"
                 f"   Cosa fare: /clear e poi /riparti (riparti dalla nota, quasi gratis). "
                 f"Nessuna nota? Dopo /clear scrivi tu in 5 righe dove eri.\n"
                 f"   Vuoi continuare qui lo stesso? Rimanda il messaggio.")
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
            if s >= 85:
                avvisi.append(f"🔴 Chat piena all'{pct}%: tra poco Claude la riassume da solo, in fretta "
                              f"e perdendo pezzi.\n   Cosa fare adesso: /nota, poi /clear, poi /riparti.")
            elif s >= 70:
                avvisi.append(f"🟠 Chat al {pct}%: da qui le risposte peggiorano e ogni messaggio costa di più.\n"
                              f"   Cosa fare: hai cambiato lavoro? /nota, /clear, /riparti. "
                              f"Stesso lavoro? /compact tieni solo decisioni, file aperti e prossimo passo")
            else:
                avvisi.append(f"🟡 Chat a metà ({pct}%). Ogni messaggio ora si porta dietro tutto questo.\n"
                              f"   Domanda da farti: sto ancora facendo lo stesso lavoro? Se no: /nota e /clear.")
            break
    st["soglie"] = sorted(fatte)

    # 4. Il "grazie" da migliaia di token
    corto = p.strip().lower()
    if len(corto) <= 30 and ctx >= CFG["grazie_soglia_token"] and \
            re.fullmatch(r"(grazie|ok|okay|perfetto|bene|ottimo|top|va bene|si|sì|👍|🙏)[\s!.,👍🙏]*.*", corto):
        equivalente = ctx * CFG["moltiplicatore_lettura_cache"]
        registra(sid, "grazie_costoso", ctx, equivalente, corto, sit.get("richieste"))
        avvisi.append(f"Anche \"{p.strip()[:20]}\" fa rileggere tutta la chat (circa {k(equivalente)} token).\n"
                      f"   Cosa fare: il grazie mettilo nel messaggio con la prossima richiesta.")

    # 5. Richieste di file interi
    if re.search(r"(riscriv\w*|dammi|mostra\w*|rigenera\w*|stampa\w*)\s+(tutto\s+)?(il\s+|l')?"
                 r"(file|codice|documento)\s+(completo|intero|per intero|da capo)|"
                 r"(tutto|intero)\s+il\s+file", p, re.I):
        avvisi.append("Rifare tutto il file costa caro: le risposte lunghe si pagano di più "
                      "e restano nella chat.\n   Cosa fare: chiedi \"applica solo le modifiche e dimmi le righe toccate\".")

    # 6. Richieste vaghe che fanno esplorare tutto
    if re.search(r"\b(guarda tu|vedi tu|controlla tutto|cerca nel progetto|dove sta|da qualche parte|"
                 r"non so dove)\b", p, re.I) and not re.search(r"[\w/-]+\.\w{1,5}", p):
        avvisi.append("Senza dire dove, Claude deve frugare in tutto il progetto e la chat si riempie.\n"
                      "   Cosa fare: se lo sai, indica il file e la riga (es. src/app.py riga 120).")

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
                 f"Fermata la lettura di {Path(percorso).name} (file pesante, ~{k(t)} token). "
                 f"Claude cercherà solo la parte che serve.",
                 "lettura_bloccata", t, peso(t, CFG["richieste_medie_dopo"]), percorso)
        t, righe = token_file(percorso)
        if t >= CFG["lettura_blocco_token"]:
            consigliati = tok(int(CFG["lettura_righe_consigliate"] * (t * CFG["caratteri_per_token"] / max(min(righe, 2000), 1))))
            risparmio = max(t - consigliati, 0)
            nega(f"{percorso} ha {righe} righe (~{t} token). Prima usa Grep per trovare la sezione "
                 f"rilevante, poi Read con offset e limit (circa {CFG['lettura_righe_consigliate']} righe). "
                 f"Se ti serve davvero tutto, rileggilo: la seconda richiesta passa.",
                 f"Fermata la lettura intera di {Path(percorso).name}: {num(righe)} righe, ~{k(t)} token. "
                 f"Claude leggerà solo la parte utile.",
                 "lettura_bloccata", risparmio, peso(risparmio, CFG["richieste_medie_dopo"]), percorso)
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
                     f"Fermato un cat da ~{k(t)} token su {Path(percorso).name}.",
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
    avvisa([f"{nome} ha portato nella chat un risultato enorme (circa {k(t)} token) che ora resta lì.\n"
            f"   Cosa fare la prossima volta: {dove}."])


def evento_inizio(d):
    sid = d.get("session_id", "")
    fonte = d.get("source", "")
    cwd = d.get("cwd", os.getcwd())
    avvisi = []

    # Ripresa di una sessione con cache scaduta
    if fonte in ("resume", "fork") and d.get("prompt_cache_likely_expired"):
        ctx = d.get("context_tokens") or 0
        if ctx >= CFG["cache_fredda_soglia_token"]:
            minuti = int((d.get("seconds_since_last_response") or 0) / 60)
            costo = d.get("estimated_cache_write_usd")
            costo_txt = f"~{costo:.2f} $" if isinstance(costo, (int, float)) else f"~{usd(ctx*1.25):.2f} $"
            registra(sid, "ripresa_fredda", ctx, ctx * CFG["moltiplicatore_scrittura_cache"], fonte)
            avvisi.append(f"Stai riprendendo una sessione da ~{k(ctx)} token ferma da {minuti} min: "
                          f"il primo messaggio la riscrive tutta ({costo_txt}). Se c'è la nota: /clear e /riparti.")

    # Ripartenza pulita dopo un nostro avviso: risparmio misurato
    marcatore = DATI / "in_attesa" / (hashlib.md5(cwd.encode()).hexdigest() + ".json")
    if fonte in ("clear", "startup") and marcatore.exists():
        try:
            m = json.loads(marcatore.read_text())
            if time.time() - m.get("ts", 0) < 3600:
                nota = Path(cwd) / "NOTA-SESSIONE.md"
                t_nota = tok(nota.read_text(encoding="utf-8", errors="ignore")) if nota.exists() else 1000
                risparmio = max(m.get("riscrittura", 0) - t_nota, 0)
                registra(sid, "cache_fredda_evitata", risparmio,
                         risparmio * CFG["moltiplicatore_scrittura_cache"], cwd)
                avvisi.append(f"Ripartenza pulita: hai evitato di riscrivere ~{k(risparmio)} token. "
                              f"Usa /riparti per caricare la nota.")
        except Exception:
            pass
        try:
            marcatore.unlink()
        except Exception:
            pass

    # Check-up leggero, al massimo una volta al giorno per progetto
    if fonte == "startup":
        timbro = DATI / "timbri" / (hashlib.md5(cwd.encode()).hexdigest() + ".txt")
        timbro.parent.mkdir(parents=True, exist_ok=True)
        oggi = time.strftime("%Y-%m-%d")
        if not timbro.exists() or timbro.read_text() != oggi:
            timbro.write_text(oggi)
            avvisi.extend(diagnosi(cwd, breve=True))

    avvisa(avvisi)


def evento_compattazione(d):
    if d.get("trigger") == "auto":
        registra(d.get("session_id", ""), "compattazione_auto", 0, 0, "")
        avvisa(["Auto-compattazione al limite: riassume tutto in fretta e perde dettagli. "
                "La prossima volta: /compact con istruzioni verso metà chat, o /nota e /clear."])
    esci()


def evento_cambio_modello(d):
    sid = d.get("session_id", "")
    sit = situazione(d, leggi_stato(sid))
    ctx = sit.get("contesto") or 0
    if ctx >= 20000:
        registra(sid, "cambio_modello", ctx, ctx * CFG["moltiplicatore_scrittura_cache"], "")
        avvisa([f"La cache vale per un solo modello: cambiandolo adesso il prossimo messaggio riscrive "
                f"~{k(ctx)} token. Meglio: tieni il modello e passa i lavori semplici a un subagent "
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
            print(f"  {et:<38} {len(vv):>4} volte   {k(e):>7}   ≈ {usd(e):6.2f} $")
    print(f"  {'TOTALE':<38} {'':>10}   {k(tot):>7}   ≈ {usd(tot):6.2f} $")
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
            print(f"  {et:<38} {len(vv):>4} volte   {k(e):>7}   ≈ {usd(e):6.2f} $")
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
    print(f"\nPrezzo usato: {CFG['prezzo_input_per_milione_usd']} $ per milione di token in ingresso "
          f"(cambialo in {DATI / 'config.json'}).\n")


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
    print(f"{'giri':>5} {'a vuoto':>8} {'token eq.':>10} {'≈ $':>8}  lavoro")
    for g in ripetuti[:15]:
        print(f"{g['giri']:>5} {g['vuoti']:>8} {k(g['eq']):>10} {usd(g['eq']):>8.2f}  {g['esempio']}")
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
          f"(≈ {usd(e):.2f} $).")


def cmd_calcolatore(args):
    import webbrowser
    locale = DATI / "calcolatore.html"
    if not locale.exists():
        locale = QUI.parent.parent / "strumenti" / "calcolatore.html"
    print(f"Calcolatore: {locale}\nVersione online: https://giandoms.github.io/FreeToken/strumenti/calcolatore.html" )
    webbrowser.open(locale.resolve().as_uri())


def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "aiuto"):
        print(__doc__)
        return
    {"hook": lambda _a: hook(), "conto": cmd_conto, "audit": cmd_audit,
     "pagella": cmd_pagella, "misura": cmd_misura, "calcolatore": cmd_calcolatore}.get(a[0], lambda _a: print(__doc__))(a[1:])


if __name__ == "__main__":
    main()
