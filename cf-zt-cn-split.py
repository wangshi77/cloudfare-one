

import requests
import os
import re

CF_API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID   = os.getenv("CF_ACCOUNT_ID")
PROFILE_ID   = os.getenv("CF_PROFILE_ID", "")
MODE         = os.getenv("MODE", "exclude")
ALLOWED_MODES = {"exclude", "include"}

if not all([CF_API_TOKEN, ACCOUNT_ID]):
    raise ValueError("缺少环境变量！请在 GitHub Secrets 设置 CF_API_TOKEN、CF_ACCOUNT_ID")

if MODE not in ALLOWED_MODES:
    raise ValueError(f"非法 MODE: {MODE}，只允许 {'/'.join(sorted(ALLOWED_MODES))}")

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

MAX_RULES       = 4000
TARGET_DOMAIN_N = 0 

VALID_DOMAIN_RE = re.compile(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')
DOMAIN_URL = "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/direct.txt"
IP_URL = "https://raw.githubusercontent.com/soffchen/GeoIP2-CN/release/CN-ip-cidr.txt"

def get_cn_cidrs():
    r = requests.get(IP_URL, timeout=30)
    r.raise_for_status()
    cidrs = [line.strip() for line in r.text.splitlines() if line.strip() and not line.startswith('#')]
    print(f"   IP 数据源获取到 {len(cidrs)} 条 CIDR")
    return cidrs

def get_cn_domains():
    r = requests.get(DOMAIN_URL, timeout=30)
    r.raise_for_status()
    domains = []
    for line in r.text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'): continue
        if line.startswith('DOMAIN-SUFFIX,'): line = line.replace('DOMAIN-SUFFIX,', '').strip()
        line = line.lstrip('.')
        if line and VALID_DOMAIN_RE.match(line):
            domains.append(f"*.{line}")
    unique = list(set(domains))
    print(f"   域名数据源获取到 {len(unique)} 条域名（已过滤非法格式）")
    return unique

def update_split_tunnels(cidrs, domains):
    # --- 你的自定义网段 ---
    custom_routes = [
        {"address": "172.17.0.0/16", "description": "Docker Bridge"},
        {"address": "192.168.0.0/16", "description": "Home/Office LAN"},
        {"address": "10.0.0.0/8", "description": "Private Network"}
    ]
    
    max_domains = min(TARGET_DOMAIN_N, len(domains))
    max_ips     = min(MAX_RULES - max_domains - len(custom_routes), len(cidrs))

    domain_entries = [{"host": d, "description": "CN Domain"} for d in domains[:max_domains]]
    ip_entries     = [{"address": cidr, "description": "CN IP"} for cidr in cidrs[:max_ips]]
    
    # 强制拼接自定义网段
    routes = domain_entries + custom_routes + ip_entries

    print(f"   注入自定义网段：{len(custom_routes)} 条 | 域名：{len(domain_entries)} 条 | IP：{len(ip_entries)} 条")
    print(f"   合计：{len(routes)} 条")

    if PROFILE_ID:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{PROFILE_ID}/{MODE}"
    else:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{MODE}"

    resp = requests.put(url, json=routes, headers=HEADERS)
    if resp.status_code in (200, 204):
        print(f"✅ 同步成功！{len(routes)} 条路由 | Mode: {MODE}")
    else:
        print(f"❌ 失败 {resp.status_code}: Cloudflare API 请求未成功")
        resp.raise_for_status()

if __name__ == "__main__":
    print("🔄 拉取最新 CN geo 数据...")
    cidrs   = get_cn_cidrs()
    domains = get_cn_domains()
    update_split_tunnels(cidrs, domains)
