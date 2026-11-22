#!/usr/bin/env python3
"""
Barra di stato di FreeToken.

Fa due lavori:
1. ti mostra quanto è piena la chat, quanto manca alla scadenza della cache,
   perché la cache si è rotta e quanto hai risparmiato finora;
2. fa da sensore: salva lo stato della cache per i controlli che partono
   quando mandi un messaggio (la barra lo riceve da Claude Code, gli agganci no).

Se avevi già una barra di stato, viene mostrata sopra la nostra.
"""
import json
import subprocess
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__file__))
import freetoken  # noqa: E402

GRIGIO, VERDE, GIALLO, ROSSO, FINE = "\033[90m", "\033[32m", "\033[33m", "\033[31m", "\033[0m"
CAUSE = {
    "tools_changed": "app collegate cambiate",
    "system_prompt_changed": "istruzioni cambiate",
    "ttl_expired_5m": "pausa oltre 5 min",
    "ttl_expired_1h": "pausa oltre 1 ora",
    "likely_server_side": "lato server",
    "model_changed": "modello cambiato",
}


def main():
    grezzo = sys.stdin.read()
    try:
        d = json.loads(grezzo)
    except Exception:
        print("🪙")
        return

    precedente = freetoken.CFG.get("statusline_precedente")
    if precedente:
        try:
            out = subprocess.run(precedente, shell=True, input=grezzo, capture_output=True,
                                 text=True, timeout=2).stdout.rstrip()
            if out:
                print(out)
        except Exception:
            pass

    cw = d.get("context_window") or {}
    pc = d.get("prompt_cache") or {}
    sid = d.get("session_id", "")
    contesto = cw.get("total_input_tokens") or 0
    finestra = cw.get("context_window_size") or freetoken.CFG["finestra_contesto"]

    st = freetoken.leggi_stato(sid)
    st["sensore"] = {"aggiornato": int(time.time()), "contesto": contesto, "finestra": finestra,
                     "prompt_cache": pc, "modello": (d.get("model") or {}).get("id")}
    freetoken.scrivi_stato(sid, st)

    parti = []
    pct = int(cw.get("used_percentage") or (contesto * 100 / finestra if finestra else 0))
    colore = ROSSO if pct >= 70 else GIALLO if pct >= 50 else VERDE
    pieno = min(pct // 10, 10)
    parti.append(f"🪙 {colore}{'█' * pieno}{'░' * (10 - pieno)} {pct}%{FINE}")

    adesso = time.time()
    scade = pc.get("expires_at")
    if scade:
        resto = int(scade - adesso)
        if resto > 0:
            m, s = divmod(resto, 60)
            c = GIALLO if resto < 60 else GRIGIO
            parti.append(f"{c}⏳ sconto {m}:{s:02d}{FINE}")
        else:
            riscr = pc.get("recache_tokens_if_cold") or contesto
            if riscr >= freetoken.CFG["cache_fredda_soglia_token"]:
                parti.append(f"{ROSSO}🧊 sconto scaduto: il prossimo msg riscrive {freetoken.k(riscr)} → /clear + /riparti{FINE}")
            else:
                parti.append(f"{GRIGIO}🧊 sconto scaduto{FINE}")

    ultima = pc.get("last_miss_at")
    causa = (pc.get("last_miss_cause") or {}).get("causes") or []
    if ultima and adesso - ultima < 120 and causa:
        parti.append(f"{GIALLO}⚠ sconto perso: {', '.join(CAUSE.get(c, c) for c in causa)}{FINE}")

    costo = (d.get("cost") or {}).get("total_cost_usd")
    if costo:
        parti.append(f"{GRIGIO}sessione {costo:.2f} ${FINE}")

    try:
        tot = json.loads((freetoken.DATI / "totale.json").read_text()).get("equivalenti", 0)
        if tot:
            parti.append(f"{VERDE}risparmiati {freetoken.k(tot)}{FINE}")
    except Exception:
        pass

    print("  ".join(parti))


if __name__ == "__main__":
    main()
