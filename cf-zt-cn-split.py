import requests
import base64
import re
import os

# 配置环境变量
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def get_gfwlist_domains():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        content = base64.b64decode(response.text).decode('utf-8')
        domains = re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)
        return list(set(domains))
    except Exception as e:
        print(f"❌ 获取 GFWList 失败: {e}")
        return []

def main():
    if not API_TOKEN or not ACCOUNT_ID:
        print("❌ 错误：未配置环境变量")
        return

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. 获取 GFWList 并构建规则
    domains = get_gfwlist_domains()
    # 根据你提供的原始数据，保留原有的 CN IP 规则，避免覆盖出错
    rules = [
        {"address": "94.191.0.0/17", "description": "CN IP"},
        {"address": "93.183.18.0/24", "description": "CN IP"}
    ]
    # 追加规则
    for d in domains[:300]:
        rules.append({"host": f"*.{d}"})
    
    print(f"✅ 已准备 {len(rules)} 条规则...")

    # 2. 最关键的逻辑：使用 'default' 而不是 ID，并使用 PUT 方法覆盖
    # 路径：/accounts/{id}/devices/policy/default
    sync_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/default"
    
    # payload：直接覆盖 exclude 列表
    payload = {"exclude": rules}
    
    print(f"🚀 正在发送同步请求到: {sync_url} ...")
    res = requests.put(sync_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")
        print("💡 如果报错 'invalid format'，请尝试将 payload 修改为: {'split_tunnel': {'exclude': rules}}")

if __name__ == "__main__":
    main()
