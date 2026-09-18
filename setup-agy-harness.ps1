<#
.SYNOPSIS
    Antigravity CLI (agy) Universal Multi-Format & OneDrive Harness Installer / Updater
.DESCRIPTION
    Injects a VERSIONED agy protection rule block into ~/AGENTS.md, ~/.gemini/GEMINI.md, ~/CLAUDE.md
    and installs the agy-safe wrapper. Re-running this script is how you update:
    an older block is replaced in place, the same version is left alone, user text outside the block is never touched.
    Works both from a git clone and from the one-liner (iwr ... | iex): with no script directory it downloads
    VERSION and agy-safe.ps1 from GitHub raw.
#>

[CmdletBinding()]
param(
    [switch]$Force
)

$RawBase = "https://raw.githubusercontent.com/bingo-taiwan/agy-harness/main"

# ---- 1. 取得自己的版本與 agy-safe.ps1（clone 目錄優先，一鍵安裝時走網路）----
$scriptDir = $null
if ($PSScriptRoot) { $scriptDir = $PSScriptRoot }
elseif ($MyInvocation.MyCommand.Path) { $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }

$Version = $null
$sourceSafeScript = $null
if ($scriptDir -and (Test-Path -LiteralPath (Join-Path $scriptDir "VERSION"))) {
    $Version = (Get-Content -LiteralPath (Join-Path $scriptDir "VERSION") -Raw).Trim()
    $sourceSafeScript = Join-Path $scriptDir "agy-safe.ps1"
} else {
    try {
        $Version = (Invoke-WebRequest -UseBasicParsing -Uri "$RawBase/VERSION" -TimeoutSec 10).Content.Trim()
        $sourceSafeScript = Join-Path $env:TEMP "agy-safe.ps1"
        Invoke-WebRequest -UseBasicParsing -Uri "$RawBase/agy-safe.ps1" -OutFile $sourceSafeScript -TimeoutSec 10
    } catch {
        Write-Error "無法從 GitHub 取得 VERSION / agy-safe.ps1：$($_.Exception.Message)"
        exit 1
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Antigravity CLI (agy) Harness Setup  v$Version" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$userHome = $env:USERPROFILE
$geminiDir = Join-Path $userHome ".gemini"
$agentsFile = Join-Path $userHome "AGENTS.md"
$claudeFile = Join-Path $userHome "CLAUDE.md"
$geminiMdFile = Join-Path $geminiDir "GEMINI.md"
if (-not (Test-Path -LiteralPath $geminiDir)) { New-Item -ItemType Directory -Path $geminiDir -Force | Out-Null }

$BeginMark = "<!-- agy-harness:begin v$Version -->"
$EndMark   = "<!-- agy-harness:end -->"

$ruleBlock = @"
$BeginMark
## agy CLI 全格式與 Microsoft OneDrive 雲端文檔處理鐵律（重要）
- **OneDrive 與雲端隨選檔案 (Files-On-Demand) 處理**：
  位於 Microsoft OneDrive (`OneDrive`, `OneDrive - 公司/機構名稱`) 的檔案可能處於「僅限雲端 (Offline/Placeholder)」狀態。
  - Agent **必須使用 PowerShell (`Copy-Item -LiteralPath ...`)** 將 OneDrive 檔案下載並強制實體化 (Hydrate) 複製至 `C:\temp\` 本地 SSD 目錄後方可使用，**嚴禁讓用戶手動下檔或搬運**。
- **二進位檔與文檔嚴禁直呼 view_file / Read**：
  包含圖檔 (`.jpg`, `.png`, `.webp`)、PDF (`.pdf`)、Word (`.docx`, `.doc`)、Excel (`.xlsx`, `.xls`)、PPT (`.pptx`, `.ppt`) 及壓縮包 (`.zip`, `.7z`, `.rar`) 等非純文字檔，**嚴禁發起 view_file 或 Read 工具**（避免觸發 `media has no inline data` 400 崩潰或 Raw Byte 轉譯死鎖）。
  - **PDF 處理**：優先使用 `pdf-inspector <file>` 直抽文本，或 Python `pypdf`/`fitz` 處理。
  - **Word / Excel / PPT**：使用 Python 庫 (`python-docx`, `pandas`/`openpyxl`, `python-pptx`) 或 PowerShell 分析，不得發起 view_file。
  - **二進位圖檔**：僅能在命令入口以 `@path` 注入，或用 `generate_image` / Python 處理。
- **全自主檔案搬運與複製**：遇到 OneDrive、NAS/網路磁碟 (`X:\`)、中文或含空格路徑時，Agent 必須**自主使用 PowerShell (`Copy-Item -LiteralPath ...`)** 複製到本地短路徑（如 `C:\temp\`），**嚴禁要求用戶手動搬運檔案**。
- **全自動任務執行與產出**：當用戶要求處理文件、轉換資料、分析報表或合成圖片時，Agent 必須自動準備檔案、執行腳本/工具並產出最終交付檔，不可只出建議或拋回給用戶。
- **崩潰處理（Session 換新）**：若執行中意外觸發 `Agent execution terminated due to error`，提示用戶此 Session 歷史已毒化，需開新 Session 執行。
$EndMark
"@

# 舊版（v1.0 之前）沒有標記，只能靠這句標題辨認
$LegacyHeading = "## agy CLI 全格式"

function Patch-ConfigFile {
    param([string]$FilePath)
    if (-not (Test-Path -LiteralPath $FilePath)) {
        Set-Content -LiteralPath $FilePath -Value ("# 全域指南`n`n" + $ruleBlock) -Encoding UTF8
        Write-Host "[+] 建立並寫入 v$Version 規則區塊: $FilePath" -ForegroundColor Green
        return
    }
    $content = Get-Content -LiteralPath $FilePath -Raw -Encoding UTF8
    $m = [regex]::Match($content, '(?s)<!-- agy-harness:begin v([0-9.]+) -->.*?<!-- agy-harness:end -->')
    if ($m.Success) {
        $installed = [version]$m.Groups[1].Value
        if ($installed -ge [version]$Version -and -not $Force) {
            Write-Host "[~] 已是 v$installed，略過: $FilePath" -ForegroundColor Yellow
            return
        }
        $content = $content.Substring(0, $m.Index) + $ruleBlock.TrimEnd() + $content.Substring($m.Index + $m.Length)
        Set-Content -LiteralPath $FilePath -Value $content -Encoding UTF8 -NoNewline
        Write-Host "[^] v$installed -> v$Version 已更新規則區塊: $FilePath" -ForegroundColor Green
        return
    }
    Add-Content -LiteralPath $FilePath -Value ("`n" + $ruleBlock) -Encoding UTF8
    Write-Host "[+] 已加入 v$Version 規則區塊: $FilePath" -ForegroundColor Green
    if ($content -like "*$LegacyHeading*") {
        Write-Host "    [!] 檔案裡還有舊版（無標記）的「$LegacyHeading…」區塊，內容重複無害；想清乾淨可手動刪掉那段。" -ForegroundColor DarkYellow
    }
}

Write-Host ">>> 階段 1: 注入 / 更新規則區塊 (AGENTS.md / GEMINI.md / CLAUDE.md)" -ForegroundColor Cyan
Patch-ConfigFile -FilePath $agentsFile
Patch-ConfigFile -FilePath $geminiMdFile
Patch-ConfigFile -FilePath $claudeFile

# ---- 2. 安裝 agy-safe.ps1 與版本記錄 ----
Write-Host ""
Write-Host ">>> 階段 2: 安裝 agy-safe 包裝腳本" -ForegroundColor Cyan
$targetBin = Join-Path $geminiDir "bin"
if (-not (Test-Path -LiteralPath $targetBin)) { New-Item -ItemType Directory -Path $targetBin -Force | Out-Null }
$targetSafeScript = Join-Path $targetBin "agy-safe.ps1"
if ($sourceSafeScript -and (Test-Path -LiteralPath $sourceSafeScript)) {
    Copy-Item -LiteralPath $sourceSafeScript -Destination $targetSafeScript -Force
    Write-Host "[+] agy-safe.ps1 -> $targetSafeScript" -ForegroundColor Green
} else {
    Write-Host "[!] 找不到 agy-safe.ps1，包裝腳本未安裝。" -ForegroundColor Red
}
Set-Content -LiteralPath (Join-Path $targetBin "agy-harness.version") -Value $Version -Encoding ASCII -NoNewline

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   agy-harness v$Version 安裝完成" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "更新方式：之後再跑一次同一行安裝指令即可，舊版規則區塊會被整段換新。" -ForegroundColor Yellow
Write-Host "快捷呼叫：在 PowerShell Profile 加入" -ForegroundColor Yellow
Write-Host "   function agy-safe { & '$targetSafeScript' `$args }" -ForegroundColor White
Write-Host ""
