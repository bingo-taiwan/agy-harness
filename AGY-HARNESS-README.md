# 🛡️ Antigravity CLI (agy) OneDrive 與全格式通用加固工具組 (agy-harness)

本工具組全面支援 **Microsoft OneDrive 雲端隨選文檔 (`Cloud Files-On-Demand`)**、**NAS 網路硬碟 (`X:\`)**、以及包含 **PDF (.pdf)**、**Word (.docx/.doc)**、**Excel (.xlsx/.csv)**、**PowerPoint (.pptx/.ppt)**、**圖檔 (.jpg/.png/.webp)** 及 **壓縮檔 (.zip/.7z/.rar)** 在內的所有二進位與辦公室文檔！

---

## ⚡ 解決的核心痛點

1. **Microsoft OneDrive 雲端隨選檔案鎖死/0-Byte**  
   OneDrive 檔案可能處於「僅限雲端 (Offline/Placeholder)」狀態。一般 CLI 工具直接讀取時會觸發檔案鎖定、讀取 0-Byte 或權限逾時問題。工具組會自動透過 PowerShell `-LiteralPath` 強制下載實體化 (Hydrate) 至 `C:\temp\` 本地 SSD 目錄。
2. **二進位/Office/PDF 文檔 view_file/Read 轉譯崩潰 (`media has no inline data`)**  
   `agy` 對非純文字檔直接呼叫 `view_file` 時，會因缺少或無法轉譯 Inline Byte Data 引發 API `400 INVALID_ARGUMENT` 崩潰。
3. **Session 歷史軌跡毒化死循環**  
   一旦 Session Trajectory 寫入壞掉的二進位檔點，該 Session 便無法再復原，必須自動導引換新。

---

## 🚀 支援的儲存來源與檔案格式 (Storage & Format Matrix)

| 儲存/檔案類別 | 包含路徑 / 副檔名 | 專屬自動化防禦機制 (SOP) |
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

## 🚀 一鍵安裝與防禦注入 (Setup Guide)

在 Windows 終端執行安裝腳本即可注入 OneDrive 與全格式規則：

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\user\agy-harness\setup-agy-harness.ps1
```

### 安裝腳本會自動完成：
* **全格式全域設定補丁**：自動將 `OneDrive 與全格式二進位檔處理鐵律` 寫入 `AGENTS.md`、`GEMINI.md` 與 `CLAUDE.md`。
* **安全包裝器安裝**：將支援 OneDrive 與多格式的 `agy-safe.ps1` 安裝至 `C:\Users\user\.gemini\bin\`。

---

## 💡 使用方式 (Usage)

直接透過 `agy-safe.ps1` 傳送任何包含 OneDrive、NAS、PDF、DOCX、XLSX、PPTX、JPG 檔案的指令：

```powershell
# 範例 1：自動將 OneDrive 上的 PDF 實體化並整理成 Word 摘要
C:\Users\user\.gemini\bin\agy-safe.ps1 -p "請讀取 @'C:\Users\user\OneDrive - 學校\2026財報.pdf' 並自動整理成 C:\temp\摘要.docx"

# 範例 2：處理 OneDrive 照片與 NAS 上的 Excel 數據
C:\Users\user\.gemini\bin\agy-safe.ps1 -p "讀取 @'X:\專案\數據.xlsx' 與 OneDrive 圖片 @'C:\Users\user\OneDrive\圖片\活動照.jpg' 完成分析"
```

---

## 📂 工具檔案結構

* [setup-agy-harness.ps1](file:///C:/Users/user/agy-harness/setup-agy-harness.ps1) - OneDrive 與全格式一鍵注入與安裝檔
* [agy-safe.ps1](file:///C:/Users/user/agy-harness/agy-safe.ps1) - 支援 OneDrive Cloud Hydration 與全格式自動轉存加固執行的 CLI 包裝器
* [AGY-HARNESS-README.md](file:///C:/Users/user/agy-harness/AGY-HARNESS-README.md) - 使用說明與儲存/格式矩陣文件
