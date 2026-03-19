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
from facebook_business.adobjects.adsinsights import AdsInsights
import pandas as pd
from datetime import datetime,timedelta

# ----步骤1：配置基础信息----
ACCESS_TOKEN = 'EAA8ZAobXXw6kBRBBYlzECbG5GhQizAvCEtkazhetZBdujadxy1Q1fkZCwH1d7IffoRIz0OlEyqvT08ZC0hsx1WGeWjR7wEnD5kCs4FQi9ToB5OxvoIYy8zJszPsM6zOk7eA6ibHE7oOVq4jmGIbivrPw5RHRcssSVE2GqoVZCTx0wGtVrZB1hLzZCucZB5htzQZDZD' # 你的token访问令牌
APP_ID = '4250306981905321' # 你的应用ID
APP_SECRET = 'adf87c091a43c70e53b04e533c469e84' # 你的secret
AD_ACCOUNT_ID = 'act_1379725066317604' # 你的广告账户

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
    获取当日广告花费（严格今日）
    """
    account = AdAccount(AD_ACCOUNT_ID)

    today = datetime.now().strftime('%Y-%m-%d')

    params = {
        "level": "account",   # 先用account级，避免重复
        "time_range": {
            "since": today,
            "until": today
        }
    }

    fields = [
        "spend"
    ]

    insights = account.get_insights(fields=fields, params=params)

    total_spend = 0
    for item in insights:
        total_spend += float(item.get("spend", 0))

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
