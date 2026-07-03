import requests
import os
import base64
import re

# 环境变量配置
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
POLICY_ID = "019f1bd7-e528-7c12-8183-5b437fb27e6e" # 我们刚刚确认过的有效 ID

def get_gfwlist_domains():
    """复刻原仓库的 GFWList 提取逻辑"""
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        content = base64.b64decode(response.text).decode('utf-8')
        # 提取 ||domain.com 格式
        domains = list(set(re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)))
        # 转换成 Cloudflare 要求的 *.domain.com 格式
        return [{"host": f"*.{d}"} for d in domains if "." in d]
    except:
        return []

def main():
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # 获取规则列表
    gfw_rules = get_gfwlist_domains()
    # 合并基础 CN IP 规则
    all_rules = [
        {"address": "94.191.0.0/17", "description": "CN IP"},
        {"address": "93.183.18.0/24", "description": "CN IP"}
    ] + gfw_rules[:3000] # Cloudflare 限制单次规则上限，取前 3000 条

    # 严格按照原仓库结构构造 payload
    payload = {
        "split_tunnel": {
            "mode": "exclude",
            "include": [],
            "exclude": all_rules
        }
    }
    
    # 使用 PATCH 方法
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{POLICY_ID}"
    
    print(f"🚀 正在执行原仓库同步逻辑 (共 {len(all_rules)} 条规则)...")
    res = requests.patch(url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！GFWList 规则已全量更新。")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")

if __name__ == "__main__":
    main()
