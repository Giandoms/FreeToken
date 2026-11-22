#!/usr/bin/env python3
"""
Installa FreeToken in Claude Code senza passare dai plugin.

  python3 install.py            installa agganci, barra di stato e comandi /nota /riparti /asciutto
  python3 install.py --solo-barra  solo la barra di stato (se FreeToken è già installato come plugin)
  python3 install.py --rimuovi  toglie tutto e rimette la tua barra di stato di prima

Prima di toccare ~/.claude/settings.json ne fa una copia di sicurezza.
"""
import json
import os
import shutil
import sys
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent.parent / "plugins" / "freetoken"
CLAUDE = Path.home() / ".claude"
IMPOSTAZIONI = CLAUDE / "settings.json"
DATI = Path(os.environ.get("FREETOKEN_HOME", "~/.freetoken")).expanduser()
PY = "python" if os.name == "nt" else "python3"
CMD = f'{PY} "{(QUI / "scripts" / "freetoken.py").as_posix()}" hook'
BARRA = f'{PY} "{(QUI / "scripts" / "barra.py").as_posix()}"'
EVENTI = {"UserPromptSubmit": None, "PreToolUse": "Read|Bash", "PostToolUse": None,
          "SessionStart": None, "PreCompact": None, "PreModelSwitch": None, "SessionEnd": None}


def nostro(gruppo):
    return any("freetoken.py" in (h.get("command") or "") for h in gruppo.get("hooks", []))


def carica():
    try:
        return json.loads(IMPOSTAZIONI.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def salva(s):
    CLAUDE.mkdir(parents=True, exist_ok=True)
    if IMPOSTAZIONI.exists():
        copia = IMPOSTAZIONI.with_name(f"settings.json.prima-di-freetoken-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(IMPOSTAZIONI, copia)
        print(f"Copia di sicurezza: {copia}")
    IMPOSTAZIONI.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


def config_utente():
    f = DATI / "config.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return {}


def salva_config(c):
    DATI.mkdir(parents=True, exist_ok=True)
    (DATI / "config.json").write_text(json.dumps(c, indent=2, ensure_ascii=False), encoding="utf-8")


def installa(solo_barra=False):
    s = carica()
    hooks = s.setdefault("hooks", {})
    for ev, matcher in ({} if solo_barra else EVENTI).items():
        gruppi = [g for g in hooks.get(ev, []) if not nostro(g)]
        g = {"hooks": [{"type": "command", "command": CMD, "timeout": 10}]}
        if matcher:
            g["matcher"] = matcher
        gruppi.append(g)
        hooks[ev] = gruppi

    c = config_utente()
    vecchia = (s.get("statusLine") or {}).get("command", "")
    if vecchia and "barra.py" not in vecchia:
        c["statusline_precedente"] = vecchia
        print("La tua barra di stato di prima resta visibile, sopra quella di FreeToken.")
    c.setdefault("prezzo_input_per_milione_usd", 5.0)
    salva_config(c)
    s["statusLine"] = {"type": "command", "command": BARRA, "refreshInterval": 5}

    if not solo_barra:
        comandi = CLAUDE / "commands"
        comandi.mkdir(parents=True, exist_ok=True)
        for f in (QUI / "commands").glob("*.md"):
            shutil.copy2(f, comandi / f.name)

    calc = QUI / "skills" / "freetoken" / "calcolatore.html"
    if calc.exists():
        DATI.mkdir(parents=True, exist_ok=True)
        shutil.copy2(calc, DATI / "calcolatore.html")

    salva(s)
    print("\n🪙 FreeToken installato.")
    print("   Riavvia Claude Code. Comandi nuovi: /nota  /riparti  /asciutto")
    print(f"   Il tuo conto:   {PY} \"{QUI / 'scripts' / 'freetoken.py'}\" conto")
    print(f"   Calcolatore:    {PY} \"{QUI / 'scripts' / 'freetoken.py'}\" calcolatore  (o apri {DATI / 'calcolatore.html'})")
    print(f"   Lavori a vuoto: {PY} \"{QUI / 'scripts' / 'freetoken.py'}\" audit")
    print(f"   Prezzi e soglie: {DATI / 'config.json'}\n")


def rimuovi():
    s = carica()
    for ev in list((s.get("hooks") or {}).keys()):
        s["hooks"][ev] = [g for g in s["hooks"][ev] if not nostro(g)]
        if not s["hooks"][ev]:
            del s["hooks"][ev]
    c = config_utente()
    if "barra.py" in (s.get("statusLine") or {}).get("command", ""):
        if c.get("statusline_precedente"):
            s["statusLine"] = {"type": "command", "command": c["statusline_precedente"]}
        else:
            s.pop("statusLine", None)
    for nome in ("nota.md", "riparti.md", "asciutto.md"):
        try:
            (CLAUDE / "commands" / nome).unlink()
        except FileNotFoundError:
            pass
    salva(s)
    print(f"FreeToken rimosso. I tuoi dati restano in {DATI} (cancellali pure se vuoi).")


if __name__ == "__main__":
    rimuovi() if "--rimuovi" in sys.argv else installa(solo_barra="--solo-barra" in sys.argv)
