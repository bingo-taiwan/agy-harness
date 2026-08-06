# 🛡️ Antigravity CLI (agy) Universal Harness & Protection Toolset (`agy-harness`)

[![CI Pipeline](https://github.com/bingo-taiwan/agy-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/bingo-taiwan/agy-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Antigravity CLI](https://img.shields.io/badge/Antigravity_CLI-v1.1.10+-blue.svg)](https://github.com/bingo-taiwan/agy-harness)

A universal safety harness and automated protection toolset for **Google Antigravity CLI (`agy`)**.

It permanently fixes **binary file view crashes (`media has no inline data` HTTP 400)**, **trajectory session poisoning**, **Microsoft OneDrive Cloud Files-On-Demand lockups**, **NAS / long-path variable traps**, and **manual user file-moving burdens**.

---

## 🌐 語言 / Language

* [繁體中文 (Traditional Chinese)](#-繁體中文說明)
* [English Description](#-english-description)

---

## 🇹🇼 繁體中文說明

### ⚡ 解決的核心痛點

1. **Microsoft OneDrive 雲端隨選檔案鎖死 / 0-Byte**  
   OneDrive 檔案（包含個人版與企業/學校版 `OneDrive - 機構名稱`）常處於「僅限雲端 (Offline/Placeholder)」狀態。一般 CLI 工具直接存取會觸發檔案鎖定、讀取 0-Byte 或權限逾時問題。工具組會自動透過 PowerShell 強制下載實體化 (Hydrate) 至 `C:\temp\` 本地 SSD 目錄。
2. **二進位 / Office / PDF 文檔 view_file / Read 轉譯崩潰 (`media has no inline data`)**  
   `agy` 對非純文字檔（PDF、Word、Excel、PPT、二進位圖檔）直接呼叫 `view_file` 時，會因缺少或無法轉譯 Inline Byte Data 引發 API `400 INVALID_ARGUMENT` 崩潰。
3. **Session 歷史軌跡毒化死循環 (Trajectory Poisoning)**  
   一旦 Session Trajectory 寫入壞掉的二進位檔點，該 Session 便無法再復原，後續發送任何訊息（即使是簡單的 `"HI"`）都會持續觸發 400 錯誤。
4. **NAS / 長路徑 / 中文路徑被動搬運**  
   自動識別並複製 `X:\` 或繁體中文資料夾內的 PDF, DOCX, XLSX, PPTX, JPG 檔案至 `C:\temp\`，並轉譯為純英文短路徑，徹底擺脫手動搬運。

---

### 🚀 支援的儲存來源與檔案格式矩陣

| 儲存 / 檔案類別 | 包含路徑 / 副檔名 | 專屬自動化防禦機制 (SOP) |
| :--- | :--- | :--- |
| **OneDrive 雲端目錄** | `OneDrive`, `OneDrive - 機構名稱` | 自動在啟動前觸發 **Cloud Hydration** 下載並轉存至 `C:\temp\` 本地 SSD |
| **NAS / 網路磁碟機** | `X:\`, `Y:\`, `Z:\`, UNC 路徑 | 自動過濾空格與中文轉寫，避開 PowerShell 變數轉義失敗 |
| **PDF 文件** | `.pdf` | **禁止 `view_file`**。優先以 `pdf-inspector` 直抽文字，非文字頁走 Python/OCR |
| **Word 文件** | `.docx`, `.doc` | **禁止 `view_file`**。使用 Python `python-docx` 或 PowerShell 讀寫解析 |
| **Excel 試算表**| `.xlsx`, `.xls`, `.csv` | **禁止 `view_file`**。使用 Python `pandas` / `openpyxl` 或 PowerShell 解析 |
| **PPT 簡報** | `.pptx`, `.ppt` | **禁止 `view_file`**。使用 Python `python-pptx` 提取簡報內容與文字 |
| **影像圖片** | `.jpg`, `.png`, `.webp`, `.bmp` | **禁止 `view_file`**。透過 `@path` 注入，多圖合成直接呼叫 `generate_image` |
| **壓縮與二進位包**| `.zip`, `.rar`, `.7z` | **禁止 `view_file`**。使用 PowerShell `Expand-Archive` 或 Python 解壓 |

---

### 📦 安裝說明 (Quick Installation)

#### Windows (PowerShell) 一鍵安裝：
```powershell
powershell -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/bingo-taiwan/agy-harness/main/setup-agy-harness.ps1 | iex"
```
或直接複製 repo 並執行：
```powershell
git clone https://github.com/bingo-taiwan/agy-harness.git
cd agy-harness
powershell -ExecutionPolicy Bypass -File .\setup-agy-harness.ps1
```

#### Linux / macOS (Bash) 一鍵安裝：
```bash
git clone https://github.com/bingo-taiwan/agy-harness.git
cd agy-harness
bash setup-agy-harness.sh
```

---

### 💡 使用方式 (Usage)

直接透過包裝器 `agy-safe.ps1` 傳送任何包含 OneDrive、NAS、PDF、DOCX、XLSX、PPTX、JPG 檔案的指令：

```powershell
# 範例 1：自動將 OneDrive 上的 PDF 實體化並整理成 Word 摘要
C:\Users\user\.gemini\bin\agy-safe.ps1 -p "請讀取 @'C:\Users\user\OneDrive - 學校\2026財報.pdf' 並自動整理成 C:\temp\摘要.docx"

# 範例 2：處理 OneDrive 照片與 NAS 上的 Excel 數據
C:\Users\user\.gemini\bin\agy-safe.ps1 -p "讀取 @'X:\專案\數據.xlsx' 與 OneDrive 圖片 @'C:\Users\user\OneDrive\圖片\活動照.jpg' 完成分析"
```

---

## 🇺🇸 English Description

`agy-harness` is an open-source, production-grade safety wrapper and system rule harness for **Antigravity CLI (`agy`)**.

### Features:
- **Cloud Hydration**: Automatically forces Microsoft OneDrive Cloud Files-On-Demand to hydrate locally to `$env:TEMP` / `C:\temp\`.
- **Binary View Protection**: Prevents `agy` from calling `view_file` on binary files (`.jpg`, `.png`, `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.zip`), eliminating `media has no inline data` (HTTP 400) crashes.
- **Trajectory Sanitization**: Protects conversation sessions from permanent history poisoning.
- **Autonomous File Handling**: Pre-copies NAS (`X:\`) and paths containing spaces or non-ASCII characters without user intervention.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
