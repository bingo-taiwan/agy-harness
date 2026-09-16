# gemini-desktop：讓 agent 用上使用者的 Gemini 訂閱與 Gemini Desktop

遠端到朋友或客戶電腦、幫他裝 agy 之後，再跑這一包：裝好 Gemini Desktop，並讓他的 agent（agy、Claude Code、Copilot CLI）知道
「什麼任務該叫 Gemini Desktop、什麼任務走 gws / agy」。用的是他自己的 Pro / Ultra 額度，不燒 API key。

## 安裝

```powershell
# Windows（一般權限 PowerShell）
git clone https://github.com/bingo-taiwan/agy-harness.git
powershell -ExecutionPolicy Bypass -File .\agy-harness\gemini-desktop\install.ps1
```

```bash
# macOS
git clone https://github.com/bingo-taiwan/agy-harness.git
bash agy-harness/gemini-desktop/install.sh
```

裝完把 `GEMINI.md.snippet` 的內容貼進 `~/.gemini/GEMINI.md`（agy）或專案 `AGENTS.md` / `CLAUDE.md`。

## 目錄

| 檔案 | 用途 |
|------|------|
| `install.ps1` / `install.sh` | 下載官方安裝檔、安裝、提醒登入；Windows 版順便跑一次遙控體檢 |
| `windows/gemini.py` | 用 CDP 遙控 Windows 版 Gemini Desktop：`launch / doctor / ask / image / canvas / research / history / open / gems / tools / shot / close` |
| `windows/selectors-and-traps.md` | Gemini 改版後怎麼找新元件、已知的坑 |
| `GEMINI.md.snippet` | 給 agent 讀的路由規則（任務 → 工具）與 gemini.py 用法 |
| `mac/README.md` | macOS 版能拿到什麼（Spark、MCP、排程、技能）、為什麼 agent 遙控不了 |

## 兩個平台差在哪（2026-09-16 實測）

| | Windows（Electron） | macOS（原生 Swift） |
|---|---|---|
| agent 能遙控 | **能**，`gemini.py` 走 CDP | 不能 |
| 產圖 | 2752×1536 原尺寸落地 | 由人操作 |
| Deep Research | 能，約 10 分鐘取回報告與來源 | 由人操作 |
| Spark（排程、技能、Obsidian/Git MCP、自訂 MCP、資料夾） | Spark 分頁有，但只有雲端連接器 | **Ultra 帳號全有** |
| 電腦控制 | 沒有 | 程式裡有，帳號沒開 |
| 額度顯示 | 沒有 | 設定 → 用量限制 |

數字是 Ultra 帳號實測；Pro 帳號的額度與功能未驗證，導入前先看一次設定頁。

## 跟「只裝原生 agy」差在哪

原生 agy 是終端裡的 coding agent，模型走 Antigravity 帳號額度。裝了 agy-harness（含本模組）之後，多了三層東西：
檔案防護、對 Gemini Desktop 的遙控（Windows）與分工規則、以及使用者自己的 Gemini 訂閱額度。下面逐項比。

### 能力對照

| 能力 | 原生 agy | agy-harness + Gemini Desktop（Pro / Ultra 訂閱） |
|------|---------|------|
| 模型 | `agy models` 清單：Gemini 3.8/3.7/3.6 Flash、3.1 Pro、Claude Sonnet/Opus 4.6、GPT-OSS 120B，可 `--model` 逐次切換 | 同上，再加 Gemini app 內的 Flash-Lite / Flash / Pro / 延伸思考（用訂閱額度） |
| 額度來源 | Antigravity 帳號 | 兩池並用：agy 跑程式碼，Gemini Desktop 跑產圖、研究，互不搶額度；macOS 版設定頁可看剩餘量 |
| 產圖 | `generate_image`，實測 1376×768、31 秒 | Windows 遙控 `gemini.py image`：Nano Banana 原尺寸 2752×1536，15–30 秒落地。免費 API key 的圖片配額是 0，訂閱是唯一不花錢的高解析路 |
| 長篇研究報告 | 沒有 | Deep Research：實測約 9.5 分鐘，11,330 字＋111 個來源，落地成 markdown |
| 單頁程式 | agent 自己寫 | 另有 Canvas：`gemini.py canvas` 取回完整 HTML |
| Google 連接器 | 沒有（要自己接 gws 或 MCP） | `@Gmail`、`@雲端硬碟`、`@日曆`、`@Keep`、`@Tasks`、`@商家檔案` 等 15 項；適合「幫我摘要」而不是查資料（查資料 gws 3 秒，Gemini 24 秒） |
| Gems、對話紀錄、Gemini Notebook | 沒有 | `gemini.py gems / history / open` 讀得到 |
| 排程、技能、Obsidian/Git MCP、自訂 MCP、本機資料夾、手機遠端派工 | agy 有自己的 MCP（stdio/SSE/HTTP）與 skills | **macOS Ultra 帳號**多一套 Spark 版：給使用者自己在視窗裡用，agent 不能遙控 |
| 讀圖、讀 PDF | `@路徑` 秒級 | 同上；要 Ultra 的 Pro 模型看檔才走 Desktop `--file`（18 秒） |
| 二進位檔／OneDrive／NAS 中文路徑 | 直接 `view_file` 會 400 崩潰、session 毒化 | harness 本體：自動實體化、禁 view_file、搬到短路徑 |
| agent 選錯工具 | 靠它自己猜 | `GEMINI.md.snippet` 一張表：查資料 gws、無頭 agy、獨有功能 Desktop |
| Claude/agy 這邊的 token | 原始資料進 context | Gemini 先摘要再回傳：同一件 Gmail 任務實測 200–300 tokens 對 600–800 |

### 什麼時候只裝原生 agy 就夠

- 純寫程式、改 repo、跑測試，不碰 Google 服務也不產圖。
- 需要無頭、可版控、批次幾百次的呼叫。Gemini Desktop 一次只能一個對話、慢、且批次有違反使用條款的風險。
- 對方沒有 Pro / Ultra 訂閱。本模組的數字都是訂閱帳號實測，免費帳號沒驗證過，別拿這裡的數字去承諾。

### 什麼時候值得多裝這一包

- 對方已付 Pro / Ultra，想把訂閱額度「當成 agent 的工具」而不是只在視窗聊天。
- 工作常要高解析圖、附來源的長報告、Gmail / 日曆摘要、Canvas 小工具。
- 對方在 Mac 上用 Ultra：Spark 的排程、技能、Obsidian/Git MCP 是目前消費者 Gemini 最接近「個人 agent」的東西，裝好、講清楚分工，他才會真的用起來。
- 對方常處理 OneDrive、NAS、中文路徑的 Office 檔：這是 harness 本體解決的老問題，跟 Gemini 無關但一起裝最省事。

### Pro 跟 Ultra 差在哪（誠實版）

本模組的數字全部來自 **Ultra** 帳號實測。Pro 帳號的 Deep Research 次數、產圖配額、macOS 有沒有 Spark 都**沒驗證**；
Google 官方只說額度按運算量計、每 5 小時補充、另有每週上限，Ultra 是 Pro 的數倍。導入 Pro 用戶前，先開一次設定 → 用量限制看實際數字。
Workspace 公司帳號實測沒有 Spark 分頁，是另一個產品線。

## 已知限制

- `gemini.py` 的元件定位照 zh-TW 介面文字寫，介面語言不是繁體中文要改檔頭 `SEL`；Gemini 改版壞掉先跑 `doctor`。
- 遙控埠開著等於本機任何程式都能操作該 Google 帳號，用完必 `close`。
- 每個指令都會在使用者的對話紀錄留一則。
