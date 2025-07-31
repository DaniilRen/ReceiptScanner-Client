#!/bin/sh

# Check if the venv already exists
VENV=".venv"
if [ -d $VENV ]; then
  echo "[!] '$VENV' directory already exists."
else
  python3 -m venv $VENV
  echo "[+] Created new python venv"

  source $VENV/bin/activate
  echo "[+] Venv activated"
fi

cd app

pip install -r requirements.txt
echo "[+] Python dependencies intalled"

echo "Starting building process for linux..."
flet build linux
echo "[+] Installation complete!"