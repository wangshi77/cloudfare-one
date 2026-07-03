import requests
import os
import re
import base64

# --- 环境配置 ---
# 请确保你在运行前已经在终端设置了这些环境变量
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID   = os.getenv("CF_ACCOUNT_ID")
PROFILE_ID   = os.getenv("CF_PROFILE_ID", "")
MODE         = "include" 

if not all([CF_API_TOKEN, ACCOUNT_ID]):
    raise ValueError("错误：未找到 CF_API_TOKEN 或 CF_ACCOUNT_ID，请检查环境变量设置")

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json"
}

# --- 设置 ---
MAX_RULES       = 4000
TARGET_DOMAIN_N = 3900 # 域名配额

DOMAIN_URL = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
VALID_DOMAIN_RE = re.compile(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')

def get_domains():
    print("正在拉取并解析 GFWList...")
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
    print(f"成功获取到 {len(unique)} 条域名")
    return unique

def update_split_tunnels(domains):
    max_domains = min(TARGET_DOMAIN_N, len(domains))
    routes = [{"host": d, "description": "GFW Domain"} for d in domains[:max_domains]]

    print(f"正在同步 {len(routes)} 条规则到 Cloudflare...")

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

# 仅通过手动执行脚本调用
if __name__ == "__main__":
    domains = get_domains()
    update_split_tunnels(domains)
    print("脚本执行完毕，已退出。")
