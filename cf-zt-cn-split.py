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
        domains = re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)
        return list(set(domains))
    except Exception as e:
        print(f"获取 GFWList 失败: {e}")
        return []

def main():
    if not API_TOKEN or not ACCOUNT_ID:
        print("❌ 错误：未配置环境变量。")
        return

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. 自动寻找策略 ID
    list_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
    response = requests.get(list_url, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 获取策略列表失败 ({response.status_code}): {response.text}")
        return

    data = response.json()
    policies = data.get('result', [])

    # 2. 严谨的策略查找逻辑
    target_policy = None
    if isinstance(policies, list):
        for p in policies:
            if isinstance(p, dict) and p.get('name') == 'Default':
                target_policy = p
                break
        # 如果没找到叫 Default 的，默认取第一个字典项
        if not target_policy:
            for p in policies:
                if isinstance(p, dict):
                    target_policy = p
                    break
    
    if not target_policy:
        print("❌ 未在 Cloudflare 中找到任何可用策略。")
        return

    policy_id = target_policy.get('id')
    print(f"✅ 已定位策略: {target_policy.get('name', 'Unknown')} (ID: {policy_id})")

    # 3. 构造规则
    rules = [{"address": "192.168.0.0/16", "description": "Local LAN"}]
    for d in get_gfwlist_domains()[:990]:
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})

    # 4. 同步执行
    sync_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{policy_id}/split_tunnel"
    payload = {"mode": "include", "include": rules}
    
    res = requests.put(sync_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print(f"🎉 同步成功！已更新规则。")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")

if __name__ == "__main__":
    main()
