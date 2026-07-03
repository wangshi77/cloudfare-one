import requests
import base64
import re
import os

# 配置环境变量
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
# 这是从你的 API 返回中解析出的正确策略 ID
POLICY_ID = "019f1bd7-e528-7c12-8183-5b437fb27e6e"

def get_gfwlist_domains():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        # GFWList 需要 Base64 解码
        content = base64.b64decode(response.text).decode('utf-8')
        # 提取域名并去重
        domains = re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)
        return list(set(domains))
    except Exception as e:
        print(f"❌ 获取 GFWList 失败: {e}")
        return []

def main():
    if not API_TOKEN or not ACCOUNT_ID:
        print("❌ 错误：未配置环境变量 (CF_API_TOKEN 或 CF_ACCOUNT_ID)")
        return

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. 获取并处理规则
    domains = get_gfwlist_domains()
    # 保持你原有的 CN IP 规则
    rules = [
        {"address": "94.191.0.0/17", "description": "CN IP"},
        {"address": "93.183.18.0/24", "description": "CN IP"}
    ]
    # 追加 GFWList 域名 (为了防止触发 API 大小限制，我们取前 400 条)
    for d in domains[:400]:
        rules.append({"host": f"*.{d}"})
    
    print(f"✅ 已准备 {len(rules)} 条规则进行同步...")

    # 2. 执行 PATCH 请求
    # 关键点：直接修改策略的 'exclude' 字段，这符合你账户的 API 结构
    patch_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{POLICY_ID}"
    payload = {"exclude": rules}
    
    print(f"🚀 正在发送同步请求...")
    res = requests.patch(patch_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！策略已更新。")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")
        print("💡 如果依然报错，请检查 Cloudflare Zero Trust 后台是否有其他权限限制。")

if __name__ == "__main__":
    main()
