import requests
import time
import threading
from flask import Flask
import os

app = Flask('')

@app.route('/')
def home():
    return "MSW Fashion Monitor ULTRA is Running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 設定區域 ---
PLAYER_MAP = {
    "20372100005827913": "Budin",
    "20372100001023713": "Majajaja",
    "20372100005450149": "lodo_0118",
    "20372100007662257": "A1U1",
    "20372100005972917": "Xuan",
    "20372000486671177": "韓國愛芮",
    "20372100005696637": "愛生病",
    "20372100003196467": "00Devi1농",
    "20372100007618840": "啊嗚嘎"
}

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497581193770696764/emqr6qKa6f96C1ukjANQbKGVb_Q5Aaxvav-khvYN1bnZFR2NKFnik5B5-ZYo4KokRO0P"
CHECK_INTERVAL = 30 # 稍微拉長間隔，減少被 API 封鎖快取的機率

SOCIAL_API = "https://mverse-api.nexon.com/social/v1/profile/{}"
PUBLIC_API = "https://mverse-api.nexon.com/profile/v1/home/profileCode/{}"

player_configs = {}

def initialize_players():
    print("--- 🚀 啟動終極監控模式 ---")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    for ppsn, name in PLAYER_MAP.items():
        try:
            # 獲取 5 碼 ID
            res = requests.get(SOCIAL_API.format(ppsn), headers=headers, timeout=10)
            p_code = res.json().get('data', {}).get('profileCode')
            if p_code:
                # 初始獲取造型
                test_url = f"{PUBLIC_API.format(p_code)}?nocache={int(time.time())}"
                res_img = requests.get(test_url, headers=headers, timeout=10)
                initial_url = res_img.json().get('data', {}).get('avatarImageUrl', '')
                
                player_configs[ppsn] = {"pcode": p_code, "name": name, "last_url": initial_url}
                print(f"✅ 已鎖定: {name} ({p_code}) | 初始網址: ...{initial_url[-15:]}")
            else:
                print(f"❌ 無法解析 {name} 的代碼")
        except Exception as e:
            print(f"❌ 初始化 {name} 失敗: {e}")

def check_fashion():
    print(f"--- [{time.strftime('%H:%M:%S')}] 深度掃描中 ---")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://mverse.nexon.com/'
    }
    
    for ppsn, config in player_configs.items():
        try:
            pcode = config['pcode']
            name = config['name']
            
            # 使用更強力的隨機參數
            url = f"{PUBLIC_API.format(pcode)}?v={time.time_ns()}"
            
            res = requests.get(url, headers=headers, timeout=10)
            current_avatar = res.json().get('data', {}).get('avatarImageUrl', '')

            if not current_avatar:
                continue

            # 檢查網址是否有任何字元變動
            if current_avatar != config['last_url']:
                print(f"🔔 【偵測到造型更新】玩家: {name}")
                print(f"   舊網址: {config['last_url']}")
                print(f"   新網址: {current_avatar}")
                
                config['last_url'] = current_avatar
                
                payload = {
                    "embeds": [{
                        "title": "✨ 造型大更新！",
                        "description": f"玩家：**{name}**\n代碼：`{pcode}`\n\n偵測到玩家更換了全身裝扮。",
                        "image": {"url": current_avatar}, 
                        "color": 15844367,
                        "footer": {"text": f"更新時間: {time.strftime('%Y-%m-%d %H:%M:%S')}"}
                    }]
                }
                requests.post(DISCORD_WEBHOOK_URL, json=payload)
            else:
                # 靜默掃描，不發通知
                pass
                
        except Exception as e:
            print(f"掃描 {ppsn} 失敗: {e}")

def main_loop():
    initialize_players()
    while True:
        check_fashion()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(target=main_loop, daemon=True).start()
    run_web()
