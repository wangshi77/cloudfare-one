import requests
import os
import re
import base64

# --- 环境配置 ---
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID   = os.getenv("CF_ACCOUNT_ID")
PROFILE_ID   = os.getenv("CF_PROFILE_ID", "")
MODE         = os.getenv("MODE", "include")  # 推荐使用 include
ALLOWED_MODES = {"exclude", "include"}

if not all([CF_API_TOKEN, ACCOUNT_ID]):
    raise ValueError("缺少环境变量！请检查 GitHub Secrets")

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

# --- 规则限制 ---
MAX_RULES       = 4000
TARGET_DOMAIN_N = 3000  # 限制域名数量，避免 API 报错

# --- 数据源配置 ---
DOMAIN_URL = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"


# 合法域名正则
VALID_DOMAIN_RE = re.compile(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')

def get_cn_cidrs():
    r = requests.get(IP_URL, timeout=30)
    r.raise_for_status()
    cidrs = [line.strip() for line in r.text.splitlines() if line.strip() and not line.startswith('#')]
    print(f"   IP 数据源获取到 {len(cidrs)} 条 CIDR")
    return cidrs

def get_cn_domains():
    """解析 gfwlist 并提取根域名"""
    r = requests.get(DOMAIN_URL, timeout=30)
    r.raise_for_status()
    # 解码 gfwlist
    raw_content = base64.b64decode(r.text).decode('utf-8')
    domains = set()
    
    for line in raw_content.splitlines():
        # 简单过滤
        if line.startswith('!') or line.startswith('[') or '@' in line or '.' not in line:
            continue
        # 清除特殊符号
        line = line.replace('||', '').replace('|', '').replace('^', '').split('/')[0]
        # 校验格式
        if VALID_DOMAIN_RE.match(line):
            domains.add(line)
            
    unique = list(domains)
    print(f"   gfwlist 获取到 {len(unique)} 条域名")
    return unique

def update_split_tunnels(cidrs, domains):
    max_domains = min(TARGET_DOMAIN_N, len(domains))
    max_ips     = min(MAX_RULES - max_domains, len(cidrs))

    # 构造请求体
    domain_entries = [{"host": d, "description": "GFW Domain"} for d in domains[:max_domains]]
    ip_entries     = [{"address": cidr, "description": "CN IP"} for cidr in cidrs[:max_ips]]
    routes = domain_entries + ip_entries

    print(f"   域名规则：{len(domain_entries)} 条 | IP 规则：{len(ip_entries)} 条 | 合计：{len(routes)} 条")

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
    print("🔄 开始处理 GFWList 与 IP 数据...")
    cidrs   = get_cn_cidrs()
    domains = get_cn_domains()
    update_split_tunnels(cidrs, domains)
