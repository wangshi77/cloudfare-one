import requests
import os
import json

API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def main():
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    
    # 获取该账户下所有的策略列表
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
    
    print(f"🚀 正在检索所有策略...")
    res = requests.get(url, headers=headers)
    
    if res.status_code == 200:
        data = res.json().get('result', [])
        print(f"\n✅ 成功找到 {len(data)} 个策略：")
        print(json.dumps(data, indent=2))
        
        # 如果找到了策略，我们顺便取第一个 ID 看看它的具体结构
        if len(data) > 0:
            target_id = data[0].get('id')
            print(f"\n👉 正在尝试获取第一个策略 ({target_id}) 的详细配置结构...")
            detail_res = requests.get(f"{url}/{target_id}", headers=headers)
            print(json.dumps(detail_res.json(), indent=2))
    else:
        print(f"❌ 获取列表失败 ({res.status_code}): {res.text}")

if __name__ == "__main__":
    main()
