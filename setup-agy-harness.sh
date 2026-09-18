#!/usr/bin/env bash
# Antigravity CLI (agy) Harness Installer / Updater (Linux / macOS)
# 把「有版本標記」的規則區塊注入 ~/AGENTS.md、~/.gemini/GEMINI.md、~/CLAUDE.md。
# 更新方式就是再跑一次：舊版區塊整段換新、同版本略過、區塊外的使用者文字不動。
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAW_BASE="https://raw.githubusercontent.com/bingo-taiwan/agy-harness/main"
if [ -f "$SCRIPT_DIR/VERSION" ]; then
    VERSION="$(tr -d '[:space:]' < "$SCRIPT_DIR/VERSION")"
else
    VERSION="$(curl -fsSL --max-time 10 "$RAW_BASE/VERSION" | tr -d '[:space:]')" || { echo "無法取得 VERSION"; exit 1; }
fi
FORCE="${1:-}"   # 傳 --force 可同版本重寫

echo "=========================================================="
echo " Antigravity CLI (agy) Harness Setup  v$VERSION"
echo "=========================================================="
echo ""

GEMINI_DIR="$HOME/.gemini"
AGENTS_FILE="$HOME/AGENTS.md"
CLAUDE_FILE="$HOME/CLAUDE.md"
GEMINI_MD_FILE="$GEMINI_DIR/GEMINI.md"
BEGIN_MARK="<!-- agy-harness:begin v$VERSION -->"
END_MARK="<!-- agy-harness:end -->"

RULE_BLOCK="$BEGIN_MARK
## agy CLI 全格式與 Microsoft OneDrive 雲端文檔處理鐵律（重要）
- **OneDrive 與雲端隨選檔案 (Files-On-Demand) 處理**：
  位於 Microsoft OneDrive (\`OneDrive\`, \`OneDrive - 公司/機構名稱\`) 的檔案可能處於「僅限雲端 (Offline/Placeholder)」狀態。
  - Agent **必須使用腳本/命令** 將 OneDrive 檔案下載並強制實體化複製至 \`/tmp/\` 本地目錄後方可使用，**嚴禁讓用戶手動下檔或搬運**。
- **二進位檔與文檔嚴禁直呼 view_file / Read**：
  包含圖檔 (\`.jpg\`, \`.png\`, \`.webp\`)、PDF (\`.pdf\`)、Word (\`.docx\`, \`.doc\`)、Excel (\`.xlsx\`, \`.xls\`)、PPT (\`.pptx\`, \`.ppt\`) 及壓縮包 (\`.zip\`, \`.7z\`, \`.rar\`) 等非純文字檔，**嚴禁發起 view_file 或 Read 工具**（避免觸發 \`media has no inline data\` 400 崩潰或 Raw Byte 轉譯死鎖）。
  - **PDF 處理**：優先使用 \`pdf-inspector <file>\` 直抽文本，或 Python \`pypdf\`/\`fitz\` 處理。
  - **Word / Excel / PPT**：使用 Python 庫 (\`python-docx\`, \`pandas\`/\`openpyxl\`, \`python-pptx\`) 或 Bash 分析，不得發起 view_file。
  - **二進位圖檔**：僅能在命令入口以 \`@path\` 注入，或用 \`generate_image\` / Python 處理。
- **全自主檔案搬運與複製**：遇到 OneDrive、NAS/網路磁碟、中文或含空格路徑時，Agent 必須**自主使用 Shell/PowerShell** 複製到本地短路徑（如 \`/tmp/\`），**嚴禁要求用戶手動搬運檔案**。
- **全自動任務執行與產出**：當用戶要求處理文件、轉換資料、分析報表或合成圖片時，Agent 必須自動準備檔案、執行腳本/工具並產出最終交付檔，不可只出建議或拋回給用戶。
- **崩潰處理（Session 換新）**：若執行中意外觸發 \`Agent execution terminated due to error\`，提示用戶此 Session 歷史已毒化，需開新 Session 執行。
$END_MARK"

# 版本比較：$1 >= $2 ?
ver_ge() { [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -1)" = "$2" ]; }

patch_config_file() {
    local f="$1"
    if [ ! -f "$f" ]; then
        printf '# 全域指南\n\n%s\n' "$RULE_BLOCK" > "$f"
        echo "[+] 建立並寫入 v$VERSION 規則區塊: $f"
        return
    fi
    local installed
    installed="$(grep -o '<!-- agy-harness:begin v[0-9.]* -->' "$f" | head -1 | sed 's/.*begin v\([0-9.]*\).*/\1/')"
    if [ -n "$installed" ]; then
        if ver_ge "$installed" "$VERSION" && [ "$FORCE" != "--force" ]; then
            echo "[~] 已是 v$installed，略過: $f"
            return
        fi
        # 用 python3 做跨行替換（macOS 內建，避開 sed 跨行與 BSD/GNU 差異）
        RULE_BLOCK="$RULE_BLOCK" python3 - "$f" <<'PY'
import os, re, sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
s = re.sub(r'<!-- agy-harness:begin v[0-9.]+ -->.*?<!-- agy-harness:end -->', lambda _: os.environ["RULE_BLOCK"], s, count=1, flags=re.S)
open(p, "w", encoding="utf-8").write(s)
PY
        echo "[^] v$installed -> v$VERSION 已更新規則區塊: $f"
        return
    fi
    printf '\n%s\n' "$RULE_BLOCK" >> "$f"
    echo "[+] 已加入 v$VERSION 規則區塊: $f"
    if grep -q "## agy CLI 全格式" "$f"; then
        echo "    [!] 檔案裡還有舊版（無標記）的「## agy CLI 全格式…」區塊，內容重複無害；想清乾淨可手動刪掉那段。"
    fi
}

mkdir -p "$GEMINI_DIR/bin"
patch_config_file "$AGENTS_FILE"
patch_config_file "$GEMINI_MD_FILE"
patch_config_file "$CLAUDE_FILE"
printf '%s' "$VERSION" > "$GEMINI_DIR/bin/agy-harness.version"

echo ""
echo "=========================================================="
echo "   agy-harness v$VERSION 安裝完成"
echo "=========================================================="
echo "更新方式：之後再跑一次同一行安裝指令即可，舊版規則區塊會被整段換新。"
