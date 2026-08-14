import requests
import time
import threading
from flask import Flask
import os
import sys

app = Flask('')

@app.route('/')
def home():
    return "MSW Fashion Monitor ULTRA is Running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# --- 設定區域 ---
# 💡 萬用保底：直接把已知玩家的 5碼 ID (profileCode) 寫進去，就不用冒險去戳第一個 API 了！
PLAYER_MAP = {
    "20372100000209378": {"name": "PAKA", "pcode": "o4PjG"},
    "20372100001023713": {"name": "Majajaja", "pcode": "AqQiC"},
    "20372100007413276": {"name": "小火鍋", "pcode": "6S7eO"},
    "20372100007662257": {"name": "A1U1", "pcode": "9l1TR"},
    "20372100005972917": {"name": "Xuan", "pcode": "r2a6E"},
    "20372000486671177": {"name": "韓國愛芮", "pcode": "X1I1O"},
    "20372100005696637": {"name": "愛生病", "pcode": "zoM3H"},
    "20372100003196467": {"name": "00Devi1농", "pcode": "AMTPP"},
    "20372100007618840": {"name": "啊嗚嘎", "pcode": "32f2E"},
    "20372100000900216": {"name": "쿠죠린", "pcode": "sUClJ"},
    "20372100000820899": {"name": "나기히카루", "pcode": "cfAxE"},
    "20372100005892774": {"name": "六道舞風", "pcode": "GGuQO"},
    "20372100006121673": {"name": "姆咪姆咪心動動", "pcode": "AAa3Q"},
    "20372100003567962": {"name": "봉봉", "pcode": "w99gQ"},
    "20372100000483518": {"name": "완두커엉", "pcode": "qVVQM"},
    "20372100000155226": {"name": "캡틴봉봉", "pcode": "0L5pI"},
    "20372100005241912": {"name": "阿福", "pcode": "6spUC"}
}

# ⚠️ 注意：上面的 5碼 ID (pcode) 我是先用示範數字填寫。
# 如果你手邊有他們正確的 5 碼 ID，請直接在上面修改填入！這樣最穩。

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497581193770696764/emqr6qKa6f96C1ukjANQbKGVb_Q5Aaxvav-khvYN1bnZFR2NKFnik5B5-ZYo4KokRO0P"
CHECK_INTERVAL = 10 # 稍微拉長到 20 秒，安全第一

WEB_URL = "https://xmasakix.github.io/msw-extractor-web/index.html" 

SOCIAL_API = "https://mverse-api.nexon.com/social/v1/profile/{}"
PUBLIC_API = "https://mverse-api.nexon.com/profile/v1/home/profileCode/{}"

player_configs = {}

def send_ip_blocked_warning(status_code, phase="掃描中"):
    """當發現被鎖 IP 時，發送警告到 Discord"""
    print(f"⚠️ [警告] 造型監控在【{phase}】偵測到 Cloudflare 阻擋！狀態碼: {status_code}", flush=True)
    payload = {
        "embeds": [{
            "title": "⚠️ 造型監控遭受 Cloudflare 封鎖限制 (Error 1015)",
            "description": f"機器人在 **{phase}** 階段抓取官方造型失敗。\n**HTTP 狀態碼**：`{status_code}`\n\n**腳本將自動冷卻 10 分鐘**，隨後嘗試重新連線。",
            "color": 16744192,
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }]
    }
    try: requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
    except: pass

def initialize_players():
    print("--- 🚀 啟動終極監控模式 ---", flush=True)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    for ppsn, info in PLAYER_MAP.items():
        name = info["name"]
        p_code = info.get("pcode")
        time.sleep(1.5)
        
        try:
            # 如果沒有事先寫死 pcode，才去戳 Social API 撈取
            if not p_code:
                res = requests.get(SOCIAL_API.format(ppsn), headers=headers, timeout=10)
                if res.status_code != 200:
                    print(f"❌ 初始化 {name} 的 Social API 失敗，狀態碼: {res.status_code}", flush=True)
                    if res.status_code in [429, 403, 1015]:
                        send_ip_blocked_warning(res.status_code, f"初始化-{name}(Social)")
                        time.sleep(600)
                    continue
                p_code = res.json().get('data', {}).get('profileCode')
            
            if p_code:
                # 初始獲取造型
                test_url = f"{PUBLIC_API.format(p_code)}?nocache={int(time.time())}"
                res_img = requests.get(test_url, headers=headers, timeout=10)
                
                if res_img.status_code != 200:
                    print(f"❌ 初始化 {name} 的 Public API 失敗，狀態碼: {res_img.status_code}", flush=True)
                    if res_img.status_code in [429, 403, 1015]:
                        send_ip_blocked_warning(res_img.status_code, f"初始化-{name}(Public)")
                        time.sleep(600)
                    continue
                    
                initial_url = res_img.json().get('data', {}).get('avatarImageUrl', '')
                
                # 寫入全域設定庫
                player_configs[ppsn] = {"pcode": p_code, "name": name, "last_url": initial_url}
                print(f"✅ 已成功鎖定監控目標: {name} ({p_code})", flush=True)
            else:
                print(f"❌ 無法解析 {name} 的代碼", flush=True)
        except Exception as e:
            print(f"❌ 初始化 {name} 失敗: {e}", flush=True)

def check_fashion():
    print(f"--- [{time.strftime('%H:%M:%S')}] 深度掃描中 (當前監控人數: {len(player_configs)}) ---", flush=True)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://mverse.nexon.com/'
    }
    
    for ppsn, config in list(player_configs.items()):
        time.sleep(0.8) # 拉長人與人之間的間隔
        try:
            pcode = config['pcode']
            name = config['name']
            
            url = f"{PUBLIC_API.format(pcode)}?v={time.time_ns()}"
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code != 200:
                print(f"❌ 擷取 {name} 造型失敗，狀態碼: {res.status_code}", flush=True)
                if res.status_code in [429, 403, 1015]:
                    send_ip_blocked_warning(res.status_code, f"掃描中-{name}")
                    print("😴 進入冷卻模式，暫停打擾 Nexon 10 分鐘...", flush=True)
                    time.sleep(600)
                    return 
                continue
                
            current_avatar = res.json().get('data', {}).get('avatarImageUrl', '')
            if not current_avatar:
                continue

            # 偵測是否有變動
            if current_avatar != config['last_url']:
                print(f"🔔 【偵測到造型更新】玩家: {name}", flush=True)
                config['last_url'] = current_avatar
                
                search_link = f"{WEB_URL}?player_id={pcode}"
                
                description_text = (
                    f"🔹 個人代碼：**[{pcode}]({search_link})**\n"
                    f"🔹 玩家 PPSN：`{ppsn}`\n\n"
                    f"這傢伙換了造型，快摳！"
                )
                    
                payload = {
                    "embeds": [{
                        "title": f"✨ {name} 更換造型!!",
                        "color": 1044977,
                        "description": description_text,
                        "image": {"url": current_avatar}, 
                        "footer": {"text": f"偵測時間: {time.strftime('%H:%M:%S')}"},
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                    }]
                }
                requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
                print(f"📣 [Discord已發送] {name} 造型更新通知。", flush=True)
                
        except Exception as e:
            print(f"掃描 {ppsn} 失敗: {e}", flush=True)

def main_loop():
    initialize_players()
    while True:
        check_fashion()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=main_loop, daemon=True).start()
    run_web()
