import requests
import base64
import re
import os

# 环境变量读取 (确保 GitHub Secrets 中设置正确)
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def get_gfwlist_domains():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        # GFWList 通常是 base64 编码
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

    # 1. 获取默认策略 (直接访问 default 路径)
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/default"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取默认策略失败: {response.text}")
        return

    data = response.json().get('result', {})
    policy_id = data.get('policy_id')
    
    if not policy_id:
        print("❌ 未能获取到 policy_id，请检查 API 返回结构。")
        return

    print(f"✅ 已锁定默认策略 ID: {policy_id}")

    # 2. 准备 Split Tunnel 规则
    # 包含本地局域网和 GFWList
    rules = [{"address": "192.168.0.0/16", "description": "Local LAN"}]
    domains = get_gfwlist_domains()
    print(f"✅ 成功解析 {len(domains)} 条 GFWList 规则")
    
    # Cloudflare API 对规则数量有限制，限制在 990 条以内
    for d in domains[:990]:
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})

    # 3. 执行更新 (PUT 请求)
    sync_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{policy_id}/split_tunnel"
    payload = {"mode": "include", "include": rules}
    
    res = requests.put(sync_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！策略已更新。")
    else:
        # 如果依然报错，请检查此处的 JSON 返回内容
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")

if __name__ == "__main__":
    main()
