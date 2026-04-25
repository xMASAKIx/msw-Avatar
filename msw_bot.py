import requests
import time
import threading
from flask import Flask
import os

app = Flask('')

@app.route('/')
def home():
    return "MSW Fashion Monitor (Public API) is Running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 設定區域 ---
# 這裡貼上你最新的長數字名單
PLAYER_MAP = {
    "20372100005827913": "Budin",
    "20372100001023713": "Majajaja",
    "20372100005450149": "lodo_0118",
    "20372100007662257": "A1U1",
    "20372100005972917": "Xuan",
    "20372100006053110": "跑車人"
}

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497581193770696764/emqr6qKa6f96C1ukjANQbKGVb_Q5Aaxvav-khvYN1bnZFR2NKFnik5B5-ZYo4KokRO0P"
CHECK_INTERVAL = 20 

# 核心 API 路徑
SOCIAL_API = "https://mverse-api.nexon.com/social/v1/profile/{}"
PUBLIC_API = "https://mverse-api.nexon.com/profile/v1/home/profileCode/{}"

# 用來儲存轉換後的 5 碼代碼與造型紀錄
player_configs = {} # 格式: {ppsn: {"pcode": "xxxxx", "name": "...", "last_url": "..."}}

def initialize_players():
    print("--- 正在初始化玩家代碼 ---")
    for ppsn, name in PLAYER_MAP.items():
        try:
            # 先從 Social API 取得 5 碼 profileCode
            res = requests.get(SOCIAL_API.format(ppsn), timeout=10)
            p_code = res.json().get('data', {}).get('profileCode')
            if p_code:
                player_configs[ppsn] = {"pcode": p_code, "name": name, "last_url": None}
                print(f"✅ 已連結: {name} -> {p_code}")
            else:
                print(f"❌ 找不到 {name} 的 5 碼代碼")
        except:
            print(f"❌ 初始化 {name} 失敗")

def check_fashion():
    print(f"--- [{time.strftime('%H:%M:%S')}] 造型雷達掃描中 ---")
    for ppsn, config in player_configs.items():
        try:
            pcode = config['pcode']
            name = config['name']
            
            # 使用公開 API 抓取造型圖
            url = f"{PUBLIC_API.format(pcode)}?t={int(time.time())}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            res = requests.get(url, headers=headers, timeout=10)
            current_avatar = res.json().get('data', {}).get('avatarImageUrl', '')

            if not current_avatar:
                continue

            # 初始紀錄
            if config['last_url'] is None:
                config['last_url'] = current_avatar
                continue

            # 偵測變更
            if current_avatar != config['last_url']:
                print(f"🔥 偵測到造型更新: {name}")
                config['last_url'] = current_avatar
                
                payload = {
                    "embeds": [{
                        "title": "✨ 發現新造型！",
                        "description": f"玩家：**{name}**\n代碼：`{pcode}`",
                        "image": {"url": current_avatar}, 
                        "color": 15844367,
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                    }]
                }
                requests.post(DISCORD_WEBHOOK_URL, json=payload)
        except Exception as e:
            print(f"掃描 {ppsn} 出錯: {e}")

def main_loop():
    initialize_players()
    while True:
        check_fashion()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=main_loop, daemon=True).start()
    run_web()
