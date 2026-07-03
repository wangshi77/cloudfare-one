import requests
import os

# --- 配置区 ---
CF_API_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
CF_PROFILE_ID = os.getenv("CF_PROFILE_ID", "")
# 模式强制设为 include，表示列表内的域名走 WARP
MODE = "include" 
# 使用 V2Fly 的 GFW 列表，格式为纯域名
GFW_LIST_URL = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/gfw"

def get_domains():
    """从 V2Fly 获取域名列表"""
    try:
        response = requests.get(GFW_LIST_URL, timeout=15)
        response.raise_for_status()
        
        domains = set()
        for line in response.text.splitlines():
            line = line.strip()
            # 过滤注释、空行
            if not line or line.startswith('#'):
                continue
            # V2Fly 数据集包含域名，直接添加
            domains.add(line)
            
        # 取前 4000 条以符合 Cloudflare 限制
        return list(domains)[:4000]
    except Exception as e:
        print(f"获取域名列表失败: {e}")
        return []

def update_cf_split_tunnels(domains):
    """通过 Cloudflare API 更新策略"""
    if not domains:
        print("没有获取到有效域名，流程终止。")
        return

    # 构建 Cloudflare 规则格式
    rules = [{"host": d, "description": "gfw-auto-sync"} for d in domains]
    
    # 构造请求 URL
    base_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/devices"
    if CF_PROFILE_ID:
        endpoint = f"{base_url}/policy/{CF_PROFILE_ID}/settings"
    else:
        endpoint = f"{base_url}/settings"

    # 注意：实际生产中需要先获取原配置再 patch，
    # 下面仅展示构建后的 payload 结构
    payload = {
        "split_tunnel": {
            "mode": MODE,
            "include": rules
        }
    }
    
    print(f"成功构建 {len(rules)} 条规则。")
    print("API Payload 已准备就绪 (如需正式更新，请移除以下 print 并取消 requests.patch 注释)")
    # headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    # response = requests.patch(endpoint, headers=headers, json=payload)
    # print(f"Cloudflare 响应: {response.status_code} - {response.text}")

if __name__ == "__main__":
    domains = get_domains()
    print(f"已成功解析 {len(domains)} 条域名。")
    update_cf_split_tunnels(domains)
