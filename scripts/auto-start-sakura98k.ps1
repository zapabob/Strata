# Auto-start the Sakura Inkling-2-Mini 98K server for Hermes Agent at logon/power-on.
# Registered as a Windows Scheduled Task (see _docs/... log). Runs the standard
# launcher with the verified vramfix config; skips if the server is already up.
$ErrorActionPreference = 'Continue'
$log = 'H:/Strata/evidence/sakura98k-autostart.log'
function L($m){ "$([DateTime]::Now.ToString('o')) $m" | Out-File $log -Append -Encoding utf8 }
$repo = 'C:/Users/downl/Documents/ChatGPT/Strata'
$launcher = Join-Path $repo 'scripts/start-sakura-inkling2-hermes.ps1'
$model = 'H:/Strata/models/Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf'
$port = 8092

L "AUTOSTART begin"

# The model lives on H:; give a freshly booted machine time to bring that disk online.
for ($i = 0; $i -lt 12 -and -not (Test-Path $model); $i++) { Start-Sleep -Seconds 5 }
if (-not (Test-Path $model)) { L "MODEL_MISSING $model"; exit 1 }
L "MODEL_READY"

# Already serving? Do not start a second copy (port 8092 is a single listener).
$existing = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($existing) { L "ALREADY_RUNNING pid=$($existing.OwningProcess); skip"; exit 0 }

if (-not $env:STRATA_API_KEY) {
  $env:STRATA_API_KEY = [Environment]::GetEnvironmentVariable('STRATA_API_KEY','User')
}
if (-not $env:STRATA_API_KEY) { L "API_KEY_MISSING"; exit 1 }

L "LAUNCH launcher=$launcher context=98k-vramfix"
& powershell -NoProfile -ExecutionPolicy Bypass -File $launcher -Context 98k-vramfix -Port $port `
  -PpStageMb 64 -VramReserveMb 3328 -Tier2Floor 0 2>&1 | Out-File $log -Append -Encoding utf8
L "LAUNCH_EXIT=$LASTEXITCODE AUTOSTART_END"
