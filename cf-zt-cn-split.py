import requests
import base64
import re
import os

# 环境变量：确保 GitHub Secrets 中的名字是 CF_API_TOKEN 和 CF_ACCOUNT_ID
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
        print("❌ 错误：未配置环境变量 (CF_API_TOKEN 或 CF_ACCOUNT_ID)")
        return

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. 自动寻找策略 ID
    list_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
    response = requests.get(list_url, headers=headers)
    
    # 打印原始响应，帮助排查权限或 ID 问题
    print(f"DEBUG: API 返回状态码: {response.status_code}")
    print(f"DEBUG: API 返回内容: {response.text}")
    
    if response.status_code != 200:
        print(f"❌ 获取策略列表失败。请检查 API Token 权限或 Account ID 是否正确。")
        return

    data = response.json()
    policies = data.get('result', [])

    if not isinstance(policies, list) or len(policies) == 0:
        print("❌ 警告：Cloudflare 返回的策略列表为空。请检查该 Account ID 下是否确实存在 Zero Trust 策略。")
        return

    # 优先寻找名为 'Default' 的策略，找不到就用第一个
    target_policy = next((p for p in policies if isinstance(p, dict) and p.get('name') == 'Default'), None)
    if not target_policy:
        target_policy = policies[0]

    policy_id = target_policy.get('id')
    policy_name = target_policy.get('name')
    print(f"✅ 已成功锁定策略: {policy_name} (ID: {policy_id})")

    # 2. 构造规则
    rules = [{"address": "192.168.0.0/16", "description": "Local LAN"}]
    domains = get_gfwlist_domains()
    print(f"✅ 成功解析 {len(domains)} 条 GFWList 规则")
    
    for d in domains[:990]:
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})

    # 3. 同步执行
    sync_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{policy_id}/split_tunnel"
    payload = {"mode": "include", "include": rules}
    
    res = requests.put(sync_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print(f"🎉 同步成功！策略 {policy_name} 已更新。")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")

if __name__ == "__main__":
    main()
