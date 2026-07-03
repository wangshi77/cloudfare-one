import requests
import base64
import re
import os

API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def get_gfwlist_domains():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        content = base64.b64decode(response.text).decode('utf-8')
        return list(set(re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)))
    except:
        return []

def main():
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    # 1. 尝试探测所有可能的路径
    possible_endpoints = [
        f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/default",
        f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/settings"
    ]
    
    domains = get_gfwlist_domains()
    rules = [{"address": "94.191.0.0/17", "description": "CN IP"}, {"address": "93.183.18.0/24", "description": "CN IP"}]
    for d in domains[:300]:
        rules.append({"host": f"*.{d}"})

    # 2. 遍历探测，只要有一次 PUT 成功，就立即停止并同步
    for url in possible_endpoints:
        print(f"🚀 正在尝试路径: {url} ...")
        # 构造载荷：尝试 exclude 模式
        payload = {"exclude": rules}
        
        res = requests.put(url, json=payload, headers=headers)
        
        if res.status_code == 200:
            print("🎉 同步成功！路径锁定为: " + url)
            return
        else:
            print(f"⚠️ 尝试失败 ({res.status_code}): {res.text}")
    
    print("❌ 最终失败：所有路径均无法写入，请确认 API Token 是否具有 'Zero Trust: Edit' 权限。")

if __name__ == "__main__":
    main()
