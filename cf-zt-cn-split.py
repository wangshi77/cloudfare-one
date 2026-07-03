import requests
import os
import json

API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def main():
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    # 获取默认策略的完整信息
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/default"
    
    print(f"🚀 正在获取当前默认策略配置...")
    res = requests.get(url, headers=headers)
    
    if res.status_code == 200:
        config = res.json().get('result', {})
        print("\n✅ 成功获取完整配置，请复制以下 JSON 内容发给我：")
        print(json.dumps(config, indent=2))
    else:
        print(f"❌ 获取失败 ({res.status_code}): {res.text}")
        print("💡 如果这里报错，说明你的策略可能不是 'default'，请运行上一个脚本查看策略列表。")

if __name__ == "__main__":
    main()
