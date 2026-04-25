import requests
import time
import threading
from flask import Flask
import os

app = Flask('')

@app.route('/')
def home():
    return "MSW Avatar Monitor is Running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 設定區域 ---
PLAYER_MAP = {
    "20372100005827913": "Budin",
    "20372100001023713": "Majajaja",
    "20372100005450149": "lodo_0118",
    "20372100007662257": "A1U1",
    "20372100005972917": "Xuan"
}

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497581193770696764/emqr6qKa6f96C1ukjANQbKGVb_Q5Aaxvav-khvYN1bnZFR2NKFnik5B5-ZYo4KokRO0P"
CHECK_INTERVAL = 20 

API_URL_TEMPLATE = "https://mverse-api.nexon.com/social/v1/profile/{}"

# 僅紀錄最後的 avatarImageUrl
last_avatar_url = {pid: None for pid in PLAYER_MAP.keys()}

def check_fashion():
    global last_avatar_url
    print(f"[{time.strftime('%H:%M:%S')}] 造型雷達掃描中...")

    for pid, name in PLAYER_MAP.items():
        try:
            url = API_URL_TEMPLATE.format(pid)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            
            response = requests.get(url, headers=headers, timeout=10)
            user_data = response.json().get('data', {})
            
            # 取得關鍵的 avatarImageUrl (全身造型圖)
            current_avatar = user_data.get('avatarImageUrl', '')
            p_code = user_data.get('profileCode', '未知')

            # 初始化
            if last_avatar_url[pid] is None:
                last_avatar_url[pid] = current_avatar
                continue

            # 比對 avatarImageUrl 是否變動
            if current_avatar != last_avatar_url[pid]:
                last_avatar_url[pid] = current_avatar
                
                # Discord 通知配置
                payload = {
                    "embeds": [{
                        "title": "✨ 偵測到新造型！",
                        "description": f"玩家：**{name}**\n代碼：`{p_code}`\n\n內容：玩家已更新全身造型裝扮。",
                        # 這裡改成使用 avatarImageUrl 作為大圖
                        "image": {"url": current_avatar}, 
                        "color": 15844367, 
                        "footer": {"text": f"PPSN: {pid}"},
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                    }]
                }
                requests.post(DISCORD_WEBHOOK_URL, json=payload)
                print(f"👗 成功通報造型變更: {name}")

        except Exception as e:
            print(f"監控 {name} 時出錯: {e}")

def main_loop():
    while True:
        check_fashion()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=main_loop, daemon=True).start()
    run_web()
