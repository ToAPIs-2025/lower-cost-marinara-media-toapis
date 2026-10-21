param([Parameter(Mandatory=$true)][string]$Target)
$ErrorActionPreference='Stop'
if (-not [IO.Path]::IsPathRooted($Target)) { throw 'Use an absolute target path, preferably on a drive with room for dependencies.' }
if (Test-Path -LiteralPath $Target) { throw 'Target already exists. Choose a new directory; existing installations are never reset.' }
foreach($name in @('git','node','pnpm')) { if(-not (Get-Command $name -ErrorAction SilentlyContinue)) { throw ('Install '+$name+' first; see README.') } }
$nodeMajor=[int]((& node -p 'process.versions.node.split(".")[0]') | Select-Object -Last 1)
if($nodeMajor -lt 24 -or $nodeMajor -ge 27) { throw 'Use Node 24, 25 or 26.' }
if((& pnpm --version).Trim() -ne '10.34.5') { throw 'Use the pinned pnpm 10.34.5 for this recipe.' }
$patch=Join-Path $PSScriptRoot 'toapis-media.patch'
if(-not (Test-Path -LiteralPath $patch)) { throw 'Download the complete guide repository, including native/toapis-media.patch.' }
function Run-Checked([scriptblock]$Action) { & $Action; if($LASTEXITCODE -ne 0) { throw ('Command failed with exit code '+$LASTEXITCODE) } }
Run-Checked { git init $Target }
Push-Location $Target
try {
  Run-Checked { git remote add origin https://github.com/Pasta-Devs/Marinara-Engine.git }
  Run-Checked { git sparse-checkout init --cone }
  Run-Checked { git sparse-checkout set packages scripts patches e2e .agents/skills .github/agents docs/media docs/connections }
  Run-Checked { git fetch --depth=1 origin d0e481913f9a0e3bab0e9b767009500d0577f98a }
  Run-Checked { git checkout --detach FETCH_HEAD }
  Run-Checked { git apply --check $patch }
  Run-Checked { git apply $patch }
  $env:TEMP=Join-Path $Target '.tmp'; $env:TMP=$env:TEMP
  New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
  $store=Join-Path $Target '.pnpm-store'
  Run-Checked { pnpm install --frozen-lockfile --store-dir $store }
  Run-Checked { pnpm check }
  Write-Host 'Built a separate community adapter. See native/README for isolated launch and connection configuration.'
} finally { Pop-Location }
