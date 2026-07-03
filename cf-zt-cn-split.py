import requests
import base64
import re
import os

# 配置环境变量
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_PROFILE_ID = os.getenv("CF_PROFILE_ID", "")
MODE = "include"  # 强制设为 include 模式

def get_gfwlist_domains():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        content = base64.b64decode(response.text).decode('utf-8')
        
        domains = set()
        # 正则匹配 ||domain.com 格式
        pattern = re.compile(r'\|\|([^\/]+)')
        
        for line in content.splitlines():
            if line.startswith(('!', '[', '@', '||/', '|', 'http:', 'https:')):
                continue
            match = pattern.search(line)
            if match:
                domains.add(match.group(1))
        
        # 截取前 4000 条
        return list(domains)[:4000]
    except Exception as e:
        print(f"获取 GFWList 失败: {e}")
        return []

def update_cf_split_tunnels(domains):
    if not domains:
        print("没有获取到有效域名，停止更新。")
        return

    # 构建 Cloudflare API Payload
    rules = [{"host": d, "description": "gfwlist-auto"} for d in domains]
    
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 构造请求 URL (若有 profile_id 则更新指定策略，否则更新默认)
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/devices/settings"
    if CF_PROFILE_ID:
        endpoint = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/devices/policy/{CF_PROFILE_ID}/settings"

    # 根据 Cloudflare API 结构，这里通常需要发送完整的配置
    payload = {
        "split_tunnel": {
            "mode": MODE,
            "include": rules
        }
    }

    # 注意：实际 API 操作可能需要先获取当前配置再合并，这里简化处理
    # 建议先在测试环境中通过 print 检查 payload 结构
    print(f"准备更新 {len(rules)} 条规则到 Cloudflare...")
    # response = requests.patch(endpoint, headers=headers, json=payload)
    # print(response.json())

if __name__ == "__main__":
    domains = get_gfwlist_domains()
    print(f"成功解析 {len(domains)} 条域名。")
    update_cf_split_tunnels(domains)
