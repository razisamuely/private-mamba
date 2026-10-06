#!/bin/bash
### One-time StarCraft II 4.10 + SMAC maps install for SMAC runs (CPU-only job; downloads ~4 GB).
### Submit from the repo root:  sbatch tools/cluster/setup_sc2_job.sh
### Afterwards jobs need:       export SC2PATH=$HOME/camamba/StarCraftII
#SBATCH --partition cpu
#SBATCH --time 0-03:00:00
#SBATCH --job-name camamba_sc2_setup
#SBATCH --output camamba_sc2_setup-id-%J.out
#SBATCH --mem=8G

set -euo pipefail
DEST="${DEST:-$HOME/camamba}"
SC2_ZIP_URL="http://blzdistsc2-a.akamaihd.net/Linux/SC2.4.10.zip"
MAPS_ZIP_URL="https://github.com/oxwhirl/smac/releases/download/v0.1-beta1/SMAC_Maps.zip"

mkdir -p "$DEST"
cd "$DEST"
if [ ! -x "$DEST/StarCraftII/Versions/Base75689/SC2_x64" ]; then
    wget -q -O SC2.4.10.zip "$SC2_ZIP_URL"
    # The archive password is Blizzard's published EULA acceptance phrase.
    unzip -q -P iagreetotheeula SC2.4.10.zip
    rm -f SC2.4.10.zip
fi
mkdir -p "$DEST/StarCraftII/Maps"
if [ ! -d "$DEST/StarCraftII/Maps/SMAC_Maps" ]; then
    wget -q -O SMAC_Maps.zip "$MAPS_ZIP_URL"
    unzip -q -o SMAC_Maps.zip -d "$DEST/StarCraftII/Maps"
    rm -f SMAC_Maps.zip
fi
ls "$DEST/StarCraftII/Versions"
ls "$DEST/StarCraftII/Maps/SMAC_Maps" | head -40
test -f "$DEST/StarCraftII/Maps/SMAC_Maps/8m.SC2Map"
echo "SC2_SETUP_OK"
