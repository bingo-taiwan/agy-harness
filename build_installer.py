<#
.SYNOPSIS
    Antigravity CLI (agy) Universal Multi-Format & OneDrive Harness Installer
.DESCRIPTION
    Injects agy CLI protection rules for PDF, DOCX, XLSX, PPTX, Images, Archives,
    and Microsoft OneDrive Cloud Files-On-Demand, auto-hydration protocols,
    and installs the agy-safe wrapper for all agy users on Windows.
#>

[CmdletBinding()]
param(
    [switch]$Force
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Antigravity CLI (agy) OneDrive & Multi-Format Harness Setup" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$userHome = $env:USERPROFILE
$geminiDir = Join-Path $userHome ".gemini"
$agentsFile = Join-Path $userHome "AGENTS.md"
$claudeFile = Join-Path $userHome "CLAUDE.md"
$geminiMdFile = Join-Path $geminiDir "GEMINI.md"

$ruleBlock = @"

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
"@

function Patch-ConfigFile {
    param(
        [string]$FilePath
    )
    if (Test-Path -LiteralPath $FilePath) {
        $content = Get-Content -LiteralPath $FilePath -Raw -Encoding UTF8
        if ($content -notlike "*OneDrive 與雲端隨選檔案*") {
            Add-Content -LiteralPath $FilePath -Value $ruleBlock -Encoding UTF8
            Write-Host "[+] 成功注入 agy OneDrive 與全格式安全鐵律至: $FilePath" -ForegroundColor Green
        } else {
            Write-Host "[~] 檔案已包含 agy OneDrive 安全鐵律: $FilePath" -ForegroundColor Yellow
        }
    } else {
        Set-Content -LiteralPath $FilePath -Value ("# 全域指南`n" + $ruleBlock) -Encoding UTF8
        Write-Host "[+] 建立並寫入 agy OneDrive 安全鐵律至: $FilePath" -ForegroundColor Green
    }
}

# 1. 注入設定檔
Write-Host ">>> 階段 1: 注入全域系統設定檔 (AGENTS.md / GEMINI.md / CLAUDE.md)" -ForegroundColor Cyan
Patch-ConfigFile -FilePath $agentsFile
Patch-ConfigFile -FilePath $geminiMdFile
Patch-ConfigFile -FilePath $claudeFile

# 2. 複製 agy-safe 腳本至使用者 bin 目錄
Write-Host ""
Write-Host ">>> 階段 2: 安裝 agy-safe 包裝安全腳本" -ForegroundColor Cyan
$targetBin = Join-Path $geminiDir "bin"
if (-not (Test-Path -LiteralPath $targetBin)) {
    New-Item -ItemType Directory -Path $targetBin -Force | Out-Null
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sourceSafeScript = Join-Path $scriptDir "agy-safe.ps1"
$targetSafeScript = Join-Path $targetBin "agy-safe.ps1"

if (Test-Path -LiteralPath $sourceSafeScript) {
    Copy-Item -LiteralPath $sourceSafeScript -Destination $targetSafeScript -Force
    Write-Host "[+] 已複製 agy-safe.ps1 至: $targetSafeScript" -ForegroundColor Green
} else {
    Write-Host "[!] 警告: 未找到源頭 agy-safe.ps1，請確認腳本目錄完整。" -ForegroundColor Red
}

# 3. 提供別名指引
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " 安裝完成！已支援 Microsoft OneDrive / NAS / 全格式自動防禦 " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "快捷呼叫建議：您可以在 PowerShell Profile 加入別名：" -ForegroundColor Yellow
Write-Host "   function agy-safe { & 'C:\Users\user\.gemini\bin\agy-safe.ps1' `$args }" -ForegroundColor White
Write-Host ""
