# 🛡️ agy-harness: get the most out of Google AI Pro / Ultra with Antigravity CLI (`agy`)

[![CI Pipeline](https://github.com/bingo-taiwan/agy-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/bingo-taiwan/agy-harness/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Antigravity CLI](https://img.shields.io/badge/Antigravity_CLI-v1.1.10+-blue.svg)](https://github.com/bingo-taiwan/agy-harness)

For people who pay for **Google AI Pro / Ultra** and run **Antigravity CLI (`agy`)**: a routing guide plus tooling so your agent
spends the right quota on the right task (`gws` for data, `agy` for code and pipelines, your subscription for full-size Nano Banana,
Deep Research and Canvas via CDP remote control on Windows and macOS), and a file safety harness so `agy` never again bricks a session
on a PDF, Office file, image, OneDrive placeholder or NAS path.

給付了 **Google AI Pro / Ultra** 又在用 **Antigravity CLI（`agy`）** 的人：一張「什麼任務走哪條路、吃哪池額度」的對照表，
加上讓 agent 用訂閱額度產原尺寸圖、跑 Deep Research、寫 Canvas 的遙控工具（Windows / macOS），
以及讓 `agy` 不再被 PDF / Office / 圖檔 / OneDrive / NAS 路徑炸掉 session 的檔案安全 harness。

---

## 🌐 語言 / Language

* [繁體中文 (Traditional Chinese)](#-繁體中文說明)
* [English Description](#-english-description)

---

## 🇹🇼 繁體中文說明

### 這一包是給誰的

你付了 **Google AI Pro 或 Ultra**，也在用 **Antigravity CLI（`agy`）**。然後你會撞到三件事：

1. **額度是兩池，不是一池。** `agy` 吃 Antigravity 帳號的額度；Gemini app / 網頁版吃你的訂閱額度。不知道這件事，就會一直用 `agy` 產 1376×768 的圖，而訂閱裡 2752×1536 的 Nano Banana、Deep Research、Canvas 從沒被 agent 用過。
2. **訂閱獨有的功能 agent 碰不到。** Gemini Desktop 和 `agy` 官方沒有互通介面。本包用 CDP（Chrome 除錯協定）遙控 Gemini Desktop（Windows）或 Chrome 開的 gemini.google.com（macOS），讓 agent 用你的訂閱額度產圖、做 Deep Research、寫 Canvas，圖檔與報告直接落地成檔案。
3. **`agy` 一碰 PDF / Office / 圖檔就炸掉整個 session。** 本包的檔案安全 harness 擋掉 `view_file` 二進位崩潰、OneDrive 雲端檔鎖死、NAS 中文路徑搬運，session 不再被毒化。

所有數字都是 2026-09-15 到 09-18 在台灣 **Ultra** 帳號實測。**Pro 帳號未驗證**：Deep Research 次數、產圖配額、macOS 有沒有 Spark 都可能不同，用到先跑一次 `doctor`。

---

### 一張表：什麼任務走哪條路

| 任務 | 用什麼 | 吃哪池額度 | 實測 |
| :--- | :--- | :--- | :--- |
| 查 / 寫 Gmail、日曆、Drive、Sheets | `gws` CLI | 不吃模型額度 | 3 秒回精確 JSON；Gemini `@Gmail` 要 24 秒且只給摘要 |
| 跑程式、批次、在 pipeline 裡問模型、無頭產圖 | `agy`（`generate_image`、`--model`） | Antigravity 帳號 | 產圖 31 秒，1376×768 |
| 原尺寸 Nano Banana 圖、Deep Research 長報告、Canvas 單頁程式、Gems、對話紀錄 | 本包 `gemini-desktop/cdp/gemini.py` 遙控（Windows 遙控 app；macOS 遙控 Chrome 網頁版，同一支腳本） | **訂閱額度** | 產圖 15–30 秒落地 2752×1536（macOS 網頁版 2816×1536）；Deep Research 約 9.5 分鐘 |
| 排程任務、技能、Obsidian / Git 本機 MCP、自訂 MCP、本機資料夾、手機遠端派工 | **macOS 版** Gemini Desktop 的 Spark 分頁，由人或手機操作 | 訂閱額度 | Ultra 帳號 2026-09-16 已開；Workspace 帳號沒有 Spark；app 本身沒有遙控入口 |
| 操控滑鼠鍵盤（Computer Use） | 目前沒有任何一條路 | — | macOS 版二進位檔有完整模組，但設定頁尚未對帳號開放 |
| 影片、音樂生成 | Gemini Desktop 工具選單有入口 | 訂閱額度 | 未實測 |

把這張表貼進你的 `AGENTS.md` / `GEMINI.md`（現成片段：`gemini-desktop/GEMINI.md.snippet`），agent 就會自己選對路。

---

### 兩池額度怎麼分配

- **`agy` 那池**拿來跑程式碼、批次、pipeline 裡的小圖。它免 UI、可 `--model` 換模型、可無頭。
- **訂閱那池**留給只有 Gemini 才有的東西：原尺寸產圖、Deep Research、Canvas、Gems。Ultra 是 5 小時滾動額度；macOS 版在「設定 → 用量限制」看得到進度條，Windows 版看不到。
- **免費 Gemini API key 的圖片模型配額是 0**（一律 429），所以訂閱是唯一不另外花錢的高解析產圖路。
- Deep Research 又慢又吃額度，本包預設停在研究計畫讓人確認，加 `--start` 才直接跑到報告。
- 每次遙控 `ask / image / canvas / research` 都會在你的 Gemini 對話紀錄留一則，做完會提醒。

---

### 30 分鐘裝好

**1. 裝 agy 與檔案安全 harness**

Windows（PowerShell）：
```powershell
powershell -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/bingo-taiwan/agy-harness/main/setup-agy-harness.ps1 | iex"
```
或 clone 後執行：
```powershell
git clone https://github.com/bingo-taiwan/agy-harness.git
cd agy-harness
powershell -ExecutionPolicy Bypass -File .\setup-agy-harness.ps1
```

Linux / macOS（Bash）：
```bash
git clone https://github.com/bingo-taiwan/agy-harness.git
cd agy-harness
bash setup-agy-harness.sh
```

**2. macOS 要讓遠端 agent 用這台的 `agy`，多做一步**（2026-09-18 mac mini 實測）

在 Mac 的 GUI Terminal 登入 `agy` 後，token 存在 Keychain，從 SSH 進來跑 `agy` 會一直回「請先登入」
（log 寫 `falling back to file: exit status 36`；先 `security unlock-keychain` 也沒用，因為 `agy` 是叫系統 `security` 指令讀 Keychain，SSH session 沒畫面跳「允許存取」）。
解法：在 Mac 上開 Terminal 執行 `ssh <user>@localhost`，在那個 session 裡再跑一次 `agy`。它會把 token 落地成
`~/.gemini/antigravity-cli/antigravity-oauth-token`（權限 600），之後任何機器 SSH 進來 `agy -p` 都通。

**3. 裝 Gemini Desktop 並登入訂閱帳號**

`gemini-desktop/install.ps1`（Windows）或 `gemini-desktop/install.sh`（macOS）會下載官方安裝檔、安裝、提醒登入。
遠端桌面幫人登入時跳出「密碼金鑰」QR code 不要掃（它靠藍牙找旁邊的裝置），按「Try another way」改用密碼。
Ultra 帳號登入後 macOS 版上方會多一個 Spark 分頁。

**4. 開遙控**

```bash
export PYTHONIOENCODING=utf-8
G="uv run -q --with websocket-client python gemini-desktop/cdp/gemini.py"
$G launch            # Windows：帶遙控埠重開 Gemini Desktop；macOS：開一個獨立 profile 的 Chrome 到 gemini.google.com（第一次要人登入一次）
$G doctor            # 帳號、模式、關鍵元件都在就緒
$G image "描述" --out-dir ./out              # 原尺寸產圖落地
$G ask "問題" --file ./doc.pdf --out ./a.md   # 看檔問答；--model flash-lite|flash|pro|thinking
$G canvas "需求" --out ./page.html            # Canvas 寫單頁程式
$G research "主題"                            # Deep Research：先停在計畫
$G research-start --conv <id> --out ./r.md    # 確認後開跑
$G close                                      # 用完一定關埠
```

macOS 細節（app 沒遙控入口、為什麼改走 Chrome 網頁版、關視窗後怎麼補分頁）：[`gemini-desktop/mac/README.md`](gemini-desktop/mac/README.md)。
Gemini 改版壞掉時怎麼找新元件：[`gemini-desktop/cdp/selectors-and-traps.md`](gemini-desktop/cdp/selectors-and-traps.md)。

**5. 把路由規則貼給 agent**

`gemini-desktop/GEMINI.md.snippet` 貼進 `~/.gemini/GEMINI.md`、專案 `AGENTS.md`，或 Claude Code 的 `CLAUDE.md`。

---

### 檔案安全 harness：`agy` 不再被二進位檔炸掉

步驟 1 的安裝腳本會把下面這些鐵律寫進 `~/.gemini/GEMINI.md`、`~/AGENTS.md`、`~/CLAUDE.md`：

| 儲存 / 檔案類別 | 包含路徑 / 副檔名 | 自動化防禦 |
| :--- | :--- | :--- |
| **OneDrive 雲端目錄** | `OneDrive`, `OneDrive - 機構名稱` | 啟動前先觸發 Cloud Hydration 下載，轉存到 `C:\temp\` 本地 SSD（Windows）或 `/tmp/`（macOS） |
| **NAS / 網路磁碟機** | `X:\`, `Y:\`, `Z:\`, UNC 路徑 | 自動複製到純英文短路徑，避開空格與中文的 PowerShell 轉義失敗 |
| **PDF** | `.pdf` | 禁止 `view_file`。`pdf-inspector` 直抽文字，非文字頁走 Python / OCR |
| **Word** | `.docx`, `.doc` | 禁止 `view_file`。`python-docx` 或 PowerShell |
| **Excel** | `.xlsx`, `.xls`, `.csv` | 禁止 `view_file`。`pandas` / `openpyxl` 或 PowerShell |
| **PPT** | `.pptx`, `.ppt` | 禁止 `view_file`。`python-pptx` |
| **圖片** | `.jpg`, `.png`, `.webp`, `.bmp` | 禁止 `view_file`。命令入口用 `@path` 注入；多圖合成直接呼叫 `generate_image` |
| **壓縮包** | `.zip`, `.rar`, `.7z` | 禁止 `view_file`。`Expand-Archive` 或 Python 解壓 |

為什麼要這樣擋：`agy` 對非純文字檔呼叫 `view_file` 會因無法轉譯 Inline Byte Data 觸發 API `400 INVALID_ARGUMENT`；
一旦壞掉的檔案點寫進 session 軌跡，之後送任何訊息（哪怕只是「HI」）都會繼續 400，這個 session 就報廢了，只能開新 session。

Windows 另外有包裝器 `agy-safe.ps1`，會在把指令交給 `agy` 之前先把 OneDrive / NAS 檔案實體化到本地：

```powershell
# 把 OneDrive 上的 PDF 實體化後整理成 Word 摘要
C:\Users\user\.gemini\bin\agy-safe.ps1 -p "請讀取 @'C:\Users\user\OneDrive - 學校\2026財報.pdf' 並自動整理成 C:\temp\摘要.docx"

# NAS 上的 Excel 加 OneDrive 圖片一起分析
C:\Users\user\.gemini\bin\agy-safe.ps1 -p "讀取 @'X:\專案\數據.xlsx' 與 OneDrive 圖片 @'C:\Users\user\OneDrive\圖片\活動照.jpg' 完成分析"
```

---

### 已知邊界與安全提醒

- **遙控埠開著的期間，本機任何程式都能操作這個已登入的 Google 帳號。** 用完就 `close`；絕對不要加 `--remote-allow-origins=*`。
- 元件定位照 **zh-TW 介面文字**寫，Gemini 介面語言要設繁體中文；其他語言要改 `gemini.py` 檔頭的 `SEL`。
- 一次只跑一個遙控指令，不要平行。
- 幾百張圖的批次不要走遙控（慢，而且有違反使用條款與帳號風控的風險），那種量走 API。
- Spark 排程 / 本機 MCP 沒有 agent 入口；Computer Use 尚未開放。

---

### 延伸閱讀

- 只裝原生 `agy` 跟多裝這一包差在哪、什麼時候原生就夠：[`gemini-desktop/README.md`「跟只裝原生 agy 差在哪」](gemini-desktop/README.md#跟只裝原生-agy差在哪)
- Windows 版 CDP 遙控、macOS 版逆向細節、三條路的速度與 token 對照：[Gemini Desktop 實機拆解第三版](https://notes.mynet.com.tw/tech/gemini-desktop-vs-agy-cli)
- 讓 agent 自動選對工具的 `AGENTS.md` 範本：[agent-md-starter](https://github.com/bingo-taiwan/agent-md-starter)

---

## 🇺🇸 English Description

### Who This Package Is For

You pay for **Google AI Pro or Ultra** and are using the **Antigravity CLI (`agy`)**. Then you hit three pain points:

1. **Quotas come from two separate pools, not one.** `agy` draws from your Antigravity account quota; the Gemini app and web version draw from your subscription quota. Without knowing this, you keep using `agy` to generate 1376×768 images, while the 2752×1536 Nano Banana, Deep Research, and Canvas from your subscription are never touched by your agent.
2. **Subscription-exclusive features are unreachable by agents.** Gemini Desktop and `agy` have no official interface between them. This package uses CDP (Chrome DevTools Protocol) to remotely control Gemini Desktop (Windows) or Chrome running gemini.google.com (macOS), letting your agent leverage your subscription quota to generate images, run Deep Research, and author in Canvas—saving image files and reports directly to disk.
3. **`agy` crashes the entire session whenever it touches PDF, Office, or image files.** The file safety harness in this package prevents `view_file` binary crashes, OneDrive cloud file deadlocks, and NAS Chinese path transfer issues, ensuring your session is never poisoned again.

All numbers are benchmarked on a Taiwan **Ultra** account from 2026-09-15 to 09-18. **Pro accounts are unverified**: Deep Research run limits, image generation quotas, and whether Spark is available on macOS may vary—run `doctor` first before relying on them.

---

### Quick Reference: Which Path for Which Task

| Task | Tool / Method | Quota Pool | Benchmark / Results |
| :--- | :--- | :--- | :--- |
| Read / write Gmail, Calendar, Drive, Sheets | `gws` CLI | Zero model quota | 3s returning precise JSON; Gemini `@Gmail` takes 24s and returns only a summary |
| Running code, batch processing, querying models in pipelines, headless image gen | `agy` (`generate_image`, `--model`) | Antigravity account | 31s image gen, 1376×768 |
| Full-size Nano Banana images, Deep Research long-form reports, Canvas single-page apps, Gems, conversation history | Remotely controlled via `gemini-desktop/cdp/gemini.py` (controls the app on Windows; controls Chrome web version on macOS with the same script) | **Subscription quota** | 15–30s image gen saved to disk at 2752×1536 (2816×1536 on macOS web); Deep Research ~9.5 min |
| Scheduled tasks, skills, Obsidian / Git local MCPs, custom MCPs, local folders, remote dispatch via mobile | **macOS** Gemini Desktop Spark tab, operated manually or from mobile | Subscription quota | Enabled for Ultra accounts on 2026-09-16; Workspace accounts do not have Spark; app itself lacks a remote control endpoint |
| Controlling mouse and keyboard (Computer Use) | Currently unavailable through any path | — | macOS binary contains complete modules, but settings page is not yet unlocked for accounts |
| Video and music generation | Available in Gemini Desktop tools menu | Subscription quota | Untested |

Paste this table into your `AGENTS.md` / `GEMINI.md` (ready-made snippet: `gemini-desktop/GEMINI.md.snippet`), and your agent will automatically select the right path.

---

### How to Allocate the Two Quota Pools

- **The `agy` pool** is best for running code, batch processing, and smaller images within pipelines. It is UI-free, supports switching models via `--model`, and runs headlessly.
- **The subscription pool** is reserved for Gemini-exclusive features: full-resolution image generation, Deep Research, Canvas, and Gems. Ultra uses a rolling 5-hour quota; the macOS app displays a progress bar under "設定 → 用量限制", while the Windows app does not.
- **Free Gemini API keys have an image model quota of 0** (always returns 429), making the subscription the only zero-additional-cost route for high-resolution image generation.
- Deep Research is slow and quota-heavy; by default, this package pauses at the research plan for human review, proceeding to the final report only when `--start` is passed.
- Every remote `ask / image / canvas / research` command leaves a thread in your Gemini chat history and notifies you upon completion.

---

### 30-Minute Setup

**1. Install agy and the file safety harness**

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/bingo-taiwan/agy-harness/main/setup-agy-harness.ps1 | iex"
```
Or clone and run:
```powershell
git clone https://github.com/bingo-taiwan/agy-harness.git
cd agy-harness
powershell -ExecutionPolicy Bypass -File .\setup-agy-harness.ps1
```

Linux / macOS (Bash):
```bash
git clone https://github.com/bingo-taiwan/agy-harness.git
cd agy-harness
bash setup-agy-harness.sh
```

**2. Extra step on macOS to allow remote agents to use this machine's `agy`** (Tested on mac mini, 2026-09-18)

After logging into `agy` via Mac GUI Terminal, the token is stored in the Keychain. Running `agy` over SSH keeps returning "請先登入" (log shows `falling back to file: exit status 36`; running `security unlock-keychain` first does not help because `agy` invokes the system `security` command to read Keychain, and headless SSH sessions cannot display the GUI prompt for "允許存取").
Solution: Open Terminal on the Mac and run `ssh <user>@localhost`, then run `agy` once inside that session. It writes the token to disk at `~/.gemini/antigravity-cli/antigravity-oauth-token` (permissions 600), after which running `agy -p` over SSH from any machine works seamlessly.

**3. Install Gemini Desktop and sign in with your subscription account**

`gemini-desktop/install.ps1` (Windows) or `gemini-desktop/install.sh` (macOS) downloads the official installer, installs it, and prompts you to sign in.
When signing in remotely via Remote Desktop, do not scan the "密碼金鑰" QR code if it appears (it relies on Bluetooth to locate nearby devices); click "Try another way" to authenticate with your password instead.
After signing in with an Ultra account, a Spark tab will appear at the top of the macOS app.

**4. Enable remote control**

```bash
export PYTHONIOENCODING=utf-8
G="uv run -q --with websocket-client python gemini-desktop/cdp/gemini.py"
$G launch            # Windows: relaunch Gemini Desktop with the debug port; macOS: open a separate-profile Chrome on gemini.google.com (sign in once by hand the first time)
$G doctor            # account, mode and key selectors all present = ready
$G image "prompt" --out-dir ./out            # full-size image saved to disk
$G ask "question" --file ./doc.pdf --out ./a.md   # Q&A over a file; --model flash-lite|flash|pro|thinking
$G canvas "spec" --out ./page.html           # Canvas writes a single-page app
$G research "topic"                          # Deep Research: pauses at the plan
$G research-start --conv <id> --out ./r.md    # run after the plan is approved
$G close                                      # always close the port when done
```

macOS details (lack of remote control endpoint in the app, why switching to the Chrome web version, and how to restore tabs after closing windows): [`gemini-desktop/mac/README.md`](gemini-desktop/mac/README.md) (zh-TW).
How to locate new elements when Gemini updates break selectors: [`gemini-desktop/cdp/selectors-and-traps.md`](gemini-desktop/cdp/selectors-and-traps.md) (zh-TW).

**5. Paste routing rules to your agent**

Paste `gemini-desktop/GEMINI.md.snippet` into `~/.gemini/GEMINI.md`, your project's `AGENTS.md`, or Claude Code's `CLAUDE.md`.

---

### File Safety Harness: No More `agy` Crashes from Binary Files

The installation script in Step 1 writes the following strict rules into `~/.gemini/GEMINI.md`, `~/AGENTS.md`, and `~/CLAUDE.md`:

| Storage / File Category | Matching Paths / Extensions | Automated Defense |
| :--- | :--- | :--- |
| **OneDrive Cloud Directories** | `OneDrive`, `OneDrive - 機構名稱` | Triggers Cloud Hydration download before execution, saving to local SSD at `C:\temp\` (Windows) or `/tmp/` (macOS) |
| **NAS / Network Drives** | `X:\`, `Y:\`, `Z:\`, UNC paths | Automatically copies to an ASCII-only short path, avoiding PowerShell escaping failures caused by spaces and Chinese characters |
| **PDF** | `.pdf` | Prohibits `view_file`. Extracts text directly via `pdf-inspector`; non-text pages fall back to Python / OCR |
| **Word** | `.docx`, `.doc` | Prohibits `view_file`. Use `python-docx` or PowerShell |
| **Excel** | `.xlsx`, `.xls`, `.csv` | Prohibits `view_file`. Use `pandas` / `openpyxl` or PowerShell |
| **PPT** | `.pptx`, `.ppt` | Prohibits `view_file`. Use `python-pptx` |
| **Images** | `.jpg`, `.png`, `.webp`, `.bmp` | Prohibits `view_file`. Inject via `@path` in command entry; call `generate_image` directly for multi-image composition |
| **Archives** | `.zip`, `.rar`, `.7z` | Prohibits `view_file`. Extract with `Expand-Archive` or Python |

Why block this: Calling `view_file` on non-plain-text files in `agy` triggers an API `400 INVALID_ARGUMENT` error due to unparseable inline byte data. Once a corrupted file entry is recorded in the session trajectory, every subsequent message (even a simple "HI") will continuously trigger 400 errors, bricking the session and forcing you to start a new one.

Windows also includes a wrapper `agy-safe.ps1`, which materializes OneDrive / NAS files locally before passing commands to `agy`:

```powershell
# Hydrate a PDF on OneDrive, then summarize it into a Word file
C:\Users\user\.gemini\bin\agy-safe.ps1 -p "請讀取 @'C:\Users\user\OneDrive - 學校\2026財報.pdf' 並自動整理成 C:\temp\摘要.docx"

# Analyze an Excel file on the NAS together with a OneDrive photo
C:\Users\user\.gemini\bin\agy-safe.ps1 -p "讀取 @'X:\專案\數據.xlsx' 與 OneDrive 圖片 @'C:\Users\user\OneDrive\圖片\活動照.jpg' 完成分析"
```

---

### Known Limitations and Security Notices

- **While the remote control port is open, any local process can operate this authenticated Google account.** Always run `close` when finished; never add `--remote-allow-origins=*`.
- Element selectors are based on **zh-TW UI strings**, so the Gemini interface language must be set to Traditional Chinese; for other languages, modify `SEL` at the top of `gemini.py`.
- Execute only one remote command at a time; do not run them in parallel.
- Do not use remote control for batch processing hundreds of images (it is slow and risks violating terms of service or triggering account risk controls); use the API for that volume.
- Spark scheduling / local MCPs have no agent interface; Computer Use is not yet available.

---

### Further Reading

- Differences between vanilla `agy` and adding this package, and when vanilla is sufficient: [`gemini-desktop/README.md` "跟只裝原生 agy 差在哪"](gemini-desktop/README.md#跟只裝原生-agy差在哪) (zh-TW)
- Windows CDP remote control, macOS reverse-engineering details, and speed vs. token comparisons across all three paths: [Gemini Desktop Hands-on Teardown Edition 3](https://notes.mynet.com.tw/tech/gemini-desktop-vs-agy-cli) (zh-TW)
- `AGENTS.md` template for helping agents automatically choose the right tool: [agent-md-starter](https://github.com/bingo-taiwan/agent-md-starter)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
