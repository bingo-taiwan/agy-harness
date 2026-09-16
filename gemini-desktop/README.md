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

## 已知限制

- `gemini.py` 的元件定位照 zh-TW 介面文字寫，介面語言不是繁體中文要改檔頭 `SEL`；Gemini 改版壞掉先跑 `doctor`。
- 遙控埠開著等於本機任何程式都能操作該 Google 帳號，用完必 `close`。
- 每個指令都會在使用者的對話紀錄留一則。
