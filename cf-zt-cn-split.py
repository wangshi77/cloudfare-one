import requests
import os
import re

# --- 配置项 ---
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID   = os.getenv("CF_ACCOUNT_ID")
PROFILE_ID   = os.getenv("CF_PROFILE_ID", "")
MODE         = os.getenv("MODE", "exclude")
# 允许注入的域名数量，防止条目超限
TARGET_DOMAIN_N = 500 

if not all([CF_API_TOKEN, ACCOUNT_ID]):
    raise ValueError("缺少环境变量！")

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

MAX_RULES = 4000
DOMAIN_URL = "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/direct.txt"
IP_URL = "https://raw.githubusercontent.com/soffchen/GeoIP2-CN/release/CN-ip-cidr.txt"

def get_cn_cidrs():
    r = requests.get(IP_URL, timeout=30)
    r.raise_for_status()
    return [line.strip() for line in r.text.splitlines() if line.strip() and not line.startswith('#')]

def get_cn_domains():
    r = requests.get(DOMAIN_URL, timeout=30)
    r.raise_for_status()
    domains = []
    for line in r.text.splitlines():
        if 'DOMAIN-SUFFIX,' in line:
            d = line.split('DOMAIN-SUFFIX,')[-1].strip().lstrip('.')
            domains.append(f"*.{d}")
    return list(set(domains))

def update_split_tunnels(cidrs, domains):
    if PROFILE_ID:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{PROFILE_ID}/{MODE}"
    else:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{MODE}"

    # 1. 获取现有规则
    print("🔄 获取云端规则...")
    resp_get = requests.get(url, headers=HEADERS)
    existing_rules = resp_get.json().get("result", []) if resp_get.status_code == 200 else []

    # 2. 定义必须保留的“硬性规则”
    my_custom_rules = [
        # 1. 归并所有 192.168.x.x 网段
        {"address": "192.168.0.0/16", "description": "Local LAN & Docker"}, 
        # 2. 保留 10.x.x.x 和 172.16-31.x.x 等其他内网段
        {"address": "10.0.0.0/8", "description": "Private Network"},
        {"address": "172.16.0.0/12", "description": "Private Network"},
        # 3. 域名规则
        {"host": "*.cctv.com", "description": "CCTV Live"},
        {"host": "*.cntv.cn", "description": "CNTV Live"}
    ]

    # 3. 合并逻辑
    # 限制域名数量，优先保留自定义规则，再补齐 IP
    domain_entries = [{"host": d, "description": "CN Domain"} for d in domains[:TARGET_DOMAIN_N]]
    ip_entries = [{"address": c, "description": "CN IP"} for c in cidrs]
    
    # 使用字典去重
    all_rules = existing_rules + my_custom_rules + domain_entries + ip_entries
    unique_rules = { (r.get("address") or r.get("host")): r for r in all_rules }.values()
    
    final_routes = list(unique_rules)[:MAX_RULES]
    
    print(f"✅ 推送 {len(final_routes)} 条路由到 Cloudflare...")
    resp = requests.put(url, json=final_routes, headers=HEADERS)
    resp.raise_for_status()
    print("🚀 同步完成！")

if __name__ == "__main__":
    update_split_tunnels(get_cn_cidrs(), get_cn_domains())
