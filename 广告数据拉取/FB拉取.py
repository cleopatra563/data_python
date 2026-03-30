from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
import pandas as pd
import os
import datetime

# ----配置基础信息----
AD_ACCOUNT_ID = os.getenv("FB_AccountID")
APP_ID = os.getenv("FB_APPID")
APP_SECRET = os.getenv("FB_Secret")
ACCESS_TOKEN = os.getenv("FB_TOKEN")

# ----初始化 API----
def init_api():
    FacebookAdsApi.init(
        app_id=APP_ID,
        app_secret=APP_SECRET,
        access_token=ACCESS_TOKEN
    )

# ----获取数据----
def get_fb_campaign_data():
    account = AdAccount(AD_ACCOUNT_ID)

    params = {
        "level": "campaign",
        "time_range": {
            "since": "2026-02-01",
            "until": "2026-02-28"
        }
    }

    fields = [
        "campaign_id",
        "campaign_name",
        "spend",
        "impressions",
        "clicks"
    ]

    insights = account.get_insights(fields=fields, params=params)

    data = []
    for item in insights:
        data.append({
            "campaign_id": item.get("campaign_id"),
            "campaign_name": item.get("campaign_name"),
            "spend": float(item.get("spend", 0)),
            "impressions": int(item.get("impressions", 0)),
            "clicks": int(item.get("clicks", 0))
        })

    df = pd.DataFrame(data)
    df["campaign_id"] = df["campaign_id"].astype(str)
    return df

# ----保存CSV----
def save_to_csv(df):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    file_name = f"fb_campaign_data_{yesterday}.csv"

    df.to_csv(file_name, index=False, encoding="utf-8-sig")

    print(f"数据已保存: {file_name}")

# ----主流程----
def main():
    try:
        init_api()
        df = get_fb_campaign_data()

        if df.empty:
            print("未获取到数据")
            return

        print("数据获取成功，预览如下：")
        print(df.head())

        save_to_csv(df)

    except Exception as e:
        print(f"脚本异常: {str(e)}")

# ----执行入口----
if __name__ == "__main__":
    main()