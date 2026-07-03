import requests
import os
import re
import base64

# --- 环境配置 ---
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID   = os.getenv("CF_ACCOUNT_ID")
PROFILE_ID   = os.getenv("CF_PROFILE_ID", "")
MODE         = "include"  # 强制设置为 include 模式

if not all([CF_API_TOKEN, ACCOUNT_ID]):
    raise ValueError("缺少环境变量！请检查 GitHub Secrets")

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

# --- 规则设置 ---
MAX_RULES       = 4000
TARGET_DOMAIN_N = 3900  # 将大部分配额全给域名

# --- 数据源：仅保留域名 ---
DOMAIN_URL = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"

# 合法域名正则
VALID_DOMAIN_RE = re.compile(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')

def get_domains():
    """解析 gfwlist 并提取根域名"""
    r = requests.get(DOMAIN_URL, timeout=30)
    r.raise_for_status()
    raw_content = base64.b64decode(r.text).decode('utf-8')
    domains = set()
    
    for line in raw_content.splitlines():
        if line.startswith('!') or line.startswith('[') or '@' in line or '.' not in line:
            continue
        line = line.replace('||', '').replace('|', '').replace('^', '').split('/')[0]
        if VALID_DOMAIN_RE.match(line):
            domains.add(line)
            
    unique = list(domains)
    print(f"   gfwlist 获取到 {len(unique)} 条域名")
    return unique

def update_split_tunnels(domains):
    # 只处理域名
    max_domains = min(TARGET_DOMAIN_N, len(domains))
    routes = [{"host": d, "description": "GFW Domain"} for d in domains[:max_domains]]

    print(f"   同步域名规则：{len(routes)} 条")

    if PROFILE_ID:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{PROFILE_ID}/{MODE}"
    else:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{MODE}"

    resp = requests.put(url, json=routes, headers=HEADERS)
    if resp.status_code in (200, 204):
        print(f"✅ 同步成功！Mode: {MODE}")
    else:
        print(f"❌ 失败 {resp.status_code}: {resp.text}")
        resp.raise_for_status()

if __name__ == "__main__":
    print("🔄 开始处理 GFWList 数据...")
    domains = get_domains()
    update_split_tunnels(domains)
