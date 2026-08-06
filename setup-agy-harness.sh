#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Antigravity CLI (agy) Universal Harness Setup Installer  "
echo "=========================================================="
echo ""

USER_HOME="$HOME"
GEMINI_DIR="$USER_HOME/.gemini"
AGENTS_FILE="$USER_HOME/AGENTS.md"
CLAUDE_FILE="$USER_HOME/CLAUDE.md"
GEMINI_MD_FILE="$GEMINI_DIR/GEMINI.md"

RULE_BLOCK='
## agy CLI 全格式與 Microsoft OneDrive 雲端文檔處理鐵律（重要）
- **OneDrive 與雲端隨選檔案 (Files-On-Demand) 處理**：
  位於 Microsoft OneDrive (`OneDrive`, `OneDrive - 公司/機構名稱`) 的檔案可能處於「僅限雲端 (Offline/Placeholder)」狀態。
  - Agent **必須使用腳本/命令** 將 OneDrive 檔案下載並強制實體化複製至 `/tmp/` 本地目錄後方可使用，**嚴禁讓用戶手動下檔或搬運**。
- **二進位檔與文檔嚴禁直呼 view_file / Read**：
  包含圖檔 (`.jpg`, `.png`, `.webp`)、PDF (`.pdf`)、Word (`.docx`, `.doc`)、Excel (`.xlsx`, `.xls`)、PPT (`.pptx`, `.ppt`) 及壓縮包 (`.zip`, `.7z`, `.rar`) 等非純文字檔，**嚴禁發起 view_file 或 Read 工具**（避免觸發 `media has no inline data` 400 崩潰或 Raw Byte 轉譯死鎖）。
  - **PDF 處理**：優先使用 `pdf-inspector <file>` 直抽文本，或 Python `pypdf`/`fitz` 處理。
  - **Word / Excel / PPT**：使用 Python 庫 (`python-docx`, `pandas`/`openpyxl`, `python-pptx`) 或 Bash 分析，不得發起 view_file。
  - **二進位圖檔**：僅能在命令入口以 `@path` 注入，或用 `generate_image` / Python 處理。
- **全自主檔案搬運與複製**：遇到 OneDrive、NAS/網路磁碟、中文或含空格路徑時，Agent 必須**自主使用 Shell/PowerShell** 複製到本地短路徑（如 `/tmp/`），**嚴禁要求用戶手動搬運檔案**。
- **全自動任務執行與產出**：當用戶要求處理文件、轉換資料、分析報表或合成圖片時，Agent 必須自動準備檔案、執行腳本/工具並產出最終交付檔，不可只出建議或拋回給用戶。
- **崩潰處理（Session 換新）**：若執行中意外觸發 `Agent execution terminated due to error`，提示用戶此 Session 歷史已毒化，需開新 Session 執行。
'

patch_config_file() {
    local target_file="$1"
    if [ -f "$target_file" ]; then
        if ! grep -q "OneDrive 與雲端隨選檔案" "$target_file"; then
            echo "$RULE_BLOCK" >> "$target_file"
            echo "[+] 成功注入 agy 全格式與 OneDrive 安全鐵律至: $target_file"
        else
            echo "[~] 檔案已包含 agy 安全鐵律: $target_file"
        fi
    else
        echo "# 全域指南" > "$target_file"
        echo "$RULE_BLOCK" >> "$target_file"
        echo "[+] 建立並寫入 agy 安全鐵律至: $target_file"
    fi
}

mkdir -p "$GEMINI_DIR"
patch_config_file "$AGENTS_FILE"
patch_config_file "$GEMINI_MD_FILE"
patch_config_file "$CLAUDE_FILE"

echo ""
echo "=========================================================="
echo "   安裝完成！已支援 OneDrive / NAS / 全格式自動防禦 "
echo "=========================================================="
