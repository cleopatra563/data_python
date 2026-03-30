# !/usr/bin/env python3
# token  放入到环境变量中
# 拉取安装数、付费数
import requests
import json
import pandas as pd
import numpy as np
import os

def get_adjust_creative_report(api_token, app_token):
    url = "https://automate.adjust.com/reports-service/report"
    params = {
        "app_token__in": app_token,
        "dimensions": "creative_id_network,country_code,partner_name",
        "metrics": "installs,clicks,impressions,network_cost,ecpm",
        "date_period": "2026-02-01:2026-02-28",
        "ad_spend_mode": "adjust" #network,adjust,mixed
    }
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"请求失败，状态码：{response.status_code}")
            print(f"错误详情：{response.text}")
            return None
    except Exception as e:
        print(f"发生异常：{e}")
        return None
api_token = 'Fz8AH944zjSazRWN4PAd'
dmg_app_token,og_app_token = '3co2hdg4sr0g','5xcjqsb8drls'
report_data = get_adjust_creative_report(api_token, dmg_app_token)
df = pd.DataFrame(report_data['rows'])
df['network_cost'] = pd.to_numeric(df['network_cost'], errors='coerce')
df['installs'] = pd.to_numeric(df['installs'], errors='coerce')
df['cpi'] = df['network_cost'] / df['installs']
df_filtered = df[
    (df['cpi'] > 0) &
    (df['cpi'] != np.inf) &
    (df['cpi'].notna())].sort_values(by='cpi', ascending=False)