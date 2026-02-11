#从ST的API获取数据
import requests


def get_timezone_by_ip(ip_address):
    # 使用在线 API 示例 (如 ip-api.com)
    url = f"http://ip-api.com/json/{ip_address}?fields=status,message,timezone"
    response = requests.get(url).json()

    if response['status'] == 'success':
        return response['timezone']  # 返回如 "America/New_York"
    else:
        return "Unknown"


# 假设用户 IP
user_ip = "101.226.103.6"
print(f"该 IP 对应的地理时区是: {get_timezone_by_ip(user_ip)}")

