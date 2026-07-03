import requests
import base64
import re
import os

API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def get_gfwlist_domains():
    url = "https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt"
    try:
        response = requests.get(url, timeout=10)
        content = base64.b64decode(response.text).decode('utf-8')
        domains = re.findall(r'\|\|([a-zA-Z0-9\.-]+)', content)
        return list(set(domains))
    except:
        return []

def main():
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    # --- 第一步：获取正确的 POLICY_ID ---
    list_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
    res_list = requests.get(list_url, headers=headers)
    
    if res_list.status_code != 200:
        print(f"❌ 获取列表失败: {res_list.text}")
        return

    policies = res_list.json().get('result', [])
    if not policies:
        print("❌ 未找到任何策略！")
        return

    # 自动选择第一个可用的策略 ID
    target_id = policies[0]['id']
    print(f"✅ 已锁定有效策略 ID: {target_id}")

    # --- 第二步：准备并同步规则 ---
    domains = get_gfwlist_domains()
    # 限制数量到 500 以防触发 API 限制
    rules = [{"address": "192.168.0.0/16", "description": "Local LAN"}]
    for d in domains[:500]:
        rules.append({"host": f"*.{d}", "description": "Auto GFWList"})
    
    # 构造 payload：根据以前成功的逻辑，使用 split_tunnel 结构
    # 注意：如果这报错，请去掉 'split_tunnel' 这一层包裹直接传 include
    payload = {
        "split_tunnel": {
            "mode": "include",
            "include": rules
        }
    }
    
    sync_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{target_id}"
    
    print(f"🚀 正在发送同步请求...")
    res = requests.patch(sync_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("🎉 同步成功！")
    else:
        print(f"❌ 同步失败 ({res.status_code}): {res.text}")
        # 如果 patch 报错，尝试直接更新 split_tunnel 子资源
        print("💡 尝试备选逻辑：直接更新 split_tunnel 资源...")
        alt_url = f"{sync_url}/split_tunnel"
        res_alt = requests.put(alt_url, json={"mode": "include", "include": rules}, headers=headers)
        print(f"备选同步结果: {res_alt.status_code} - {res_alt.text}")

if __name__ == "__main__":
    main()
