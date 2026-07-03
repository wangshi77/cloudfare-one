import requests
import base64
import re
import os

# 环境变量
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
    if not API_TOKEN or not ACCOUNT_ID:
        print("❌ 错误：环境变量未配置")
        return

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. 准备规则
    domains = get_gfwlist_domains()
    rules = [{"address": "94.191.0.0/17", "description": "CN IP"}, {"address": "93.183.18.0/24", "description": "CN IP"}]
    for d in domains[:300]:
        rules.append({"host": f"*.{d}"})
    
    # 2. 使用已锁定的正确路径
    target_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/settings"
    
    # 构造载荷
    payload = {"exclude": rules}
    
    print(f"🚀 正在执行稳定同步到: {target_url} ...")
    res = requests.put(target_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！GFWList 规则已生效。")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")

if __name__ == "__main__":
    main()
