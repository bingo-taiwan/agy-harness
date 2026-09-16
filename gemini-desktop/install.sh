#!/bin/bash
# gemini-desktop/install.sh — macOS：裝 Gemini Desktop（原生 Swift app），並說明 agent 能拿到什麼
# 用法：bash gemini-desktop/install.sh
# ponytail: Mac 版沒有 CDP、沒有 AppleScript 字典，agent 無法遙控它；這支只負責裝好＋講清楚該用哪條路。
set -euo pipefail
DMG_URL="https://gemini.google/download/mac/"     # 302 → dl.google.com/release2/.../Gemini.dmg
APP="/Applications/Gemini.app"

if [ -d "$APP" ]; then
  echo "[ok] 已安裝：$APP $(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP/Contents/Info.plist" 2>/dev/null)"
else
  TMP=$(mktemp -d); DMG="$TMP/Gemini.dmg"
  echo "[..] 下載官方 dmg → $DMG"
  curl -sL -o "$DMG" "$DMG_URL"
  [ "$(stat -f %z "$DMG")" -gt 1000000 ] || { echo "下載的檔案太小，可能不是 dmg"; exit 1; }
  MNT="$TMP/mnt"; hdiutil attach -nobrowse -readonly -mountpoint "$MNT" "$DMG" >/dev/null
  SRC=$(ls -d "$MNT"/*.app | head -1)
  ditto "$SRC" "$APP"
  hdiutil detach "$MNT" -quiet
  spctl -a -vv "$APP" 2>&1 | grep -q "Google LLC" && echo "[ok] 公證簽章：Google LLC" || echo "[!!] 簽章檢查沒通過，先別開"
  echo "[ok] 已安裝：$APP"
fi

open -a "$APP"
cat <<'EOF'

==> 接下來是人要做的：
  1. 在 Gemini 視窗登入 Google 帳號。遠端桌面操作時若跳出「密碼金鑰」QR code，不要掃（它靠藍牙找旁邊的電腦），
     按「Try another way」改用密碼。
  2. Ultra 帳號登入後上方會出現「Spark」分頁：排程、技能、連結的應用程式（含 Obsidian·本機 / Git·本機 MCP、自訂 MCP）、
     新增 Mac 資料夾。Workspace 公司帳號沒有 Spark。Pro 帳號未實測。
  3. 電腦控制（Computer Use）目前沒開放給任何帳號，設定裡看不到；系統會要 Accessibility 權限但沒有對應功能。

==> agent 怎麼用它：Mac 版沒有遙控入口。查資料用 gws CLI，無頭產圖或問模型用 agy，
    要 Gemini app 獨有的 Deep Research / Nano Banana / Spark 就由人在 Gemini 視窗操作。
    細節見 gemini-desktop/mac/README.md。
EOF
