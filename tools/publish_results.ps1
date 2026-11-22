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
if (!(Test-Path (Join-Path $repo '.git'))) {
  throw 'GitHub feltöltéshez git clone szükséges. A Download ZIP nem tartalmaz .git mappát. A kész output mappát másold át egy klónozott repóba, majd ott futtasd újra ezt a szkriptet.'
}
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
$v=Get-Content $validation -Raw -Encoding UTF8 | ConvertFrom-Json
if (!$v.siemens_live_verification -or @($v.errors).Count -gt 0) {
  throw 'A Siemens modellparaméterek ellenőrzése sikertelen.'
}
if ($r.source_output_count -ne 10000 -or $r.packed -ne $r.good -or
    ($r.loaded_at_station_1 + $r.loaded_at_station_2) -ne $r.good -or
    !$r.lot_time_at_least_pack_time) {
  throw 'Az input, az összeszerelés vagy a rakodás mért számlálói nem egyeznek.'
}
if (!$r.complete -or !$r.pass_quantity_and_quality_tolerance -or $r.processed -ne 10000) {
  throw 'Nem sikeres a 10 000 darabos Siemens-futtatás.'
}
if ($e.synthetic_images -ne $false -or @($e.screenshots.PSObject.Properties).Count -ne 5) {
  throw 'Hiányzó öt valódi Siemens-screenshot.'
}
$checksum=(Get-FileHash $spp -Algorithm SHA256).Hash
if ($checksum -ne $e.spp_sha256) { throw 'SPP SHA256-eltérés.' }
$expectedShots=@(
  '01_fomodell.png',
  '02_minosegellenorzes.png',
  '03_csomagolas.png',
  '04_szallitas_elokeszites.png',
  '05_allomasstatisztika.png'
)
$pngSignature=[byte[]](137,80,78,71,13,10,26,10)
foreach ($name in $expectedShots) {
  $entry=$e.screenshots.PSObject.Properties[$name]
  if ($null -eq $entry) { throw "Hiányzik a képernyőkép manifest-bejegyzése: $name" }
  $path=Join-Path $local ("screenshots\" + $name)
  if (!(Test-Path $path)) { throw "Hiányzik a tényleges Siemens PNG: $name" }
  $bytes=[System.IO.File]::ReadAllBytes($path)
  if ($bytes.Length -lt 1000 -or $bytes.Length -ne $entry.Value.bytes) {
    throw "Eltérő méretű Siemens PNG: $name"
  }
  for ($i=0; $i -lt 8; $i++) {
    if ($bytes[$i] -ne $pngSignature[$i]) { throw "Hibás PNG fejléc: $name" }
  }
  $actual=(Get-FileHash $path -Algorithm SHA256).Hash
  if ($actual -ne $entry.Value.sha256) {
    throw "Eltérő vagy módosított Siemens-képernyőkép: $name"
  }
}
$target=Join-Path $repo "submissions\$Neptun"
New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item $spp (Join-Path $target "$Neptun.spp") -Force
Copy-Item $result (Join-Path $target 'simulation_result.json') -Force
Copy-Item $validation (Join-Path $target 'config_validation.json') -Force
Copy-Item $manifest (Join-Path $target 'evidence_manifest.json') -Force
$report=Join-Path $local 'Siemens_meresi_jegyzokonyv.pdf'
if (!(Test-Path $report)) { throw 'A valós mérési jegyzőkönyv hiányzik.' }
Copy-Item $report (Join-Path $target 'Siemens_meresi_jegyzokonyv.pdf') -Force
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
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) { Write-Host 'Nem történt változás.'; exit 0 }
git commit -m "evidence: verified $Neptun Plant Simulation model and screenshots"
if ($LASTEXITCODE -ne 0) { throw 'Git commit hiba.' }
git push origin HEAD:main
if ($LASTEXITCODE -ne 0) { throw 'Git push hiba. A commit helyben megmaradt.' }
Write-Host "Valódi Siemens-eredmények feltöltve: submissions/$Neptun/"
