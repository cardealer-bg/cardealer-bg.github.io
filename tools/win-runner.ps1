# CAR DEALER liste: instalira GitHub "runner" na ovaj Windows racunar, da dugme "Azuriraj liste"
# i automatska azuriranja rade preko ovog racunara (kucni internet), ne preko GitHub servera.
# Pokretanje: otvorite PowerShell i nalepite:
#   irm https://cardealer-bg.github.io/tools/win-runner.ps1 | iex
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$DIR  = Join-Path $env:USERPROFILE 'cardealer-runner'
$REPO = 'https://github.com/cardealer-bg/cardealer-bg.github.io'
function Say($t) { Write-Host ''; Write-Host $t -ForegroundColor Cyan }
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') }
function Has-Python { try { & python -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" 2>$null; return ($LASTEXITCODE -eq 0) } catch { return $false } }

& {
Say '1/5  Provera osnovnih alata (Git, Python)...'
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host 'Instaliram Git (par minuta)...'
  winget install -e --id Git.Git --silent --accept-package-agreements --accept-source-agreements | Out-Null
  Refresh-Path
}
if (-not (Has-Python)) {
  Write-Host 'Instaliram Python (par minuta)...'
  winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Null
  Refresh-Path
}
if (-not (Get-Command git -ErrorAction SilentlyContinue) -or -not (Has-Python)) {
  Say 'Git ili Python jos nisu dostupni. Zatvorite PowerShell, otvorite ga ponovo i pokrenite istu komandu.'
  return
}
git --version; python --version
$gitBash = Join-Path (Split-Path (Split-Path (Get-Command git).Source)) 'bin\bash.exe'
if (-not (Test-Path $gitBash)) { $gitBash = 'C:\Program Files\Git\bin\bash.exe' }
if (-not (Test-Path $gitBash)) { Say 'Nije pronadjen Git Bash (deo Git-a). Javite Claude-u.'; return }

Say '2/5  Python alati za citanje oglasa i PDF (par minuta)...'
New-Item -ItemType Directory -Force -Path $DIR | Out-Null
$PY = Join-Path $DIR 'venv\Scripts\python.exe'
if (-not (Test-Path $PY)) { python -m venv (Join-Path $DIR 'venv') }
& $PY -m pip install -q --upgrade pip
& $PY -m pip install -q playwright pypdf tzdata
& $PY -m playwright install chromium

Say '3/5  Probno citanje oglasa sa Polovnih automobila...'
$T = Join-Path $env:TEMP ('cardealer-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Force -Path $T | Out-Null
Invoke-WebRequest "$REPO/archive/refs/heads/main.zip" -OutFile "$T\main.zip" -UseBasicParsing
Expand-Archive "$T\main.zip" -DestinationPath $T -Force
$tools = Join-Path $T 'cardealer-bg.github.io-main\tools'
$env:PYTHONUTF8 = '1'
try { $ErrorActionPreference = 'Continue'; & $PY "$tools\scrape.py" "$T\proba" *> $null } catch {} finally { $ErrorActionPreference = 'Stop' }
$n = 0
try { $n = (Get-Content "$T\proba\list.json" -Raw -Encoding UTF8 | ConvertFrom-Json).ads.Count } catch {}
if ($n -gt 0) {
  Write-Host "Procitano oglasa: $n"
  Say 'OK - Polovni automobili se citaju sa ovog racunara.'
} else {
  Say 'PAZNJA: oglasi se ne mogu procitati sa ovog racunara. Instalacija staje - javite Claude-u.'
  return
}

Say '4/5  Povezivanje sa GitHub-om'
Write-Host 'Na GitHubu (nalog cardealer-bg) otvorite:'
Write-Host "  $REPO/settings/actions/runners/new?arch=x64&os=win"
Write-Host "U delu 'Configure' kopirajte SAMO kod iza  --token  (niz velikih slova i brojeva)."
$TOKEN = (Read-Host 'Nalepite kod ovde i pritisnite Enter').Trim()
if ($TOKEN -match '--token\s+(\S+)') { $TOKEN = $Matches[1] }
if (-not $TOKEN) { Say 'Kod nije unet.'; return }

Set-Location $DIR
if (-not (Test-Path (Join-Path $DIR 'config.cmd'))) {
  $V = (Invoke-RestMethod 'https://api.github.com/repos/actions/runner/releases/latest').tag_name.TrimStart('v')
  Invoke-WebRequest "https://github.com/actions/runner/releases/download/v$V/actions-runner-win-x64-$V.zip" -OutFile runner.zip -UseBasicParsing
  Expand-Archive runner.zip -DestinationPath $DIR -Force
  Remove-Item runner.zip
}
Get-Process Runner.Listener -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
& .\config.cmd --unattended --replace --url $REPO --token $TOKEN --name $env:COMPUTERNAME --labels cardealer
if ($LASTEXITCODE -ne 0) { Say 'Povezivanje nije uspelo. Uzmite novi kod sa iste GitHub stranice i pokrenite komandu ponovo.'; return }

Say '5/5  Pokretanje u pozadini (i posle restarta racunara)...'
# Git Bash mora biti na PATH-u za korake azuriranja (shell: bash)
$gitBin = Split-Path $gitBash
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
if ($userPath -notlike "*$gitBin*") { [Environment]::SetEnvironmentVariable('Path', ($userPath.TrimEnd(';') + ';' + $gitBin), 'User') }
$run = Join-Path $DIR 'run.cmd'
$vbs = Join-Path ([Environment]::GetFolderPath('Startup')) 'CAR DEALER runner.vbs'
"CreateObject(""WScript.Shell"").Run """"""$run"""""", 0, False" | Set-Content -Path $vbs -Encoding ASCII
Refresh-Path
Start-Process wscript.exe -ArgumentList "`"$vbs`""
Start-Sleep 5
if (Get-Process Runner.Listener -ErrorAction SilentlyContinue) {
  Say "GOTOVO. Dugme 'Azuriraj liste' sada radi i preko ovog racunara (mora biti ukljucen i prijavljen)."
} else {
  Say 'Runner nije pokrenut. Javite Claude-u.'
}
}
