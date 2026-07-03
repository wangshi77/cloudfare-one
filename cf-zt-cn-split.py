import requests
import os
import json

# 配置
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
# 这是你刚才探测出的路径
SETTINGS_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/settings"

def get_gfwlist_rules():
    # 保持原有的 CN IP 规则
    rules = [
        {"address": "94.191.0.0/17", "description": "CN IP"},
        {"address": "93.183.18.0/24", "description": "CN IP"},
        {"address": "93.183.14.0/24", "description": "CN IP"},
        {"address": "1.1.8.0/24", "description": "CN IP"}
    ]
    # 这里可以添加你需要的 GFWList 域名逻辑
    # 为了演示，先手动添加一个
    rules.append({"host": "*.google.com"}) 
    return rules

def main():
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    # 1. 获取当前线上完整配置
    res = requests.get(SETTINGS_URL, headers=headers)
    if res.status_code != 200:
        print(f"❌ 读取失败: {res.text}")
        return
    
    current_config = res.json().get('result', {})
    
    # 2. 注入新规则
    new_rules = get_gfwlist_rules()
    current_config['exclude'] = new_rules
    
    # 3. 将完整的、结构正确的对象回写 (使用 PUT)
    print("🚀 正在回写完整配置以确保控制台可见...")
    res_put = requests.put(SETTINGS_URL, json=current_config, headers=headers)
    
    if res_put.status_code == 200:
        print("🎉 同步成功！Cloudflare 控制台现在应该能正常显示规则了。")
    else:
        print(f"❌ 同步失败: {res_put.text}")

if __name__ == "__main__":
    main()
