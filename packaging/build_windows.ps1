param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("window10", "window11")]
    [string]$Target
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot
$Version = (python -c "from sta_lite import __version__; print(__version__)").Trim()
if (-not $Version) { throw "无法读取 STA-Lite 版本号。" }

$ReleaseRoot = Join-Path $ProjectRoot "build\release\$Target"
$PayloadDir = Join-Path $ReleaseRoot "payload"
$OutputDir = Join-Path $ProjectRoot "install_package\$Target"
$WorkDir = Join-Path $ReleaseRoot "pyinstaller-work"
$SpecDir = Join-Path $ReleaseRoot "spec"

if (Test-Path $ReleaseRoot) { Remove-Item -Recurse -Force $ReleaseRoot }
New-Item -ItemType Directory -Force $PayloadDir, $OutputDir, $WorkDir, $SpecDir | Out-Null
Get-ChildItem $OutputDir -File | Where-Object { $_.Name -ne "README.md" } | Remove-Item -Force

$DataArgs = @(
    "--add-data", "sta_lite/gui/static;sta_lite/gui/static",
    "--add-data", "examples;examples",
    "--add-data", "lint;lint",
    "--add-data", "risk_profile;risk_profile",
    "--add-data", "tests;tests",
    "--add-data", "README.md;."
)

python -m PyInstaller --noconfirm --clean --onedir --windowed --name "STA-Lite" `
    --distpath $PayloadDir --workpath (Join-Path $WorkDir "desktop") --specpath $SpecDir `
    @DataArgs "sta-lite-desktop"
if ($LASTEXITCODE -ne 0) { throw "STA-Lite 桌面程序构建失败。" }

python -m PyInstaller --noconfirm --clean --onedir --console --name "sta-lite-cli" `
    --distpath $PayloadDir --workpath (Join-Path $WorkDir "cli") --specpath $SpecDir `
    @DataArgs "sta-lite"
if ($LASTEXITCODE -ne 0) { throw "STA-Lite CLI 构建失败。" }

$CliExe = Join-Path $PayloadDir "sta-lite-cli\sta-lite-cli.exe"
& $CliExe --version
if ($LASTEXITCODE -ne 0) { throw "CLI 版本 smoke test 失败。" }

$ExpectedCases = [int](python -c "from sta_lite.review.case_registry import CASE_REGISTRY; print(len(CASE_REGISTRY))")
$GuiExe = Join-Path $PayloadDir "STA-Lite\STA-Lite.exe"
$SmokeWorkspace = Join-Path $ReleaseRoot "smoke-workspace"
$GuiProcess = Start-Process -FilePath $GuiExe -ArgumentList @("--no-browser", "--port", "18765", "--workspace", $SmokeWorkspace) -PassThru
try {
    $Response = $null
    for ($Attempt = 0; $Attempt -lt 40; $Attempt++) {
        Start-Sleep -Milliseconds 250
        try {
            $Response = Invoke-RestMethod -Uri "http://127.0.0.1:18765/api/case_coverage" -TimeoutSec 2
            break
        } catch {
            if ($GuiProcess.HasExited) { throw "GUI 在 smoke test 中提前退出。" }
        }
    }
    if ($null -eq $Response) { throw "GUI HTTP smoke test 超时。" }
    if ([int]$Response.summary.total -ne $ExpectedCases) {
        throw "Case Coverage smoke test 失败：期望 $ExpectedCases，实际 $($Response.summary.total)。"
    }
} finally {
    if (-not $GuiProcess.HasExited) { Stop-Process -Id $GuiProcess.Id -Force }
}

$DependencyText = @"
STA-Lite $Version / $Target
运行时依赖：无须另装 Python、Yosys 或 OpenSTA。
安装器内含：CPython 3.10 x64 运行时、PyInstaller 6.21.0 冻结依赖、STA-Lite RTL Review 资源。
可选 Backend Analysis：仅在用户主动使用该页面时需要另装 Yosys/OpenSTA 和 Liberty。
构建平台：GitHub Actions windows-2022；Windows 10/11 真机认证状态见 README 和发布说明。
"@
Set-Content -Path (Join-Path $PayloadDir "DEPENDENCIES.txt") -Value $DependencyText -Encoding UTF8
Copy-Item "THIRD_PARTY_NOTICES.md" $PayloadDir

$Makensis = (Get-Command makensis.exe -ErrorAction SilentlyContinue).Source
if (-not $Makensis) { $Makensis = "C:\Program Files (x86)\NSIS\makensis.exe" }
if (-not (Test-Path $Makensis)) { throw "未找到 makensis.exe，请先安装 NSIS。" }
& $Makensis "/DAPP_VERSION=$Version" "/DTARGET=$Target" "/DPAYLOAD_DIR=$PayloadDir" "/DOUTPUT_DIR=$OutputDir" "packaging\windows_installer.nsi"
if ($LASTEXITCODE -ne 0) { throw "NSIS 安装器构建失败。" }

$Installers = @(Get-ChildItem $OutputDir -Filter "*.exe")
if ($Installers.Count -ne 1) { throw "安装器数量异常：$($Installers.Count)。" }
$Installer = $Installers[0]
$Hash = (Get-FileHash -Algorithm SHA256 $Installer.FullName).Hash.ToLowerInvariant()
Set-Content -Path (Join-Path $OutputDir "SHA256SUMS.txt") -Value "$Hash *$($Installer.Name)" -Encoding ASCII
Copy-Item (Join-Path $PayloadDir "DEPENDENCIES.txt") $OutputDir
Write-Host "[sta-lite] 已生成 $($Installer.FullName)"
