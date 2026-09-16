# Selector 與踩坑紀錄

實測環境：2026-09-13，Gemini Desktop `app-1.10.4`（Electron / Chrome 152），帳號 UI 語言 zh-TW。
Gemini 改版後 selector 失效時，照「怎麼摸新 selector」重找，再更新 `scripts/gemini.py` 的 `SEL`。

## 已驗證的 selector

| 用途 | selector / 定位法 | 備註 |
|------|------------------|------|
| 輸入框 | `div.ql-editor[contenteditable=true]` | 送出：`Input.insertText` + Enter 鍵事件 |
| 生成中 | `button[aria-label="停止回覆"]` | 消失＝完成；送出後先等 3 秒再判斷，短回答可能一閃即逝 |
| 回答 | `model-response`，內文 `.markdown` | 直接讀 `model-response` 會多出「Gemini 說了」螢幕閱讀器前綴 |
| 使用者訊息 | `user-query .query-text-line` | 直接讀 `user-query` 會多「你說了」並重複一次文字 |
| 模型選單 | 按 `button[aria-label*="開啟模式挑選器"]`，選項 `gem-menu [role=menuitem]` | 模型選單**不在** `.cdk-overlay-container` 裡；選項首行如「3.8 Flash」，比對首行結尾避免 Flash 誤中 Flash-Lite |
| 工具選單 | 按 `button[aria-label="上傳與工具"]`，項目用「可見葉節點文字完全相符」點 | 除前兩項外沒有 role；子選單「更多工具」「更多上傳選項」要再點一次並等約 1.2 秒動畫 |
| 新對話 | `[aria-label="新對話"]` | 是 `<a>` 不是 button；腳本直接 `Page.navigate` 到 `/app` 較穩 |
| 側欄對話 | `a[href^="/app/"]` | 側欄收合時不在 DOM，要先點 `button[aria-label="開啟側欄"]` |
| Gem | 導到 `/gems/view`，卡片 `a[href^="/gem/"]` | 開 Gem 對話：導到 `/gem/<slug>` |
| 附件 | `Input.dispatchDragEvent` dragEnter→dragOver→drop 到輸入框中心 | `data` 必須含 `dragOperationsMask`；成功後出現 `.file-preview-chip` |
| 圖片下載 | 回應內 `button[aria-label="下載原尺寸圖片"]` | 見下方下載坑 |
| Canvas 原始碼 | 點「程式碼」分頁，`window.monaco.editor.getModels().at(-1).getValue()` | `.view-lines` 只有畫面可見行，長檔會截斷，只當備援；預覽分頁是跨網域 iframe 讀不到 |
| Deep Research 開始 | `deep-research-confirmation-widget button` 中文字含「開始/开始」者 | 按鈕文字時繁時簡，不要比對完整文字 |

## 踩過的坑

1. **單例鎖**：Gemini 已在跑時再開一個帶參數的 Gemini.exe，參數被丟掉、埠不會開。一定先 `taskkill /F /IM Gemini.exe`。
2. **Playwright 卡死**：`connect_over_cdp` 與 `@playwright/mcp --cdp-endpoint` 都在 attach 後 30–180 秒逾時。推測是 Electron 的 `app://bundle/...` 內部頁面。改用原生 WebSocket 直連 `/json/list` 裡 `gemini.google.com` 那個 page 目標，並加 `suppress_origin=True`。
3. **下載導向會被還原**：`Browser.setDownloadBehavior` 綁在發出它的那條 browser WebSocket 上，連線一關 Chrome 就還原成預設行為，檔案不會落地到指定目錄。要撐到檔案下載完成才關連線。
4. **產圖的 img 是 blob: URL**：在頁面裡 `fetch(img.src)` 會 `Failed to fetch`；canvas 轉 dataURL 只拿到 1024 寬預覽。原尺寸只能點「下載原尺寸圖片」。
5. **導航會毀掉 JS context**：`Page.navigate` 後舊的 evaluate 會失敗；腳本在 `js()` 內偵測後重連一次。
6. **原生檔案選擇視窗攔不到**：點工具選單「上傳檔案」後等不到 `Page.fileChooserOpened`，Electron 的原生對話框繞過了這個事件。上傳一律用拖放。
7. **Windows 主控台編碼**：Python 印中文到 cp950 主控台會 `UnicodeEncodeError`，要 `PYTHONIOENCODING=utf-8`。
8. **JS 字串裡的換行**：在 Python f-string 裡寫 `'\n'` 會變成真的換行字元送進 JS，造成 `SyntaxError: Invalid or unexpected token`。用 `String.fromCharCode(10)`。
9. **app 內沒有額度顯示**：左下只顯示方案名稱「Ultra」；帳戶連結會開外部瀏覽器，CDP 攔不到。

## 怎麼摸新 selector

1. `launch` 後用 `shot` 截圖確認畫面狀態。
2. 用一次性小腳本 `from gemini import Gemini; g=Gemini(); print(g.js("..."))`，列出候選元素：
   - 有 aria-label 的按鈕：`[...document.querySelectorAll('button[aria-label],a[aria-label]')].map(b=>b.getAttribute('aria-label'))`
   - 自訂元件標籤（Angular 元件名通常最穩）：`[...new Set([...document.querySelectorAll('model-response *')].map(e=>e.tagName).filter(t=>t.includes('-')))]`
   - 有 role 的選單項：`[...document.querySelectorAll('[role]')].map(x=>[x.tagName,x.getAttribute('role'),x.innerText.slice(0,40)])`
3. 優先順序：自訂元件標籤 ＞ aria-label ＞ 可見文字。文字會隨語系或繁簡切換而變。
