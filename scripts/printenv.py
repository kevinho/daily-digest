import os

# 打印所有相关的环境变量
print("--- Proxy Environment Variables ---")
print(f"HTTP_PROXY:  {os.environ.get('HTTP_PROXY')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY')}")
print(f"http_proxy:  {os.environ.get('http_proxy')}")  # 小写有时也会生效
print(f"https_proxy: {os.environ.get('https_proxy')}")
print("-----------------------------------")