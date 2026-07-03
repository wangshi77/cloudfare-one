import requests
import os

# 确保环境变量正确配置
API_TOKEN = os.getenv("CF_API_TOKEN")
ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

def main():
    headers = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}
    
    # 获取策略列表
    list_url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/devices/policy"
    res = requests.get(list_url, headers=headers)
    
    # 打印原始返回内容，这是最关键的诊断信息
    print(f"DEBUG_RAW_RESPONSE: {res.text}")
    
    # 尝试多种提取 ID 的方式
    try:
        data = res.json()
        result = data.get('result', {})
        
        # 探测结构
        if isinstance(result, list):
            print(f"结构分析: 返回的是列表 (长度: {len(result)})")
            for i, p in enumerate(result):
                print(f"  策略 {i}: ID={p.get('id')}, 名称={p.get('name')}")
        elif isinstance(result, dict):
            print(f"结构分析: 返回的是字典")
            print(f"  ID={result.get('id')}, 名称={result.get('name')}")
        else:
            print("结构分析: 未知类型")
            
    except Exception as e:
        print(f"解析错误: {e}")

if __name__ == "__main__":
    main()
