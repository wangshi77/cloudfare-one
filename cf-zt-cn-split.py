import os
import requests
import json

# 配置 (保持原样)
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_PROFILE_ID = os.getenv("CF_PROFILE_ID", "")
# 修改点1：改为 include 模式以匹配 GFWList 的逻辑
MODE = "include" 

# 修改点2：替换为 Loyalsoldier 的 GFW 列表 (纯域名格式，最稳定)
DOMAIN_URL = "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/gfw.txt"

def get_data():
    # 逻辑简化：只拉取 GFWList
    try:
        print("🔄 拉取最新 GFW 域名数据...")
        resp = requests.get(DOMAIN_URL, timeout=15)
        # 过滤掉注释和空行
        domains = [line.strip() for line in resp.text.splitlines() 
                   if line.strip() and not line.startswith(('#', '!'))]
        
        # 保持原有的逻辑：取前 4000 条
        final_domains = domains[:4000]
        print(f"域名数据获取到 {len(final_domains)} 条")
        return final_domains
    except Exception as e:
        print(f"数据获取失败: {e}")
        return []

def update_cf(domains):
    if not domains:
        print("无数据，跳过更新")
        return

    # 构建规则 (保持原格式)
    rules = [{"host": d, "description": "gfw-auto-sync"} for d in domains]
    
    # API 调用 (保持原逻辑)
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/devices/settings"
    if CF_PROFILE_ID:
        endpoint = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/devices/policy/{CF_PROFILE_ID}/settings"

    payload = {"split_tunnel": {"mode": MODE, "include": rules}}

    # 发送请求
    r = requests.patch(endpoint, headers=headers, json=payload)
    if r.status_code == 200:
        print(f"✅ 同步成功！{len(domains)} 条路由 | Mode: {MODE}")
    else:
        print(f"❌ 同步失败: {r.text}")

if __name__ == "__main__":
    data = get_data()
    update_cf(data)
