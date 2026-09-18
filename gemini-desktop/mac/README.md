# macOS 版 Gemini Desktop：agent 拿得到什麼、拿不到什麼

> 實測環境：macOS 15.6（Apple Silicon）、Gemini 1.113.6.866、台灣 Ultra 帳號，2026-09-16。
> 完整逆向與截圖：[Gemini Desktop 實機拆解第三版](https://notes.mynet.com.tw/tech/gemini-desktop-vs-agy-cli)。

## 一句話

Mac 版是原生 Swift app，**app 本身 agent 遙控不了**；但 Gemini 的網頁版功能相同，agent 改遙控 Chrome 開的 gemini.google.com 就好（下面「agent 怎麼遙控」）。app 給使用者的 agent 功能（Spark）則比 Windows 版多很多。

## 入口盤點（全部查過）

| 入口 | 有沒有 |
|------|--------|
| CDP（Windows 版用的那套） | 沒有，不是 Electron |
| AppleScript 字典 | 沒有 |
| App Intents / 捷徑 | 沒有 |
| URL scheme | 有 `googlegemini://newchat`、`googlegemini://conversation/<id>`，只能開畫面，不能帶提示字 |
| Accessibility UI 自動化 | 跟任何 Mac app 一樣可以，但要使用者在系統設定授權給終端機，且元件沒有穩定 id，改版就壞。本模組沒做 |

## agent 怎麼遙控：走 Chrome 網頁版（2026-09-18 michelle mac mini 實測）

Windows 版 Gemini Desktop 是 Electron 殼包 gemini.google.com，所以 `../windows/gemini.py` 在 macOS 上會自動切分支：
`launch` 用 `open -na "Google Chrome"` 帶 `--remote-debugging-port=9222` 和獨立 `--user-data-dir=~/gemini-cdp-profile` 開網頁版，
其餘 `doctor / ask / image / canvas / research / close` 指令與 Windows 完全相同。

```bash
cd <repo>/gemini-desktop/windows
G="uv run -q --with websocket-client python gemini.py"
$G launch    # 第一次：人在跳出的 Chrome 視窗登入 Google 帳號一次；之後 profile 記住
$G doctor    # account 有帳號、picker 不是 Flash-Lite 就緒
$G image "描述" --out-dir ./out
$G close     # 只殺遙控用的 Chrome 實例，使用者自己的 Chrome 不受影響
```

| 實測 | 結果 |
|------|------|
| `doctor` | selector 與 Windows 版全同，帳號 Ultra，模式 Pro |
| `ask` | 12 秒 |
| `image` | 29 秒落地 2816×1536 JPG |

坑：網頁版有 Trusted Types，設 `innerHTML` 會被擋（Electron 版沒有），腳本已改 `replaceChildren()`；
使用者關掉遙控視窗時 Chrome 行程還在但沒分頁，`curl -X PUT "http://127.0.0.1:9222/json/new?https://gemini.google.com/app"` 補一個即可。
遠端呼叫：`ssh <user>@<mac> 'cd <repo>/gemini-desktop/windows && uv run -q --with websocket-client python gemini.py ask "..." --out ~/a.md'`。

## Ultra 帳號登入後看得到的（Workspace 公司帳號沒有 Spark；Pro 未實測）

| 功能 | 在哪 |
|------|------|
| Spark 分頁 | 視窗上方切換 |
| 排程任務 | Spark → 排程；設定 → Gemini Spark 可開「讓 Mac 保持啟用」 |
| 技能（SKILL 上傳、`/` 套用） | Spark → 技能 |
| Obsidian · 本機、Git · 本機 MCP | Spark → 連結的應用程式 |
| 自訂 MCP（填 MCP 網址） | 同上，最底下「新增自訂應用程式」 |
| 本機資料夾存取 | Spark → 已連結的資料夾 → 新增 Mac 資料夾 |
| 手機遠端派工到這台 Mac | 設定 → Gemini Spark → 從其他裝置遠端執行任務 |
| Finder 右鍵「新增至 Gemini」 | 設定 → 擴充功能（要到系統設定啟用） |
| 額度進度條 | 設定 → 用量限制 |
| **電腦控制（Computer Use）** | **沒有**。程式裡有完整模組與 23 種動作，但設定頁沒有這一項 |

## 給導入的人

1. 先問對方帳號是消費者 Pro/Ultra 還是 Workspace。Workspace 連 Spark 都沒有。
2. 遠端桌面幫人登入時，跳出「密碼金鑰」QR code 不要掃（要藍牙近距離），按「Try another way」用密碼。
3. 開「新增 Mac 資料夾」與 Obsidian MCP 之前，先建一個空的測試資料夾，別直接掛整個家目錄。
4. agent 這邊：查資料 `gws`、無頭產圖 `agy`，要 Gemini 獨有的產圖 / Deep Research / Canvas 就用 `gemini.py` 遙控 Chrome 網頁版；只有 Spark 類功能由人在 app 做。規則片段在 `../GEMINI.md.snippet`。
