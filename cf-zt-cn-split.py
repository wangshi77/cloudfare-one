import os
import requests
import json

# --- 配置区 ---
# 确保你在环境变量或执行环境中设置了以下值
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_PROFILE_ID = os.getenv("CF_PROFILE_ID", "")
MODE = "include" 
DOMAIN_URL = "https://cdn.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/gfw.txt"

def get_data():
    """拉取 GFWList 纯域名数据"""
    try:
        print("🔄 正在从源拉取域名列表...")
        resp = requests.get(DOMAIN_URL, timeout=20)
        resp.raise_for_status()
        # 过滤注释与空行
        domains = [line.strip() for line in resp.text.splitlines() 
                   if line.strip() and not line.startswith(('#', '!'))]
        
        final_domains = list(set(domains))[:4000]
        print(f"✅ 获取到 {len(final_domains)} 条域名")
        return final_domains
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return []

def update_cf(domains):
    if not domains:
        print("无数据，跳过更新")
        return

    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}", 
        "Content-Type": "application/json"
    }
    
    # 确定 API 路径
    base_endpoint = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/devices"
    endpoint = f"{base_endpoint}/policy/{CF_PROFILE_ID}/settings" if CF_PROFILE_ID else f"{base_endpoint}/settings"

    # 1. 获取现有配置 (必须，否则 PATCH/PUT 会导致配置丢失)
    print("正在从 Cloudflare 获取现有设置...")
    resp_get = requests.get(endpoint, headers=headers)
    if resp_get.status_code != 200:
        print(f"❌ 获取现有配置失败: {resp_get.status_code} - {resp_get.text}")
        return
    
    current_settings = resp_get.json().get("result", {})
    
    # 2. 注入 Split Tunnel 新规则
    rules = [{"host": d, "description": "gfw-auto-sync"} for d in domains]
    current_settings["split_tunnel"] = {"mode": MODE, "include": rules}
    
    # 3. 使用 PUT 覆盖更新
    print("正在提交更新到 Cloudflare...")
    resp_put = requests.put(endpoint, headers=headers, json=current_settings)
    
    if resp_put.status_code == 200:
        print(f"🎉 同步成功！{len(domains)} 条域名已更新到策略。")
    else:
        print(f"❌ 同步失败: {resp_put.status_code} - {resp_put.text}")

if __name__ == "__main__":
    if not CF_API_TOKEN or not CF_ACCOUNT_ID:
        print("❌ 错误：请先设置 CF_API_TOKEN 和 CF_ACCOUNT_ID 环境变量")
    else:
        data = get_data()
        update_cf(data)
