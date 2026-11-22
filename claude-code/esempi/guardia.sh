#!/usr/bin/env bash
# Guardia a costo zero per i lavori automatici.
#
# Il problema: un agente programmato che si sveglia ogni ora, legge tutto,
# scopre che non c'è niente da fare e intanto ha bruciato migliaia di token.
# La soluzione: prima controlla con un comando che non costa niente,
# e sveglia l'IA solo se c'è davvero lavoro.
#
# Uso (es. in cron):  ./guardia.sh "nome-lavoro" "comando-di-controllo" "prompt per claude"
# Il comando di controllo deve stampare qualcosa SOLO se c'è lavoro nuovo.
#
# Esempi di comandi di controllo:
#   find ~/Trascrizioni -name '*.txt' -newer ~/.freetoken/guardia/report-call.stamp
#   gh pr list --search "review-requested:@me" --json number --jq '.[].number'
#   ls ~/Scontrini/nuovi/*.jpg 2>/dev/null

set -euo pipefail
NOME="$1"; CONTROLLO="$2"; PROMPT="$3"
DIR="$HOME/.freetoken/guardia"; mkdir -p "$DIR"
STAMP="$DIR/$NOME.stamp"; [ -f "$STAMP" ] || touch -d '1970-01-01' "$STAMP" 2>/dev/null || touch "$STAMP"
LOG="$DIR/$NOME.log"

NOVITA=$(bash -c "$CONTROLLO" 2>/dev/null || true)
if [ -z "$NOVITA" ]; then
  echo "$(date '+%F %T') saltato: niente di nuovo (0 token)" >> "$LOG"
  exit 0
fi

echo "$(date '+%F %T') eseguito: $(echo "$NOVITA" | wc -l | tr -d ' ') novità" >> "$LOG"
# Passa all'IA solo l'elenco delle novità, non tutto l'archivio.
claude -p "$PROMPT

Lavora SOLO su queste novità:
$NOVITA"
touch "$STAMP"
