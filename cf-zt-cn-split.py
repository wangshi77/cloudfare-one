import requests
import os
import re
import ipaddress

# --- 配置环境变量 ---
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID   = os.getenv("CF_ACCOUNT_ID")
PROFILE_ID   = os.getenv("CF_PROFILE_ID", "")
MODE         = os.getenv("MODE", "exclude")  # exclude=CN直连 | include=只有CN走WARP
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
TARGET_DOMAIN_N = 1000  

# 域名合法性正则
VALID_DOMAIN_RE = re.compile(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')

# 数据源地址
DOMAIN_URL = "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/direct.txt"
IP_URL = "https://raw.githubusercontent.com/soffchen/GeoIP2-CN/release/CN-ip-cidr.txt"

def is_local_or_private(cidr):
    """判断是否为本地局域网、回环或链路本地地址"""
    try:
        network = ipaddress.ip_network(cidr)
        # 过滤私有网段 (RFC 1918)、回环地址 (127.0.0.0/8) 及链路本地地址 (169.254.0.0/16)
        return network.is_private or network.is_loopback or network.is_link_local
    except ValueError:
        return False

def get_cn_cidrs():
    """获取并清洗 CN IP 列表"""
    r = requests.get(IP_URL, timeout=30)
    r.raise_for_status()
    raw_lines = [line.strip() for line in r.text.splitlines() if line.strip() and not line.startswith('#')]
    
    # 执行过滤
    cidrs = [c for c in raw_lines if not is_local_or_private(c)]
    
    print(f"   IP 数据源获取到 {len(raw_lines)} 条，排除私有网段后剩余 {len(cidrs)} 条")
    return cidrs

def get_cn_domains():
    """获取并格式化域名列表"""
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
    print(f"   域名数据源获取到 {len(unique)} 条")
    return unique

def update_split_tunnels(cidrs, domains):
    """将规则推送至 Cloudflare"""
    max_domains = min(TARGET_DOMAIN_N, len(domains))
    max_ips     = min(MAX_RULES - max_domains, len(cidrs))

    domain_entries = [{"host": d, "description": "CN Domain"} for d in domains[:max_domains]]
    ip_entries     = [{"address": cidr, "description": "CN IP"} for cidr in cidrs[:max_ips]]
    routes = domain_entries + ip_entries

    print(f"   域名规则：{len(domain_entries)} 条 | IP 规则：{len(ip_entries)} 条 | 合计：{len(routes)} 条")

    if PROFILE_ID:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{PROFILE_ID}/{MODE}"
    else:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{MODE}"

    resp = requests.put(url, json=routes, headers=HEADERS)
    if resp.status_code in (200, 204):
        print(f"✅ 同步成功！")
    else:
        print(f"❌ 失败 {resp.status_code}: {resp.text}")
        resp.raise_for_status()

if __name__ == "__main__":
    print("🔄 开始拉取与清洗数据...")
    cidrs   = get_cn_cidrs()
    domains = get_cn_domains()
    update_split_tunnels(cidrs, domains)
