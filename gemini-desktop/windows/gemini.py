"""gemini-desktop-cdp: 用原生 CDP 遙控本機 Gemini Desktop（Windows Electron app）。

執行：PYTHONIOENCODING=utf-8 uv run --with websocket-client python gemini.py <子命令> ...
每個子命令在 stdout 印一個 JSON（ok=true/false），錯誤時 exit 1 並在 --debug-dir 留截圖。
selector 全部集中在 SEL，Gemini 改版壞掉先跑 `doctor` 看哪個失效。
設計借鑑 blessleon/electron-cdp-automation（MIT）：導航後自動重連、以可見文字找元素、輪詢而非等 load 事件。
"""
import argparse, base64, glob, json, os, pathlib, re, subprocess, sys, time, urllib.request

PORT = 9222
BASE = "https://gemini.google.com"
SEL = {  # 2026-09-13 實測，Gemini Desktop app-1.10.4，UI zh-TW
    "editor": "div.ql-editor[contenteditable=true]",
    "stop": 'button[aria-label="停止回覆"]',
    "picker": 'button[aria-label*="開啟模式挑選器"]',
    "tools": 'button[aria-label="上傳與工具"]',
    "new_chat": '[aria-label="新對話"]',  # 是 <a> 不是 button
    "open_sidebar": 'button[aria-label="開啟側欄"]',  # 側欄收合時才存在；收合時對話清單不在 DOM
    "response": "model-response",
    "query": "user-query",
    "chip": ".file-preview-chip",
    "history": 'a[href^="/app/"]',
    "gem_card": 'a[href^="/gem/"]',
    "download_img": 'button[aria-label="下載原尺寸圖片"]',
    "monaco": ".view-lines",
}
# Deep Research 確認按鈕：文字時繁時簡（開始研究/开始研究），用元件標籤定位最穩
START_BTN = "[...document.querySelectorAll('deep-research-confirmation-widget button')].find(b=>!b.disabled&&/開始|开始/.test(b.innerText))"  # 已完成的研究會留一顆停用的舊按鈕
MODELS = {"flash-lite": "Flash-Lite", "flash": "Flash", "pro": "Pro", "thinking": "延伸思考"}


def out(obj, code=0):
    print(json.dumps(obj, ensure_ascii=False, indent=1))
    sys.exit(code)


def http_json(path, timeout=2):
    return json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}{path}", timeout=timeout))


def port_open():
    try:
        http_json("/json/version"); return True
    except Exception:
        return False


def gemini_running():
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Gemini.exe", "/NH"], capture_output=True, text=True)
    return "Gemini.exe" in r.stdout


def find_exe():
    exes = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Google\Gemini\app-*\Gemini.exe"))
    if not exes:
        raise RuntimeError("找不到 Gemini.exe（%LOCALAPPDATA%\\Google\\Gemini\\app-*）")
    ver = lambda p: [int(x) for x in re.findall(r"app-([\d.]+)", p)[0].split(".")]
    return max(exes, key=ver)


