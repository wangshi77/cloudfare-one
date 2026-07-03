import requests
import os

# 直接使用环境变量
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def main():
    # 1. 获取所有策略
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
    res = requests.get(url, headers=headers)
    
    if res.status_code != 200:
        print(f"API 获取策略失败: {res.text}")
        return

    data = res.json()
    # 兼容处理：无论 result 是列表还是字典，都转为列表处理
    policies = data.get('result', [])
    if isinstance(policies, dict):
        policies = [policies]

    # 2. 找到第一个默认策略
    target = next((p for p in policies if p.get('default') == True), None)
    if not target:
        print("未找到默认策略，请检查账户配置")
        return
        
    policy_id = target.get('policy_id')
    print(f"目标策略 ID: {policy_id}")

    # 3. 构造与开源项目一致的 payload
    # 这里直接填入你需要同步的 GFWList 规则列表
    rules = [{"address": "94.191.0.0/17", "description": "CN IP"}] # 你可以在此扩充
    
    payload = {
        "split_tunnel": {
            "mode": "exclude",
            "include": [],
            "exclude": rules
        }
    }

    # 4. 执行 PATCH
    target_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy/{policy_id}"
    res = requests.patch(target_url, json=payload, headers=headers)
    
    if res.status_code == 200:
        print("同步成功！")
    else:
        print(f"同步失败: {res.text}")

if __name__ == "__main__":
    main()
