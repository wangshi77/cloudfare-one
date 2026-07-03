import requests
import base64
import re
import os

# 读取你在 GitHub Secrets 设置的名称
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def get_gfwlist_domains():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        # 解码 Base64
        content = base64.b64decode(response.text).decode('utf-8')
        # 提取域名
        domains = re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)
        return list(set(domains))
    except Exception as e:
        print(f"获取 GFWList 失败: {e}")
        return []

def main():
    if not API_TOKEN or not ACCOUNT_ID:
        print("❌ 错误：未获取到环境变量，请检查 GitHub Secrets 设置。")
        return

    # 1. 构造规则
    rules = [{"address": "192.168.0.0/16", "description": "Local LAN"}]
    for d in get_gfwlist_domains()[:990]:
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})

    # 2. 同步到默认策略 (Default Policy)
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/default/split_tunnel"
    payload = {"mode": "include", "include": rules}
    headers = {
        "Authorization": f"Bearer {API_TOKEN}", 
        "Content-Type": "application/json"
    }
    
    print(f"🚀 正在同步 {len(rules)} 条规则到默认策略...")
    response = requests.put(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("✅ 同步成功！")
    else:
        print(f"❌ 同步失败: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