class Gemini:
    def __init__(self, debug_dir=None):
        from websocket import create_connection  # 延後 import，launch/close 不需要
        self._create = create_connection
        self.debug_dir = pathlib.Path(debug_dir) if debug_dir else None
        self._id = 0
        self.connect()

    def connect(self):
        t0 = time.time()
        while True:
            try:
                t = next(t for t in http_json("/json/list") if t.get("type") == "page" and t["url"].startswith(BASE))
                break
            except Exception:
                if time.time() - t0 > 30:
                    raise RuntimeError("找不到 gemini.google.com 頁面目標；先跑 launch")
                time.sleep(1)
        self.ws = self._create(t["webSocketDebuggerUrl"], suppress_origin=True, timeout=120)

    def cdp(self, method, **params):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self._id:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})

    def js(self, expr, await_=False, _retry=True):
        try:
            r = self.cdp("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=await_)
        except Exception as e:  # 導航會毀掉 context / websocket，重連一次
            if _retry and re.search(r"context|detached|closed|Connection", str(e), re.I):
                time.sleep(1); self.connect(); return self.js(expr, await_, False)
            raise
        if "exceptionDetails" in r:
            d = r["exceptionDetails"]
            msg = d.get("exception", {}).get("description") or d.get("text")
            if _retry and re.search(r"context", msg or "", re.I):
                time.sleep(1); self.connect(); return self.js(expr, await_, False)
            raise RuntimeError(f"JS 錯誤: {msg}")
        return r.get("result", {}).get("value")

    def shot(self, path):
        pathlib.Path(path).write_bytes(base64.b64decode(self.cdp("Page.captureScreenshot", format="png")["data"]))

    def debug_shot(self, name):
        if self.debug_dir:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            p = self.debug_dir / f"{time.strftime('%H%M%S')}-{name}.png"
            try: self.shot(p); return str(p)
            except Exception: pass

    # ---------- 基本動作 ----------
    def wait_for(self, expr, timeout, what, interval=0.8):
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                v = self.js(expr)
                if v: return v
            except RuntimeError:
                pass
            time.sleep(interval)
        raise RuntimeError(f"等待逾時（{timeout}s）：{what}")

    def visible(self, sel):
        return f"(()=>{{const e=document.querySelector({json.dumps(sel)});if(!e)return false;const r=e.getBoundingClientRect();return r.width>0&&r.height>0}})()"

    def goto(self, url):
        self.cdp("Page.navigate", url=url)
        time.sleep(2); self.connect()
        self.wait_for(self.visible(SEL["editor"]) if "/gems/view" not in url else "true", 60, f"頁面就緒 {url}")
        time.sleep(1.5)

    def click_text(self, text, timeout=8):
        """點可見、文字完全相符的葉節點（選單項多半沒有 role/aria-label）。"""
        expr = f"""(()=>{{const want={json.dumps(text)};
          const el=[...document.querySelectorAll('*')].find(x=>x.children.length===0&&x.textContent.trim()===want&&(()=>{{const r=x.getBoundingClientRect();return r.width>0&&r.height>0}})());
          if(!el)return false; (el.closest('button,[role=menuitem],a')||el).click(); return true;}})()"""
        self.wait_for(expr, timeout, f"找不到可點的文字「{text}」")
        time.sleep(1.2)

    def select_model(self, key):
        label = MODELS[key]
        self.js(f"document.querySelector({json.dumps(SEL['picker'])}).click()"); time.sleep(1.2)
        # 選項首行像「3.8 Flash」「3.5 Flash-Lite」，用首行結尾比對避免 Flash 誤中 Flash-Lite
        expr = f"""(()=>{{const want={json.dumps(label)};
          const items=[...document.querySelectorAll('[role^=menuitem]')];  // 模型選單是 gem-menu，不在 cdk overlay 裡
          const el=items.find(x=>{{const l=(x.innerText||'').trim().split('\\n')[0].trim();return l===want||l.endsWith(' '+want)}});
          if(!el)return false; el.click(); return true;}})()"""
        self.wait_for(expr, 8, f"模型選單找不到「{label}」")
        time.sleep(1.2)
        return self.js(f"document.querySelector({json.dumps(SEL['picker'])})?.getAttribute('aria-label')")

    def select_tool(self, path):
        """path 例：'Canvas'、'建立圖像'、'更多工具>Deep Research'。"""
        self.js(f"document.querySelector({json.dumps(SEL['tools'])}).click()"); time.sleep(1.2)
        for name in [p.strip() for p in path.split(">")]:
            self.click_text(name)

    def attach(self, files):
        for f in files:
            p = str(pathlib.Path(f).resolve())
            if not os.path.isfile(p):
                raise RuntimeError(f"附件不存在：{p}")
            n0 = self.js(f"document.querySelectorAll({json.dumps(SEL['chip'])}).length") or 0
            x, y = self.js(f"(()=>{{const b=document.querySelector({json.dumps(SEL['editor'])}).getBoundingClientRect();return [b.x+b.width/2,b.y+b.height/2]}})()")
            data = {"items": [{"mimeType": "Files", "data": ""}], "files": [p], "dragOperationsMask": 1}
            for typ in ("dragEnter", "dragOver", "drop"):
                self.cdp("Input.dispatchDragEvent", type=typ, x=x, y=y, data=data)
            self.wait_for(f"document.querySelectorAll({json.dumps(SEL['chip'])}).length>{n0}", 60, f"附件預覽未出現：{p}")
            time.sleep(3)  # 等上傳完成（chip 出現到可送出之間有延遲）

    def send(self, prompt):
        n0 = self.js(f"document.querySelectorAll({json.dumps(SEL['response'])}).length") or 0
        self.js(f"(()=>{{const e=document.querySelector({json.dumps(SEL['editor'])});e.focus();e.innerHTML='';}})()")
        self.cdp("Input.insertText", text=prompt); time.sleep(0.6)
        for typ in ("keyDown", "keyUp"):
            self.cdp("Input.dispatchKeyEvent", type=typ, key="Enter", code="Enter", windowsVirtualKeyCode=13, nativeVirtualKeyCode=13)
        return n0

    def wait_done(self, n0, timeout=300, stable_polls=3, interval=1.5):
        """完成 = 回應數增加 + 「停止回覆」按鈕消失 + 最後一則 HTML 長度連續不變。"""
        time.sleep(3)
        t0, last, stable = time.time(), -1, 0
        probe = f"""JSON.stringify({{n:document.querySelectorAll({json.dumps(SEL['response'])}).length,
          stop:!!document.querySelector({json.dumps(SEL['stop'])}),
          len:([...document.querySelectorAll({json.dumps(SEL['response'])})].at(-1)?.outerHTML||'').length}})"""
        while time.time() - t0 < timeout:
            s = json.loads(self.js(probe))
            if s["n"] > n0 and not s["stop"]:
                stable = stable + 1 if s["len"] == last else 0
                if stable >= stable_polls: return round(time.time() - t0 + 3)
            else:
                stable = 0
            last = s["len"]; time.sleep(interval)
        raise RuntimeError(f"回答逾時（{timeout}s）")

    def last_response(self, html=False):
        prop = "outerHTML" if html else "innerText"
        # 優先讀 .markdown 內文，避開螢幕閱讀器前綴「Gemini 說了」
        return self.js(f"(()=>{{const r=[...document.querySelectorAll({json.dumps(SEL['response'])})].at(-1);if(!r)return '';const m=r.querySelector('.markdown');return (m||r).{prop}||''}})()")

    def download_from_last(self, out_dir, aria_contains="下載", timeout=180):
        """點最後一則回應裡所有 aria-label 含「下載」的按鈕，等檔案落地。"""
        d = pathlib.Path(out_dir).resolve(); d.mkdir(parents=True, exist_ok=True)
        # 下載導向綁在這條 browser 連線上，連線一斷 Chrome 就還原設定，所以要撐到檔案落地才關
        bws = self._create(http_json("/json/version")["webSocketDebuggerUrl"], suppress_origin=True, timeout=30)
        bws.send(json.dumps({"id": 1, "method": "Browser.setDownloadBehavior", "params": {"behavior": "allow", "downloadPath": str(d)}}))
        bws.recv()
        try:
            return self._click_downloads(d, aria_contains, timeout)
        finally:
            bws.close()

    def _click_downloads(self, d, aria_contains, timeout):
        before = {p.name for p in d.iterdir()}
        n = self.js(f"""(()=>{{const r=[...document.querySelectorAll({json.dumps(SEL['response'])})].at(-1);
          const bs=[...r.querySelectorAll('button[aria-label]')].filter(b=>b.getAttribute('aria-label').includes({json.dumps(aria_contains)}));
          bs.forEach((b,i)=>setTimeout(()=>b.click(), i*2500)); return bs.length;}})()""")
        if not n:
            return []
        t0 = time.time()
        while time.time() - t0 < timeout:
            new = [p for p in d.iterdir() if p.name not in before]
            if len(new) >= n and not any(p.suffix == ".crdownload" for p in new):
                return [str(p) for p in sorted(new)]
            time.sleep(2)
        raise RuntimeError(f"下載逾時：預期 {n} 個檔，實得 {len([p for p in d.iterdir() if p.name not in before])}")

    def prepare(self, a):
        """依參數開好對話：--conv 接續既有、--gem 開 Gem、--continue 沿用目前頁、否則新對話。"""
        if getattr(a, "conv", None): self.goto(f"{BASE}/app/{a.conv}")
        elif getattr(a, "gem", None): self.goto(f"{BASE}/gem/{a.gem}")
        elif not getattr(a, "cont", False): self.goto(f"{BASE}/app")
        else: self.wait_for(self.visible(SEL["editor"]), 30, "輸入框")
        info = {}
        if getattr(a, "model", None): info["model"] = self.select_model(a.model)
        if getattr(a, "tool", None): self.select_tool(a.tool); info["tool"] = a.tool
        if getattr(a, "file", None): self.attach(a.file); info["files"] = a.file
        return info

    def ensure_sidebar(self):
        if not self.js(f"document.querySelectorAll({json.dumps(SEL['history'])}).length"):
            self.js(f"document.querySelector({json.dumps(SEL['open_sidebar'])})?.click()")
            time.sleep(2)

    def conv_id(self):
        m = re.search(r"/app/([0-9a-f]+)", self.js("location.pathname") or "")
        return m.group(1) if m else None


# ---------- 子命令 ----------
def cmd_launch(a):
    if port_open():
        out({"ok": True, "status": "already_open"})
    if gemini_running() and not a.restart:
        out({"ok": False, "error": "Gemini 正在執行但沒開遙控埠。加 --restart 會強制關閉重開（使用者正在進行的對話畫面會被打斷）"}, 1)
    subprocess.run(["taskkill", "/F", "/IM", "Gemini.exe"], capture_output=True)
    time.sleep(2)
    exe = find_exe()
    # 單例鎖：舊行程沒死光時參數會被丟掉，所以上面先 taskkill
    subprocess.Popen([exe, f"--remote-debugging-port={PORT}"], creationflags=0x00000008 | 0x00000200, close_fds=True)
    t0 = time.time()
    while not port_open():
        if time.time() - t0 > 40: out({"ok": False, "error": "遙控埠 40 秒內沒起來"}, 1)
        time.sleep(1)
    g = Gemini()
    g.wait_for(g.visible(SEL["editor"]), 90, "Gemini 頁面載入（可能未登入）")
    out({"ok": True, "status": "launched", "exe": exe, "seconds": round(time.time() - t0)})


def cmd_close(a):
    subprocess.run(["taskkill", "/F", "/IM", "Gemini.exe"], capture_output=True)
    time.sleep(2)
    if a.reopen:  # 以一般模式重開（沒有遙控埠）
        subprocess.Popen([find_exe()], creationflags=0x00000008 | 0x00000200, close_fds=True)
        time.sleep(3)
    out({"ok": not port_open(), "port_closed": not port_open(), "reopened": a.reopen})


def cmd_doctor(a):
    g = Gemini(a.debug_dir)
    g.goto(f"{BASE}/app")
    g.ensure_sidebar()
    checks = {k: bool(g.js(f"!!document.querySelector({json.dumps(v)})")) for k, v in SEL.items()
              if k in ("editor", "picker", "tools", "new_chat", "history")}
    acct = g.js("(()=>{const a=document.querySelector('a[aria-label*=\"Google 帳戶\"]');return a?a.getAttribute('aria-label').replace(/\\s+/g,' '):null})()")
    checks["account_found"] = bool(acct)
    out({"ok": all(checks.values()), "checks": checks, "account": acct, "picker_label": g.js(f"document.querySelector({json.dumps(SEL['picker'])})?.getAttribute('aria-label')")},
        0 if all(checks.values()) else 1)


def cmd_tools(a):
    g = Gemini(a.debug_dir); g.goto(f"{BASE}/app")
    leaf = "[...document.querySelectorAll('.cdk-overlay-container *')].filter(x=>x.children.length===0&&x.textContent.trim()&&x.getBoundingClientRect().width>0).map(x=>x.textContent.trim())"
    g.js(f"document.querySelector({json.dumps(SEL['tools'])}).click()"); time.sleep(1.5)
    top = g.js(leaf)
    subs = {}
    for parent in ("更多工具", "更多上傳選項"):
        if parent in (top or []):
            g.click_text(parent); subs[parent] = [x for x in g.js(leaf) if x not in top]
            g.js(f"document.querySelector({json.dumps(SEL['tools'])}).click()"); time.sleep(0.8)
            g.js(f"document.querySelector({json.dumps(SEL['tools'])}).click()"); time.sleep(1.2)
    g.cdp("Input.dispatchKeyEvent", type="keyDown", key="Escape", code="Escape", windowsVirtualKeyCode=27)
    g.js(f"document.querySelector({json.dumps(SEL['picker'])}).click()"); time.sleep(1.2)
    models = g.js("[...document.querySelectorAll('gem-menu [role^=menuitem]')].map(x=>x.innerText.trim().split(String.fromCharCode(10)).join(' | '))")
    g.cdp("Input.dispatchKeyEvent", type="keyDown", key="Escape", code="Escape", windowsVirtualKeyCode=27)
    out({"ok": True, "tools": top, "submenus": subs, "models": models})


def cmd_ask(a):
    g = Gemini(a.debug_dir)
    info = g.prepare(a)
    n0 = g.send(a.prompt)
    secs = g.wait_done(n0, timeout=a.timeout)
    text = g.last_response()
    res = {"ok": True, **info, "seconds": secs, "conversation_id": g.conv_id(), "chars": len(text)}
    if a.download:
        res["downloads"] = g.download_from_last(a.download)
    if a.out:
        pathlib.Path(a.out).write_text(g.last_response(html=True) if a.html else text, encoding="utf-8")
        res["saved"] = str(pathlib.Path(a.out).resolve())
    else:
        res["text"] = text
    out(res)


def cmd_image(a):
    g = Gemini(a.debug_dir)
    info = g.prepare(a)
    n0 = g.send(a.prompt)
    secs = g.wait_done(n0, timeout=a.timeout)
    imgs = f"[...document.querySelectorAll({json.dumps(SEL['response'])})].at(-1).querySelectorAll('img')"
    g.wait_for(f"[...{imgs}].filter(i=>i.naturalWidth>=256).length", 60, "回應裡沒有圖片（可能被拒絕或只回了文字）")
    time.sleep(2)
    files = g.download_from_last(a.out_dir, aria_contains="下載原尺寸")
    out({"ok": True, **info, "seconds": secs, "conversation_id": g.conv_id(), "files": files, "text": g.last_response()[:500]})


def cmd_canvas(a):
    a.tool = "Canvas"
    g = Gemini(a.debug_dir)
    info = g.prepare(a)
    n0 = g.send(a.prompt)
    secs = g.wait_done(n0, timeout=a.timeout)
    g.click_text("程式碼", timeout=20); time.sleep(1.5)
    # Monaco 會虛擬化只畫可見行；先試 monaco model API，拿不到才讀畫面上的行
    code = g.js("(()=>{try{const m=window.monaco?.editor?.getModels?.();if(m&&m.length)return m.at(-1).getValue()}catch(e){}return null})()")
    source = "monaco_model"
    if not code:
        code = g.js(f"document.querySelector({json.dumps(SEL['monaco'])})?.innerText") or ""
        source = "view_lines（長檔可能只抓到畫面可見部分）"
    res = {"ok": bool(code), **info, "seconds": secs, "conversation_id": g.conv_id(), "chars": len(code), "source": source}
    if a.out:
        pathlib.Path(a.out).write_text(code, encoding="utf-8"); res["saved"] = str(pathlib.Path(a.out).resolve())
    else:
        res["code"] = code
    out(res, 0 if code else 1)


def cmd_research(a):
    a.tool = "更多工具>Deep Research"
    g = Gemini(a.debug_dir)
    info = g.prepare(a)
    g.send(a.prompt)
    btn = START_BTN
    g.wait_for(f"!!{btn}", 180, "研究計畫（「開始研究」按鈕）")
    plan = g.last_response()
    res = {"ok": True, **info, "conversation_id": g.conv_id(), "plan": plan}
    if not a.start:
        res["next"] = f"確認計畫後執行：research-start --conv {g.conv_id()}"
        out(res)
    n0 = g.js(f"document.querySelectorAll({json.dumps(SEL['response'])}).length")
    g.js(f"{btn}.click()")
    res.update(_wait_report(g, n0, a))
    out(res)


def _wait_report(g, n0, a):
    # Deep Research 要數分鐘（實測約 9.5 分鐘）；以「停止回覆」消失 + 長時間穩定判斷完成（間隔 15 秒、連續 4 次不變）
    secs = g.wait_done(n0 - 1, timeout=a.timeout, stable_polls=4, interval=15)
    r = {"seconds": secs, **_read_report(g)}
    report = r.pop("report")
    if a.out:
        pathlib.Path(a.out).write_text(report, encoding="utf-8"); r["saved"] = str(pathlib.Path(a.out).resolve())
    else:
        r["report"] = report
    return r


def _read_report(g):
    """報告在 deep-research-immersive-panel 裡；聊天區那則只是「研究完成」通知。面板沒開就點研究卡片。"""
    if not g.js("!!document.querySelector('deep-research-immersive-panel message-content')"):
        g.js("[...document.querySelectorAll('immersive-entry-chip')].at(-1)?.click()")
        g.wait_for("!!document.querySelector('deep-research-immersive-panel message-content')", 30, "研究報告面板")
        time.sleep(2)
    d = json.loads(g.js("""JSON.stringify((()=>{const p=document.querySelector('deep-research-immersive-panel');
      const body=p.querySelector('message-content').innerText;
      const seen=new Set(), src=[];
      for (const a of p.querySelectorAll('deep-research-source-lists a[href^="http"]')) {
        if (seen.has(a.href)) continue; seen.add(a.href);
        const ls=(a.innerText||'').trim().split(String.fromCharCode(10)).map(x=>x.trim()).filter(Boolean); src.push({t:ls.length>1?ls[1]+'（'+ls[0]+'）':ls[0], h:a.href});
      }
      return {body, src};})())"""))
    sources = [f"- [{x['t'] or x['h']}]({x['h']})" for x in d["src"]]
    md = d["body"].strip() + "\n\n## 資料來源\n\n" + "\n".join(sources)
    return {"report": md, "report_chars": len(d["body"]), "sources": len(d["src"])}


def cmd_research_start(a):
    g = Gemini(a.debug_dir)
    g.goto(f"{BASE}/app/{a.conv}")
    btn = START_BTN
    if not g.js(f"!!{btn}"):  # 已經跑完的研究：直接讀報告
        time.sleep(3)
        if g.js("!!document.querySelector('immersive-entry-chip, deep-research-immersive-panel')"):
            r = _read_report(g); report = r.pop("report")
            if a.out: pathlib.Path(a.out).write_text(report, encoding="utf-8"); r["saved"] = str(pathlib.Path(a.out).resolve())
            else: r["report"] = report
            out({"ok": True, "conversation_id": a.conv, "already_done": True, **r})
    g.wait_for(f"!!{btn}", 30, "這個對話沒有待開始的研究計畫，也沒有已完成的報告")
    n0 = g.js(f"document.querySelectorAll({json.dumps(SEL['response'])}).length")
    g.js(f"{btn}.click()")
    out({"ok": True, "conversation_id": a.conv, **_wait_report(g, n0, a)})


def cmd_history(a):
    g = Gemini(a.debug_dir)
    if not (g.js("location.href") or "").startswith(f"{BASE}/app"): g.goto(f"{BASE}/app")
    g.ensure_sidebar()
    g.wait_for(f"document.querySelectorAll({json.dumps(SEL['history'])}).length", 30, "側欄對話清單")
    items = g.js(f"[...document.querySelectorAll({json.dumps(SEL['history'])})].map(x=>({{id:x.getAttribute('href').split('/').pop(),title:x.innerText.trim()}})).filter(x=>x.title)")
    out({"ok": True, "count": len(items), "conversations": items[: a.limit]})


def cmd_open(a):
    g = Gemini(a.debug_dir)
    g.goto(f"{BASE}/app/{a.conv}")
    g.wait_for(f"document.querySelectorAll({json.dumps(SEL['response'])}).length", 30, "對話內容")
    time.sleep(2)
    turns = g.js(f"""[...document.querySelectorAll({json.dumps(SEL['query'] + ',' + SEL['response'])})].map(e=>{{
      const u=e.tagName.toLowerCase()==='user-query';
      const t=u?[...e.querySelectorAll('.query-text-line')].map(x=>x.innerText).join(String.fromCharCode(10)):(e.querySelector('.markdown')||e).innerText;
      return {{role:u?'user':'gemini',text:(t||e.innerText).trim()}};}})""")
    res = {"ok": True, "conversation_id": a.conv, "turns": len(turns)}
    if a.out:
        md = "\n\n".join(f"## {t['role']}\n\n{t['text']}" for t in turns)
        pathlib.Path(a.out).write_text(md, encoding="utf-8"); res["saved"] = str(pathlib.Path(a.out).resolve())
    else:
        res["content"] = turns
    out(res)


def cmd_gems(a):
    g = Gemini(a.debug_dir)
    g.goto(f"{BASE}/gems/view")
    g.wait_for(f"document.querySelectorAll({json.dumps(SEL['gem_card'])}).length", 30, "Gem 卡片")
    gems = g.js(f"[...new Map([...document.querySelectorAll({json.dumps(SEL['gem_card'])})].map(x=>[x.getAttribute('href'),x.innerText.trim().split('\\n')[0]])).entries()].map(([h,t])=>({{slug:h.replace('/gem/',''),title:t}}))")
    out({"ok": True, "gems": gems})


def cmd_shot(a):
    g = Gemini(a.debug_dir); g.shot(a.path)
    out({"ok": True, "saved": str(pathlib.Path(a.path).resolve()), "url": g.js("location.href")})


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="遙控 Gemini Desktop（CDP）")
    p.add_argument("--debug-dir", default=os.path.join(os.environ.get("TEMP", "."), "gemini-cdp-debug"), help="失敗時截圖存放處")
    sp = p.add_subparsers(dest="cmd", required=True)

    def conv_opts(s, tool=True):
        s.add_argument("prompt")
        s.add_argument("--model", choices=list(MODELS))
        s.add_argument("--file", action="append", help="附件，可重複")
        s.add_argument("--gem", help="在指定 Gem 裡問（slug，見 gems）")
        s.add_argument("--conv", help="接續既有對話 id（見 history）")
        s.add_argument("--continue", dest="cont", action="store_true", help="沿用目前頁面的對話")
        if tool: s.add_argument("--tool", help="工具路徑，例：'建立影片'、'更多工具>引導式學習'")
        s.add_argument("--timeout", type=int, default=300)

    s = sp.add_parser("launch"); s.add_argument("--restart", action="store_true"); s.set_defaults(f=cmd_launch)
    s = sp.add_parser("close"); s.add_argument("--reopen", action="store_true", help="關掉後以一般模式重開"); s.set_defaults(f=cmd_close)
    sp.add_parser("doctor").set_defaults(f=cmd_doctor)
    sp.add_parser("tools").set_defaults(f=cmd_tools)
    s = sp.add_parser("ask"); conv_opts(s)
    s.add_argument("--out", help="回答存檔（避免大段文字進 context）"); s.add_argument("--html", action="store_true")
    s.add_argument("--download", metavar="DIR", help="把最後一則回應裡所有「下載」按鈕的檔案抓到 DIR（影片/音樂等）")
    s.set_defaults(f=cmd_ask)
    s = sp.add_parser("image"); conv_opts(s); s.add_argument("--out-dir", required=True); s.set_defaults(f=cmd_image)
    s = sp.add_parser("canvas"); conv_opts(s, tool=False); s.add_argument("--out"); s.set_defaults(f=cmd_canvas)
    s = sp.add_parser("research"); conv_opts(s, tool=False)
    s.add_argument("--start", action="store_true", help="不停在計畫，直接開始研究並等報告")
    s.add_argument("--out"); s.set_defaults(f=cmd_research, timeout=1800)
    s = sp.add_parser("research-start"); s.add_argument("--conv", required=True); s.add_argument("--out")
    s.add_argument("--timeout", type=int, default=1800); s.set_defaults(f=cmd_research_start)
    s = sp.add_parser("history"); s.add_argument("--limit", type=int, default=30); s.set_defaults(f=cmd_history)
    s = sp.add_parser("open"); s.add_argument("conv"); s.add_argument("--out"); s.set_defaults(f=cmd_open)
    sp.add_parser("gems").set_defaults(f=cmd_gems)
    s = sp.add_parser("shot"); s.add_argument("path"); s.set_defaults(f=cmd_shot)

    a = p.parse_args()
    if a.cmd not in ("launch", "close") and not port_open():
        out({"ok": False, "error": "遙控埠沒開。先跑：gemini.py launch（Gemini 已開著則加 --restart）"}, 1)
    try:
        a.f(a)
    except SystemExit:
        raise
    except Exception as e:
        shot = None
        try: shot = Gemini(a.debug_dir).debug_shot(a.cmd)
        except Exception: pass
        out({"ok": False, "error": str(e), "debug_screenshot": shot}, 1)


if __name__ == "__main__":
    main()
