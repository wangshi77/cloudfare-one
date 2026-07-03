import requests
import base64
import re
import os

# 凭据配置
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
POLICY_ID = "019f1bd7-e528-7c12-8183-5b437fb27e6e" # 你之前确认的 ID

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
        print("❌ 错误：环境变量未配置")
        return

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. 准备规则 (限制数量以防止 400 错误)
    domains = get_gfwlist_domains()
    # Cloudflare API 对单次请求的 Payload 大小有限制，建议分批或控制在 500 条以内
    rules = [{"address": "192.168.0.0/16", "description": "Local LAN"}]
    for d in domains[:500]: 
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})
    
    print(f"✅ 已准备 {len(rules)} 条规则进行同步...")

    # 2. 构造符合 API 要求的 JSON 结构
    # Cloudflare Split Tunnel 通常要求显式包含 include 和 exclude
    payload = {
        "mode": "include",
        "include": rules,
        "exclude": []
    }

    # 3. 发送同步请求
    sync_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{POLICY_ID}/split_tunnel"
    
    print(f"🚀 正在执行同步...")
    res = requests.put(sync_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")
        print("💡 提示：如果依然报错 400，请检查 Cloudflare 后台该策略的模式是否允许 'include'。")

if __name__ == "__main__":
    main()
