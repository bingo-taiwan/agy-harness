<#
.SYNOPSIS
    Smart Multi-Format & OneDrive Safe Launcher for Antigravity CLI (agy)
.DESCRIPTION
    Wraps agy CLI with automatic pre-copying & cloud hydration for OneDrive,
    NAS (X:\), PDF, DOCX, XLSX, PPTX, Images & Archives, path normalization,
    optimal model injection, and crash recovery.
#>

[CmdletBinding()]
param(
    [string]$Prompt,
    [string]$Model = "claude-sonnet-4-6",
    [switch]$SkipPermissions = $true,
    [ValueFromRemainingArguments()]$ExtraArgs
)

$agyExe = "$env:LOCALAPPDATA\agy\bin\agy.exe"
if (-not (Test-Path -LiteralPath $agyExe)) {
    $agyExe = (Get-Command agy -ErrorAction SilentlyContinue).Path
}

if (-not $agyExe -or -not (Test-Path -LiteralPath $agyExe)) {
    Write-Error "找不到 agy.exe 可執行檔，請確認 agy 已正確安裝。"
    exit 1
}

# 涵蓋二進位檔副檔名正則
$supportedExt = "(jpg|jpeg|png|webp|gif|bmp|pdf|docx?|xlsx?|pptx?|zip|rar|7z|csv)"
# 包含 OneDrive, X:\-Z:\, 或包含 spaces/Chinese 的檔案路徑正則
$pathPattern = "([A-Z]:\\[^\s'\"]*(?:OneDrive|[X-Z]:)[^\s'\"]*\.$supportedExt|[A-Z]:\\[^\s'\"]+\.$supportedExt)"

if ($Prompt -and ($Prompt -match $pathPattern)) {
    Write-Host "[agy-safe] 檢測到 Prompt 包含 OneDrive / 網路硬碟 / 外部文檔，進行自動實體化轉存預處理..." -ForegroundColor Yellow
    $matchesList = [regex]::Matches($Prompt, $pathPattern)
    
    $tempDir = "C:\temp"
    if (-not (Test-Path -LiteralPath $tempDir)) {
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    }
    
    $idx = 1
    foreach ($m in $matchesList) {
        $srcPath = $m.Value
        if (Test-Path -LiteralPath $srcPath) {
            $ext = [System.IO.Path]::GetExtension($srcPath)
            $baseName = [System.IO.Path]::GetFileNameWithoutExtension($srcPath)
            # 安全檔名化
            $safeName = ($baseName -replace "[^\w\.-]", "_") + "_onedrive_$idx$ext"
            $destPath = "$tempDir\$safeName"
            
            # 使用 Copy-Item -LiteralPath 強制觸發 OneDrive Cloud Files-On-Demand 下載實體化
            Copy-Item -LiteralPath $srcPath -Destination $destPath -Force
            Write-Host "[agy-safe] 已將 OneDrive / 網路檔案實體化轉存至: $destPath" -ForegroundColor Green
            $Prompt = $Prompt.Replace($srcPath, $destPath)
            $idx++
        }
    }
}

$cmdArgs = @()
if ($Model) {
    $cmdArgs += "--model"
    $cmdArgs += $Model
}
if ($SkipPermissions) {
    $cmdArgs += "--dangerously-skip-permissions"
}
if ($Prompt) {
    $cmdArgs += "-p"
    $cmdArgs += $Prompt
}
if ($ExtraArgs) {
    $cmdArgs += $ExtraArgs
}

Write-Host "[agy-safe] 啟動 OneDrive / 全格式加固版 agy CLI (Model: $Model)..." -ForegroundColor Cyan
& $agyExe @cmdArgs

$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "[agy-safe] 警告: agy CLI 異常終止 (Exit Code: $exitCode)。" -ForegroundColor Red
    Write-Host "[agy-safe] 若為二進位檔/OneDrive view_file 錯，此 Session 歷史已毒化，請開新 Session 執行。" -ForegroundColor Yellow
}
