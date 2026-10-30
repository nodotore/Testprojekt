#!/bin/sh
# Schreibt alle Bilder in tv-frame/ nach images.json (Aufruf: sh tv-frame/make-list.sh)
cd "$(dirname "$0")" || exit 1
ls | grep -iE '\.(jpe?g|png|webp)$' | sort | awk 'BEGIN{printf "["} {printf "%s\"%s\"", (NR>1?",":""), $0} END{print "]"}' > images.json
cat images.json
