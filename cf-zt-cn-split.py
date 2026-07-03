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

    # 1. 准备规则 (限制 300 条以确保请求成功)
    domains = get_gfwlist_domains()
    rules = [
        {"address": "94.191.0.0/17", "description": "CN IP"},
        {"address": "93.183.18.0/24", "description": "CN IP"}
    ]
    for d in domains[:300]:
        rules.append({"host": f"*.{d}"})
    
    # 2. 关键点：使用 'default' 别名路径，并以 split_tunnel 结构发送
    # 这是 Cloudflare 文档中针对单一默认策略的最标准更新方式
    sync_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/default/split_tunnel"
    
    payload = {
        "mode": "exclude",  # 你的账户显示使用了 exclude 结构，这里必须匹配
        "exclude": rules    # 将规则放入 exclude 列表
    }
    
    print(f"🚀 正在向 {sync_url} 同步...")
    res = requests.put(sync_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")
        print("💡 如果报错 'invalid mode'，请尝试将 payload 中的 mode 改为 'include'。")

if __name__ == "__main__":
    main()
