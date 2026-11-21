#!/bin/bash
# CAR DEALER liste: install the GitHub "runner" on this Mac, so the "Ažuriraj liste" button
# and the automatic morning/afternoon updates run here (home internet), not on GitHub servers.
# Run in Terminal:  curl -fsSL https://cardealer-bg.github.io/tools/mac-runner.sh | bash
set -e
DIR="$HOME/cardealer-runner"
REPO="https://github.com/cardealer-bg/cardealer-bg.github.io"
say() { printf "\n\033[1m%s\033[0m\n" "$1"; }

say "1/5  Provera osnovnih alata (git, python3)…"
if ! xcode-select -p >/dev/null 2>&1; then
  xcode-select --install || true
  say "Otvorio se prozor 'Command Line Tools' – kliknite Install, sačekajte da završi, pa ponovo pokrenite istu komandu."
  exit 1
fi
git --version && python3 --version

say "2/5  Python alati za čitanje oglasa i PDF (par minuta)…"
mkdir -p "$DIR"
[ -x "$DIR/venv/bin/python" ] || python3 -m venv "$DIR/venv"
"$DIR/venv/bin/pip" install -q --upgrade pip
"$DIR/venv/bin/pip" install -q playwright pypdf
"$DIR/venv/bin/python" -m playwright install chromium

say "3/5  Probno čitanje oglasa sa Polovnih automobila…"
T=$(mktemp -d)
curl -fsSL "$REPO/archive/refs/heads/main.tar.gz" | tar -xz -C "$T" --strip-components=1
if "$DIR/venv/bin/python" "$T/tools/scrape.py" "$T/proba" >/dev/null 2>&1 && \
   "$DIR/venv/bin/python" -c "import json,sys;d=json.load(open('$T/proba/list.json'));n=len(d['ads']);print('Pročitano oglasa:',n);sys.exit(0 if n>0 else 1)"; then
  say "OK – Polovni automobili se čitaju sa ovog računara."
else
  say "PAŽNJA: oglasi se ne mogu pročitati ni sa ovog računara. Instalacija staje – javite Claude-u."
  exit 1
fi

say "4/5  Povezivanje sa GitHub-om"
echo "Na GitHubu (nalog cardealer-bg) otvorite:"
echo "  $REPO/settings/actions/runners/new?arch=arm64&os=osx"
echo "U delu 'Configure' kopirajte dugačak kod iza  --token  (počinje sa A...)."
printf "Nalepite kod ovde i pritisnite Enter: "
read -r TOKEN < /dev/tty
[ -n "$TOKEN" ] || { echo "Kod nije unet."; exit 1; }

cd "$DIR"
if [ ! -x ./config.sh ]; then
  V=$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest | "$DIR/venv/bin/python" -c "import json,sys;print(json.load(sys.stdin)['tag_name'].lstrip('v'))")
  curl -fsSL -o runner.tgz "https://github.com/actions/runner/releases/download/v$V/actions-runner-osx-arm64-$V.tar.gz"
  tar xzf runner.tgz && rm runner.tgz
fi
[ -f .runner ] && ./svc.sh stop >/dev/null 2>&1 || true
./config.sh --unattended --replace --url "$REPO" --token "$TOKEN" --name "$(scutil --get ComputerName 2>/dev/null | tr -cd "A-Za-z0-9-" || hostname -s)" --labels "cardealer"

say "5/5  Pokretanje u pozadini (i posle restarta računara)…"
./svc.sh install >/dev/null 2>&1 || true
./svc.sh start
./svc.sh status | tail -3
say "GOTOVO. Dugme 'Ažuriraj liste' sada radi preko ovog Mac-a (Mac mora biti uključen)."
