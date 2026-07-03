import requests
import base64
import re
import os

# 配置环境变量
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
POLICY_ID = "019f1bd7-e528-7c12-8183-5b437fb27e6e"

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
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    # 1. 先获取当前策略的完整定义 (这是最关键的一步)
    get_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{POLICY_ID}"
    res = requests.get(get_url, headers=headers)
    
    if res.status_code != 200:
        print(f"❌ 获取策略失败: {res.text}")
        return
        
    policy_data = res.json().get('result', {})
    
    # 2. 构建新的排除列表
    domains = get_gfwlist_domains()
    new_rules = [
        {"address": "94.191.0.0/17", "description": "CN IP"},
        {"address": "93.183.18.0/24", "description": "CN IP"}
    ]
    for d in domains[:300]:
        new_rules.append({"host": f"*.{d}"})
    
    # 3. 将新规则覆盖到原有的策略对象中
    # 这里我们只修改 exclude 字段，其他配置（如 fallback_domains 等）原样保留
    policy_data['exclude'] = new_rules
    
    # 4. 执行全量覆盖更新 (PATCH)
    print(f"🚀 正在发送全量策略同步...")
    res_patch = requests.patch(get_url, json=policy_data, headers=headers)
    
    if res_patch.status_code == 200:
        print("🎉 同步成功！")
    else:
        print(f"❌ 同步失败 ({res_patch.status_code}): {res_patch.text}")

if __name__ == "__main__":
    main()
