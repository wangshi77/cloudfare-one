import requests
import os
import re

# --- 配置项 ---
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID   = os.getenv("CF_ACCOUNT_ID")
PROFILE_ID   = os.getenv("CF_PROFILE_ID", "")
MODE         = os.getenv("MODE", "exclude")
ALLOWED_MODES = {"exclude", "include"}

if not all([CF_API_TOKEN, ACCOUNT_ID]):
    raise ValueError("缺少环境变量！请设置 CF_API_TOKEN、CF_ACCOUNT_ID")

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
        line = line.strip()
        if not line or line.startswith('#') or not line.startswith('DOMAIN-SUFFIX,'): continue
        d = line.replace('DOMAIN-SUFFIX,', '').lstrip('.')
        domains.append(f"*.{d}")
    return list(set(domains))

def update_split_tunnels(cidrs, domains):
    # 1. 设置 API URL
    if PROFILE_ID:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{PROFILE_ID}/{MODE}"
    else:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{MODE}"

    # 2. 获取云端现有规则
    print("🔄 正在获取云端现有规则...")
    resp_get = requests.get(url, headers=HEADERS)
    existing_rules = resp_get.json().get("result", []) if resp_get.status_code == 200 else []
    print(f"   云端现有 {len(existing_rules)} 条规则")

    # 3. 定义你必须保留的“硬性规则”
    my_custom_rules = [
        {"address": "172.17.0.0/16", "description": "Docker Bridge"},
        {"host": "*.cctv.com", "description": "CCTV Live"},
        {"host": "*.cntv.cn", "description": "CNTV Live"}
    ]

    # 4. 准备要注入的新规则
    new_entries = [{"host": d, "description": "CN Domain"} for d in domains] + \
                  [{"address": c, "description": "CN IP"} for c in cidrs]
    
    # 5. 合并并去重
    # 使用字典以 address 或 host 为 Key 进行合并，优先保留已有规则
    all_rules_dict = {}
    for rule in (existing_rules + my_custom_rules + new_entries):
        key = rule.get("address") or rule.get("host")
        if key and key not in all_rules_dict:
            all_rules_dict[key] = rule

    final_routes = list(all_rules_dict.values())[:MAX_RULES]
    print(f"   准备推送 {len(final_routes)} 条路由...")

    # 6. 推送更新
    resp = requests.put(url, json=final_routes, headers=HEADERS)
    if resp.status_code in (200, 204):
        print(f"✅ 同步成功！当前共 {len(final_routes)} 条规则。")
    else:
        print(f"❌ 请求失败: {resp.status_code}")
        resp.raise_for_status()

if __name__ == "__main__":
    print("🚀 开始同步任务...")
    cidrs = get_cn_cidrs()
    domains = get_cn_domains()
    update_split_tunnels(cidrs, domains)
