#!/usr/bin/env python3
"""
Prepara la versione di FreeToken per le directory ufficiali di Claude e OpenAI.

La directory di Claude accetta script e controlli automatici solo da organizzazioni verificate,
e quella di OpenAI non accetta plugin con hook. Questa versione contiene solo testo:
la skill che si attiva da sola, i comandi, il calcolatore, le immagini.
La versione completa con il pilota automatico resta in plugins/freetoken.

Uso:  python3 strumenti/prepara-directory.py
"""
import json, shutil, zipfile
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
FONTE = RADICE / "plugins" / "freetoken"
DEST = RADICE / "directory" / "freetoken"

if DEST.exists():
    shutil.rmtree(DEST)
(DEST / ".claude-plugin").mkdir(parents=True)
for cartella in ("skills", "commands", "assets"):
    shutil.copytree(FONTE / cartella, DEST / cartella)
shutil.copy2(FONTE / "LICENSE", DEST / "LICENSE")
# Le directory accettano solo testo, Markdown, JSON, YAML e immagini: il calcolatore resta online
(DEST / "skills" / "freetoken" / "calcolatore.html").unlink()
skill = DEST / "skills" / "freetoken" / "SKILL.md"
testo = skill.read_text(encoding="utf-8")
import re
testo = re.sub(r'- "calcolatore": consegna[^\n]*', '- "calcolatore": dai il link al calcolatore gratuito di FreeToken, che mostra quanto pesa un testo in chat e se conviene ripartire: https://giandoms.github.io/FreeToken/strumenti/calcolatore.html', testo)
skill.write_text(testo, encoding="utf-8")

claude = json.loads((FONTE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
claude.pop("hooks", None)
claude["description"] = ("Ti avvisa quando la chat con l'IA consuma troppo e ti dice cosa fare: semaforo, "
                         "Passaggio per ripartire leggero, calcolatore. Gratis, in italiano.")
(DEST / ".claude-plugin" / "plugin.json").write_text(json.dumps(claude, indent=2, ensure_ascii=False), encoding="utf-8")
shutil.copy2(FONTE / "plugin.json", DEST / "plugin.json")
(DEST / ".codex-plugin").mkdir(exist_ok=True)
shutil.copy2(FONTE / ".codex-plugin" / "plugin.json", DEST / ".codex-plugin" / "plugin.json")

readme = (FONTE / "README.md").read_text(encoding="utf-8")
inizio = readme.index("## Cosa esegue e cosa tocca (trasparenza)")
fine = readme.index("## Privacy")
readme = readme[:inizio] + """## Cosa contiene (trasparenza)
Questa versione contiene solo testo: la skill FreeToken, i comandi `/nota`, `/riparti` e `/asciutto`, il link al calcolatore online e le immagini. Non esegue codice, non fa chiamate di rete e non salva niente sul tuo computer.

La versione completa per Claude Code, con il pilota automatico che legge i consumi veri e ferma gli sprechi prima che partano, si installa dal progetto GitHub: https://github.com/Giandoms/FreeToken

""" + readme[fine:]
readme = readme.replace("Tutto quello che salva resta sul tuo computer, in `~/.freetoken/`, e puoi cancellarlo quando vuoi.",
                        "Questa versione non salva niente.")
(DEST / "README.md").write_text(readme, encoding="utf-8")

zip_openai = RADICE / "scarica" / "freetoken-openai.zip"
zip_openai.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(zip_openai, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(DEST.rglob("*")):
        rel = f.relative_to(DEST)
        if f.is_file() and not str(rel).startswith(".claude-plugin") and not str(rel).startswith("commands"):
            z.write(f, rel)
print("Pronta:", DEST)
print("Pacchetto OpenAI:", zip_openai)
