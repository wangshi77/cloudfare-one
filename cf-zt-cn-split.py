import requests
import base64
import re
import os

# 配置环境变量
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")

def get_policy_id_by_name(name="ios"):
    """自动获取名为 'ios' 的策略 ID"""
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    response = requests.get(url, headers=headers).json()
    
    for policy in response.get("result", []):
        if policy["name"] == name:
            return policy["id"]
    return None

def get_gfwlist_domains():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        content = base64.b64decode(response.text).decode('utf-8')
        domains = re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)
        return list(set(domains))
    except: return []

def main():
    profile_id = get_policy_id_by_name("ios")
    if not profile_id:
        print("❌ 未找到名为 'ios' 的配置文件，请检查名称。")
        return

    # 基础规则
    rules = [
        {"address": "192.168.0.0/16", "description": "Local LAN"},
        {"address": "10.0.0.0/8", "description": "Private Network"},
        {"address": "172.16.0.0/12", "description": "Private Network"}
    ]
    
    # 注入 GFWList 域名
    for d in get_gfwlist_domains()[:990]:
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})
    
    # 核心修正：发送完整的 Include 列表
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{profile_id}/split_tunnel"
    payload = {
        "mode": "include",
        "include": rules  # 确保这里是一个包含字典的列表 (Array)
    }
    
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    print(f"🚀 正在将 {len(rules)} 条规则同步到 'ios' 策略...")
    response = requests.put(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print("✅ 同步成功！")
    else:
        print(f"❌ 同步失败: {response.text}")

if __name__ == "__main__":
    main()
