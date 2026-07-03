import requests
import base64
import re
import os

# 从环境变量获取 API 凭证
API_TOKEN = os.getenv("cfat_Y8mLtKHpGAwYk9cXlKuqsOgyPdDObnSW7TlyPmKmc7b77de7")
ACCOUNT_ID = os.getenv("6fffa32a503ef35a744ef3243f4003f2")

def get_gfwlist_domains():
    """自动获取并解析最新的 GFWList"""
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        # 解码 Base64
        content = base64.b64decode(response.text).decode('utf-8')
        # 提取域名 (匹配 ||domain.com)
        domains = re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)
        return list(set(domains))
    except Exception as e:
        print(f"获取 GFWList 失败: {e}")
        return []

def get_policy_id_by_name(name="ios"):
    """自动获取名为 'ios' 的策略 ID"""
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if not data.get("success"):
        print(f"❌ API 请求失败: {data.get('errors')}")
        return None
        
    result = data.get("result")
    if result is None:
        print("❌ 错误：Cloudflare 未返回 policy 列表。")
        return None
        
    for policy in result:
        if policy.get("name") == name:
            return policy.get("id")
            
    print(f"❌ 错误：未找到名为 '{name}' 的配置文件。")
    return None

def main():
    policy_id = get_policy_id_by_name("ios")
    if not policy_id:
        return

    # 1. 基础内网豁免
    rules = [
        {"address": "192.168.0.0/16", "description": "Local LAN"},
        {"address": "10.0.0.0/8", "description": "Private Network"},
        {"address": "172.16.0.0/12", "description": "Private Network"}
    ]
    
    # 2. 注入 GFWList 前 990 条域名
    gfw_domains = get_gfwlist_domains()
    for d in gfw_domains[:990]:
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})

    # 3. 推送到 Cloudflare
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{policy_id}/split_tunnel"
    payload = {"mode": "include", "include": rules}
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    print(f"🚀 正在同步 {len(rules)} 条规则到 'ios' 策略...")
    response = requests.put(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("✅ 同步成功！")
    else:
        print(f"❌ 同步失败: {response.text}")

if __name__ == "__main__":
    main()
