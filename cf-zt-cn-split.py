import requests
import os
import base64
import re

# 配置参数
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def get_gfwlist():
    """直接使用该开源项目的域名获取逻辑"""
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        content = base64.b64decode(response.text).decode('utf-8')
        domains = list(set(re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)))
        # 严格对齐开源仓库的格式要求
        return [{"host": f"*.{d}"} for d in domains if "." in d]
    except:
        return []

def main():
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    # 1. 自动定位策略 (开源项目的逻辑：获取所有策略并筛选出 default)
    policy_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
    res = requests.get(policy_url, headers=headers)
    if res.status_code != 200:
        print(f"❌ 获取策略失败: {res.text}")
        return
    
    policies = res.json().get('result', [])
    # 自动定位可写的策略 ID
    target_policy = next((p for p in policies if p.get('default')), None)
    if not target_policy:
        print("❌ 未找到默认策略，无法同步")
        return
    
    policy_id = target_policy['policy_id']
    
    # 2. 构造规则 (IP + 域名)
    rules = [
        {"address": "94.191.0.0/17", "description": "CN IP"},
        {"address": "93.183.18.0/24", "description": "CN IP"}
    ] + get_gfwlist()[:2000] # 限制数量以防接口溢出

    # 3. 严格复刻开源项目的 PATCH 载荷结构
    payload = {
        "split_tunnel": {
            "mode": "exclude",
            "include": [],
            "exclude": rules
        }
    }
    
    # 4. 同步更新
    update_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{policy_id}"
    print(f"🚀 正在使用开源项目逻辑同步到策略 {policy_id} ...")
    
    res = requests.patch(update_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！完全匹配开源项目行为。")
    else:
        print(f"❌ 同步失败: {res.text}")

if __name__ == "__main__":
    main()
