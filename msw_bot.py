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
    "20372100007618840": "啊嗚嘎",
    "20372100000900216": "쿠죠린",
    "20372100000820899": "나기히카루",
    "20372100005892774": "六道舞風",
    "20372100006121673": "姆咪姆咪心動動"
}

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1497581193770696764/emqr6qKa6f96C1ukjANQbKGVb_Q5Aaxvav-khvYN1bnZFR2NKFnik5B5-ZYo4KokRO0P"
CHECK_INTERVAL = 20 # 稍微拉長間隔，減少被 API 封鎖快取的機率

# 🚀 這裡填入你的裝備提取網站 URL
WEB_URL = "https://xmasakix.github.io/msw-extractor-web/index.html" 

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
                
                # 🚀 動態生成帶有玩家 5碼ID 參數的直達連結
                search_link = f"{WEB_URL}?player_id={pcode}"
                
                # 建立發送給 Discord 的資料
                payload = {
                    "embeds": [{
                        "title": "✨ 發現新造型！",
                        "color": 15844367,
                        "fields": [
                            {
                                "name": "📋 玩家資料",
                                "value": (
                                    f"玩家名稱：**{name}**\n\n"
                                    f"🔗 **[🔍 點此前往提取裝備列表]({search_link})**\n\n"
                                    f"點擊選取複製：\n"
                                    f"🔹 個人代碼：`{pcode}`\n"
                                    f"🔹 玩家 PPSN：`{ppsn}`\n\n"
                                    f"這傢伙換了造型，快摳！"
                                ),
                                "inline": True
                            }
                        ],
                        # 💡 修正 1：把 custom_image 改成 current_avatar
                        # 💡 修正 2：從 thumbnail 改成 image，這樣圖片就會變成下方大圖
                        "image": {"url": current_avatar}, 
                        "footer": {"text": f"偵測時間: {time.strftime('%H:%M:%S')}"},
                        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
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
