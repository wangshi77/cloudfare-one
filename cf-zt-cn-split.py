import requests
import os
import re

CF_API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID   = os.getenv("CF_ACCOUNT_ID")
PROFILE_ID   = os.getenv("CF_PROFILE_ID", "")
MODE         = os.getenv("MODE", "exclude") 
ALLOWED_MODES = {"exclude", "include"}

if not all([CF_API_TOKEN, ACCOUNT_ID]):
    raise ValueError("缺少环境变量！")

HEADERS = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}

MAX_RULES       = 4000
TARGET_DOMAIN_N = 1000  

# 核心：定义所有需要豁免/强制包含的本地及 OrbStack 网段
PRIVATE_NETWORKS = [
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", 
    "127.0.0.0/8", "169.254.0.0/16", 
    "172.17.0.0/16", "172.18.0.0/16", "172.19.0.0/16"，"10.0.0.0/8"
]

def get_cn_cidrs():
    r = requests.get("https://raw.githubusercontent.com/soffchen/GeoIP2-CN/release/CN-ip-cidr.txt", timeout=30)
    r.raise_for_status()
    cidrs = [line.strip() for line in r.text.splitlines() if line.strip() and not line.startswith('#')]
    # 合并并去重
    return list(set(PRIVATE_NETWORKS + cidrs))

def update_split_tunnels(cidrs, domains):
    # 确保私有网段排在最前面，赋予最高优先级
    other_cidrs = [c for c in cidrs if c not in PRIVATE_NETWORKS]
    sorted_cidrs = PRIVATE_NETWORKS + other_cidrs
    
    # 限制总数
    max_domains = min(TARGET_DOMAIN_N, len(domains))
    max_ips = min(MAX_RULES - max_domains, len(sorted_cidrs))

    routes = [{"host": d, "description": "CN Domain"} for d in domains[:max_domains]] + \
             [{"address": c, "description": "Local/CN IP"} for c in sorted_cidrs[:max_ips]]

    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{PROFILE_ID + '/' if PROFILE_ID else ''}{MODE}"
    resp = requests.put(url, json=routes, headers=HEADERS)
    
    if resp.status_code in (200, 204):
        print(f"✅ 同步成功！已包含本地及 OrbStack 网段。")
    else:
        print(f"❌ 失败: {resp.text}")
        resp.raise_for_status()

if __name__ == "__main__":
    cidrs = get_cn_cidrs()
    # 域名获取逻辑保持不变...
    # (省略域名部分以保持篇幅，请直接复用之前的 get_cn_domains 函数)
    update_split_tunnels(cidrs, []) # 确保传入域名列表
