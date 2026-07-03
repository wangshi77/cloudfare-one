import requests
import os
import base64
import re

# 这里的逻辑完全套用自 upbeat-backbone-bose/cf-zt-cn-split
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
POLICY_ID = os.getenv("CF_POLICY_ID") # 如果你之前运行不成功，可以尝试留空，让脚本自动发现

def get_gfwlist():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        content = base64.b64decode(response.text).decode('utf-8')
        # 原版仓库的正则提取逻辑
        domains = list(set(re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)))
        return [{"host": f"*.{d}"} for d in domains if "." in d]
    except Exception as e:
        print(f"获取规则失败: {e}")
        return []

def main():
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    # 1. 自动寻找策略 (如果没提供 POLICY_ID)
    if not POLICY_ID:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
        res = requests.get(url, headers=headers)
        policies = res.json().get('result', [])
        # 严格套用原作者的筛选逻辑
        target = next((p for p in policies if p.get('default')), None)
        if not target:
            print("无法自动找到默认策略")
            return
        policy_id = target['policy_id']
    else:
        policy_id = POLICY_ID

    # 2. 构造数据
    rules = [
        {"address": "94.191.0.0/17", "description": "CN IP"},
        {"address": "93.183.18.0/24", "description": "CN IP"}
    ] + get_gfwlist()

    # 3. 严格套用该仓库的 PATCH 结构
    payload = {
        "split_tunnel": {
            "mode": "exclude",
            "include": [],
            "exclude": rules
        }
    }
    
    # 4. 执行更新
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{policy_id}"
    res = requests.patch(url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！")
    else:
        print(f"❌ 同步失败: {res.text}")

if __name__ == "__main__":
    main()
