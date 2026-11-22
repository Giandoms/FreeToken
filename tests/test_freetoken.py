#!/usr/bin/env python3
"""Collaudo di FreeToken con eventi simulati. Uso: python3 tests/test_freetoken.py"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent / "plugins" / "freetoken" / "scripts"
TMP = Path(tempfile.mkdtemp())
ENV = dict(os.environ, FREETOKEN_HOME=str(TMP / "dati"))
ok = fail = 0


def gira(script, dati, *args):
    r = subprocess.run([sys.executable, str(RADICE / script), *args], input=json.dumps(dati),
                       capture_output=True, text=True, env=ENV, timeout=20)
    if r.returncode != 0:
        print(r.stderr)
    return r.stdout.strip()


def verifica(nome, cond, dettaglio=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  ✓ {nome}")
    else:
        fail += 1
        print(f"  ✗ {nome}  {dettaglio}")


base = {"session_id": "prova1", "cwd": str(TMP), "transcript_path": str(TMP / "t.jsonl")}

print("Incolla enorme")
log = "\n".join(f"2026-11-21 10:00:{i%60:02d} ERROR qualcosa è andato storto riga {i}" for i in range(800))
out = gira("freetoken.py", {**base, "hook_event_name": "UserPromptSubmit", "prompt": log}, "hook")
verifica("blocca il log", '"decision": "block"' in out, out[:200])
out = gira("freetoken.py", {**base, "hook_event_name": "UserPromptSubmit", "prompt": "!!" + log}, "hook")
verifica("lascia passare con !!", out == "", out[:200])

print("Barra di stato e cache fredda")
barra = {"session_id": "prova1", "model": {"id": "claude-opus-5-5"},
         "context_window": {"total_input_tokens": 140000, "context_window_size": 200000, "used_percentage": 70},
         "prompt_cache": {"expires_at": int(time.time()) - 400, "recache_tokens_if_cold": 140000,
                          "requests": 10, "last_miss_at": int(time.time()) - 30,
                          "last_miss_cause": {"causes": ["tools_changed"]}},
         "cost": {"total_cost_usd": 1.23}}
out = gira("barra.py", barra)
verifica("mostra cache fredda", "sconto scaduto" in out, out)
verifica("mostra causa", "app collegate cambiate" in out, out)
out = gira("freetoken.py", {**base, "hook_event_name": "UserPromptSubmit", "prompt": "continua col punto 3"}, "hook")
verifica("blocca a cache fredda", '"decision": "block"' in out and "sconto" in out, out[:200])
out = gira("freetoken.py", {**base, "hook_event_name": "UserPromptSubmit", "prompt": "continua col punto 3"}, "hook")
verifica("al secondo invio passa (con avviso soglia)", "block" not in out and "70%" in out, out[:300])

print("Ripartenza pulita misurata")
out = gira("freetoken.py", {"session_id": "prova2", "cwd": str(TMP), "hook_event_name": "SessionStart",
                        "source": "clear"}, "hook")
verifica("registra il risparmio", "Ripartenza pulita" in out, out[:200])

print("Grazie costoso")
barra["prompt_cache"]["expires_at"] = int(time.time()) + 200
gira("barra.py", {**barra, "session_id": "prova3"})
out = gira("freetoken.py", {**base, "session_id": "prova3", "hook_event_name": "UserPromptSubmit",
                        "prompt": "grazie!"}, "hook")
verifica("avvisa sul grazie", "grazie" in out.lower() and "block" not in out, out[:300])

print("Lettura di file enorme")
grande = TMP / "grande.py"
grande.write_text("\n".join(f"def funzione_{i}(x):\n    return x * {i}  # commento lungo per pesare" for i in range(3000)))
pre = {**base, "hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": str(grande)}}
out = gira("freetoken.py", pre, "hook")
verifica("nega la lettura intera", '"permissionDecision": "deny"' in out, out[:200])
out = gira("freetoken.py", pre, "hook")
verifica("al secondo tentativo passa", "deny" not in out, out[:200])
out = gira("freetoken.py", {**pre, "tool_input": {"file_path": str(grande), "offset": 1, "limit": 200}}, "hook")
verifica("con offset e limit passa muto", out == "", out)
nm = TMP / "node_modules" / "x" / "index.js"
nm.parent.mkdir(parents=True)
nm.write_text("x")
out = gira("freetoken.py", {**pre, "tool_input": {"file_path": str(nm)}}, "hook")
verifica("nega node_modules", "deny" in out, out[:200])

print("Uscita pesante")
out = gira("freetoken.py", {**base, "hook_event_name": "PostToolUse", "tool_name": "mcp__Meta_ADS__x",
                        "tool_response": {"dati": "x" * 80000}}, "hook")
verifica("avvisa uscita pesante", "connettore" in out, out[:200])

print("Regole sempre attive all'avvio")
out = gira("freetoken.py", {"session_id": "prova9", "cwd": str(TMP), "hook_event_name": "SessionStart",
                           "source": "startup"}, "hook")
verifica("mette le regole nel contesto", '"additionalContext"' in out and "FreeToken è attivo" in out, out[:200])

print("Consiglio del modello, in euro")
m = {"cwd": str(TMP), "hook_event_name": "UserPromptSubmit"}
out = gira("freetoken.py", {**m, "session_id": "mod1", "model": "claude-opus-5-5",
                           "prompt": "riscrivi questa mail in modo più formale"}, "hook")
verifica("Opus su una mail: suggerisce Sonnet", "/model sonnet" in out and "€" in out, out[:300])
out = gira("freetoken.py", {**m, "session_id": "mod1", "model": "claude-opus-5-5", "prompt": "ora traducila"}, "hook")
verifica("un solo consiglio per sessione", out == "", out[:200])
out = gira("freetoken.py", {**m, "session_id": "mod2", "model": {"id": "claude-sonnet-5-5"},
                           "prompt": "progetta l'architettura del modulo fatture su più file"}, "hook")
verifica("Sonnet su un lavoro difficile: suggerisce Opus", "/model opus" in out and "€" in out, out[:300])
for testo in ("non funziona ancora", "stesso errore, riprova"):
    out = gira("freetoken.py", {**m, "session_id": "mod3", "model": "claude-haiku-5-5", "prompt": testo}, "hook")
verifica("due tentativi falliti: suggerisce di salire", "/model sonnet" in out, out[:300])
out = gira("freetoken.py", {**m, "session_id": "mod4", "model": "claude-sonnet-5-5",
                           "prompt": "riassumi questo paragrafo"}, "hook")
verifica("Sonnet su un riassunto: nessun avviso", out == "", out[:200])
r = subprocess.run([sys.executable, str(RADICE / "freetoken.py"), "modello"], capture_output=True, text=True, env=ENV)
verifica("comando modello in euro", "Claude Opus → Claude Sonnet" in r.stdout and "€" in r.stdout, r.stderr)

print("Fine sessione e conto")
gira("freetoken.py", {**base, "hook_event_name": "SessionEnd"}, "hook")
r = subprocess.run([sys.executable, str(RADICE / "freetoken.py"), "conto"], capture_output=True, text=True, env=ENV)
print(r.stdout)
verifica("il conto ha un totale in euro", "TOTALE" in r.stdout and "€" in r.stdout and " $" not in r.stdout)
r = subprocess.run([sys.executable, str(RADICE / "freetoken.py"), "pagella", str(TMP)], capture_output=True, text=True, env=ENV)
verifica("pagella vede node_modules", "node_modules" in r.stdout, r.stdout)
r = subprocess.run([sys.executable, str(RADICE / "freetoken.py"), "audit"], capture_output=True, text=True, env=ENV)
verifica("audit gira", "audit" in r.stdout, r.stderr)

print(f"\n{ok} superati, {fail} falliti")
sys.exit(1 if fail else 0)
