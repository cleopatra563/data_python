# !/usr/bin/env python3

"""
预安装库：Meta官方PythonSDK facebook_business
具备功能：
1、获取指定广告账户的当日花费
2、判断是否超过预算
3、超过则触发告警
4、最小可用版本

核心思路：
1、用MarketingAPI拉取花费、展示、点击
2、做简单阈值判断（花费超预算）
3、触发告警（打印/飞书Webhook）

脚本关键：
1、稳定拿数
2、定时执行（cron/Airflow）
3、告警闭环
"""

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
import pandas as pd
from datetime import datetime

# ----步骤1：配置基础信息----
ACCESS_TOKEN = 'YOUR_ACCESS_TOKEN_HERE' # 你的token
APP_ID = 'YOUR_APP_ID_HERE' # 你的app_id
APP_SECRET = 'YOUR_APP_SECRET_HERE' # 你的secret
AD_ACCOUNT_ID = 'YOUR_AD_ACCOUNT_ID_HERE' # 你的广告账户

DAILY_BUDGET = 100 #美元预算

# ----步骤2：初始化API----
def init_api():
    """
    初始化 Facebook API
    """
    FacebookAdsApi.init(
        app_id=APP_ID,
        app_secret=APP_SECRET,
        access_token=ACCESS_TOKEN
    )

# ----步骤3：调用API获取Insights数据----
def get_spend():
    """
    获取当日广告花费
    """
    account = AdAccount(AD_ACCOUNT_ID) # 拿到对应账户
    params = {
        "time_range":{
            "since":datetime.now().strftime('%Y-%m-%d'),
            "until":datetime.now().strftime('%Y-%m-%d')
        }
    }
    fields = [
        "campaign_name",
        "adset_name",
        "spend",
        "impressions", # 曝光量
        "clicks", #点击量
        "cpc", #平均点击成本
        "ctr" #点击率
    ]

    instights = account.get_insights(fields = fields,params = params) # 获取数据 对应HTTP API GET/act_xxx/insights
    total_spend = 0

    for item in instights:
        total_spend += float(item.get("spend",0))
    return total_spend

# ----步骤4：逻辑监控与报警----
def alert(msg):
    """
    告警函数(目前使用print，可接飞书)
    """
    print("🚨 ALERT:", msg)

# ----主流程----
def main():
    try:
        init_api()
        spend = get_spend()
        print(f"今日花费:${spend}")

        #预算判断
        if spend > DAILY_BUDGET:
            alert(f"花费超预算：{spend} > {DAILY_BUDGET}")
        else:
            print("花费正常")
    except Exception as e:
        alert(f"脚本异常：{str(e)}")

# ----执行入口----
if __name__ == '__main__':
    main()
