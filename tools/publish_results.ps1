# Run after a verified Plant Simulation execution, from the cloned repository.
param(
  [Parameter(Mandatory=$true)]
  [ValidatePattern('^[A-Za-z0-9]{6}$')]
  [string]$Neptun,
  [string]$OriginalAssignmentPdf = ''
)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repo
$Neptun=$Neptun.ToUpperInvariant()
$local=Join-Path $repo 'output'
$spp=Join-Path $local "$Neptun.spp"
$result=Join-Path $local 'simulation_result.json'
$manifest=Join-Path $local 'evidence_manifest.json'
$validation=Join-Path $local 'config_validation.json'
foreach ($path in @($spp,$result,$manifest,$validation)) {
  if (!(Test-Path $path)) { throw "Hiányzó élő Siemens-fájl: $path" }
}
$r=Get-Content $result -Raw -Encoding UTF8 | ConvertFrom-Json
$e=Get-Content $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
if (!$r.complete -or !$r.pass_quantity_and_quality_tolerance -or $r.processed -ne 10000) {
  throw 'Nem sikeres a 10 000 darabos Siemens-futtatás.'
}
if ($e.synthetic_images -ne $false -or @($e.screenshots.PSObject.Properties).Count -ne 5) {
  throw 'Hiányzó öt valódi Siemens-screenshot.'
}
$checksum=(Get-FileHash $spp -Algorithm SHA256).Hash
if ($checksum -ne $e.spp_sha256) { throw 'SPP SHA256-eltérés.' }
$target=Join-Path $repo "submissions\$Neptun"
New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item $spp (Join-Path $target "$Neptun.spp") -Force
Copy-Item $result (Join-Path $target 'simulation_result.json') -Force
Copy-Item $validation (Join-Path $target 'config_validation.json') -Force
Copy-Item $manifest (Join-Path $target 'evidence_manifest.json') -Force
$shots=Join-Path $target 'screenshots'
New-Item -ItemType Directory -Path $shots -Force | Out-Null
Copy-Item (Join-Path $local 'screenshots\*.png') $shots -Force
if ($OriginalAssignmentPdf) {
  if (!(Test-Path $OriginalAssignmentPdf)) { throw 'Az eredeti feladatlap PDF hiányzik.' }
  $original=Join-Path $repo 'docs\assignment\PS_beadando_original.pdf'
  New-Item -ItemType Directory -Path (Split-Path $original) -Force | Out-Null
  Copy-Item $OriginalAssignmentPdf $original -Force
  git add -f $original
}
git add -f $target
git config user.name 'SzE Plant Simulation export'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Write-Host 'Nem történt változás.'; exit 0 }
git commit -m "evidence: verified $Neptun Plant Simulation model and screenshots"
if ($LASTEXITCODE -ne 0) { throw 'Git commit hiba.' }
git push origin HEAD:main
if ($LASTEXITCODE -ne 0) { throw 'Git push hiba. A commit helyben megmaradt.' }
Write-Host "Valódi Siemens-eredmények feltöltve: submissions/$Neptun/"
