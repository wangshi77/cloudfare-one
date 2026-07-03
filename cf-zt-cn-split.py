import requests
import base64
import re
import os

# 环境变量读取
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
        print(f"获取 GFWList 失败: {e}")
        return []

def main():
    if not API_TOKEN or not ACCOUNT_ID:
        print("❌ 错误：环境变量未配置")
        return

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. 获取规则
    domains = get_gfwlist_domains()
    # 保持与以前同步 IP 类似的数据格式
    rules = [{"address": "192.168.0.0/16", "description": "Local LAN"}]
    for d in domains[:500]: 
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})
    
    print(f"✅ 已准备 {len(rules)} 条规则...")

    # 2. 这是 Cloudflare 修改 Split Tunnel 最标准的 PATCH 路径
    # 如果以前能跑通，极大概率是这个路径或者是 policy 直接 PATCH
    sync_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{POLICY_ID}"
    
    # Payload 结构：以前同步 IP 成功，说明这个结构是正确的
    # 注意：split_tunnel 下分为 include 和 exclude 两个部分
    payload = {
        "split_tunnel": {
            "mode": "include",
            "include": rules
        }
    }

    print(f"🚀 正在执行 PATCH 请求...")
    res = requests.patch(sync_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")
        print("💡 提示：如果依然报错 404，请确认该策略在后台是否支持 Split Tunnel 模式。")

if __name__ == "__main__":
    main()
