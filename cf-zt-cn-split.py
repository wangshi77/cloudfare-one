import requests
import base64
import re
import os

# 从环境变量读取凭据
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

# 使用你之前 DEBUG 成功拿到的 Policy ID
POLICY_ID = "019f1bd7-e528-7c12-8183-5b437fb27e6e"

def get_gfwlist_domains():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        content = base64.b64decode(response.text).decode('utf-8')
        domains = re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)
        return list(set(domains))
    except Exception as e:
        print(f"获取 GFWList 失败: {e}")
        return []

def main():
    if not API_TOKEN or not ACCOUNT_ID:
        print("❌ 错误：未配置环境变量 CF_API_TOKEN 或 CF_ACCOUNT_ID")
        return

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 构造 Split Tunnel 规则
    # 注意：Cloudflare 默认可能使用 'include' 或 'exclude' 模式
    # 如果你的策略原本是 include 模式，请确保这里的结构正确
    rules = [{"address": "192.168.0.0/16", "description": "Local LAN"}]
    domains = get_gfwlist_domains()
    print(f"✅ 成功解析 {len(domains)} 条 GFWList 规则")
    
    for d in domains[:990]:
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})

    # 使用具体的 Policy ID 访问 API
    # 如果下方的路径依然报 404，请尝试将 'split_tunnel' 改为 'exclude' 或 'include'
    sync_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{POLICY_ID}/split_tunnel"
    payload = {"mode": "include", "include": rules}
    
    print(f"🚀 正在向策略 {POLICY_ID} 同步规则...")
    res = requests.put(sync_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")
        # 如果是 404，说明此路径不支持 split_tunnel 操作，
        # 我们可以尝试另一种路径：
        if res.status_code == 404:
            print("💡 尝试备选路径...")
            alt_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{POLICY_ID}/exclude"
            res_alt = requests.put(alt_url, json={"exclude": rules}, headers=headers)
            print(f"备选路径结果: {res_alt.status_code} - {res_alt.text}")

if __name__ == "__main__":
    main()
