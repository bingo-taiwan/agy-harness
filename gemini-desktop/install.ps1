# gemini-desktop/install.ps1 — Windows：裝 Gemini Desktop，並確認 agent 橋接（CDP）可用
# 用法（一般權限 PowerShell，不要用系統管理員）：
#   powershell -ExecutionPolicy Bypass -File .\gemini-desktop\install.ps1
# 做的事：1) 沒裝就下載官方 GeminiSetup.exe 執行  2) 等 Gemini.exe 出現  3) 提醒登入  4) 跑 gemini.py doctor
# ponytail: 官方安裝檔沒有文件化的靜默參數，就讓安裝視窗正常跑；遠端桌面時有人在旁邊按，不需要無人值守。

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8   # 中文訊息在舊版主控台不變亂碼
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Url  = "https://gemini.google/download/windows/"          # 302 → dl.google.com/.../GeminiSetup.exe
$ExePattern = Join-Path $env:LOCALAPPDATA "Google\Gemini\app-*\Gemini.exe"

function Find-Gemini { Get-ChildItem $ExePattern -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1 }

$exe = Find-Gemini
if ($exe) {
    Write-Host "[ok] Gemini Desktop 已安裝：$($exe.FullName)"
} else {
    $setup = Join-Path $env:TEMP "GeminiSetup.exe"
    Write-Host "[..] 下載官方安裝檔 → $setup"
    Invoke-WebRequest -Uri $Url -OutFile $setup -UseBasicParsing -MaximumRedirection 5
    if ((Get-Item $setup).Length -lt 1MB) { throw "下載的檔案太小，可能不是安裝檔：$setup" }
    Write-Host "[..] 執行安裝程式（會跳視窗，照著按）"
    Start-Process $setup -Wait
    $deadline = (Get-Date).AddMinutes(5)
    while (-not (Find-Gemini) -and (Get-Date) -lt $deadline) { Start-Sleep 3 }
    $exe = Find-Gemini
    if (-not $exe) { throw "5 分鐘內沒看到 Gemini.exe 出現在 $ExePattern，安裝可能被取消" }
    Write-Host "[ok] 已安裝：$($exe.FullName)"
}

# 前置：uv（跑 gemini.py 用，免全域 pip）
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[..] 安裝 uv（Python 執行器）"
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

Write-Host ""
Write-Host "==> 請先打開 Gemini Desktop 用你的 Google 帳號登入（Pro / Ultra 訂閱才有產圖與 Deep Research 額度）。"
Write-Host "    登入後把 Gemini 介面語言設為「繁體中文」：gemini.py 的元件定位是照 zh-TW 文字寫的。"
Write-Host "    登入完成按 Enter 繼續檢查；要跳過就 Ctrl+C。"
$null = Read-Host

$env:PYTHONIOENCODING = "utf-8"
$py = Join-Path $Here "windows\gemini.py"
Write-Host "[..] 帶遙控埠啟動並體檢（會關掉目前開著的 Gemini 視窗）"
uv run -q --with websocket-client python $py launch --restart
uv run -q --with websocket-client python $py doctor
uv run -q --with websocket-client python $py close --reopen
Write-Host ""
Write-Host "[ok] 完成。把 gemini-desktop/GEMINI.md.snippet 的內容貼進這台電腦的 ~/.gemini/GEMINI.md（或專案 AGENTS.md），agent 就知道什麼任務該叫 Gemini Desktop。"
