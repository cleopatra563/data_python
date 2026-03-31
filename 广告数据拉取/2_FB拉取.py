from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
import pandas as pd
import os
import datetime

# ----配置基础信息----
AD_ACCOUNT_IDS = [account_id.strip() for account_id in os.getenv("FB_AccountID").split(";") if account_id.strip()]
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
    params = {
        "level": "ad",
        "time_increment": 1,
        "time_range": {
            "since": "2026-02-01",
            "until": "2026-02-28"
        }
    }

    fields = [
        "date_start",
        "account_id",
        "ad_id",
        "ad_name",
        "spend",
        "impressions",
        "clicks",
        "video_p25_watched_actions",
        "video_p50_watched_actions",
        "video_avg_time_watched_actions"
    ]
    
    def get_action_value(actions):
        if not actions:
            return 0.0
        if isinstance(actions, list) and len(actions) > 0:
            return float(actions[0].get("value", 0))
        return 0.0

    data = []
    for account_id in AD_ACCOUNT_IDS:
        account = AdAccount(account_id)
        insights = account.get_insights(fields=fields, params=params)

        for item in insights:
            impressions = int(item.get("impressions", 0))
            # video_3s = get_action_value(item.get("video_3_sec_watched_actions"))

            data.append({
                "date": item.get("date_start"),
                "account_id": item.get("account_id"),
                "ad_id": item.get("ad_id"),
                "ad_name": item.get("ad_name"),
                "spend": float(item.get("spend", 0)),
                "impressions": impressions,
                "clicks": int(item.get("clicks", 0)),
                # "单次展示的播放视频达3s率": (video_3s / impressions) if impressions > 0 else 0.0,
                "视频播放进度25%次数": get_action_value(item.get("video_p25_watched_actions")),
                "视频播放进度50%次数": get_action_value(item.get("video_p50_watched_actions")),
                "视频平均播放时长": get_action_value(item.get("video_avg_time_watched_actions"))
            })

    df = pd.DataFrame(data)
    df["account_id"] = df["account_id"].astype(str)
    df["ad_id"] = df["ad_id"].astype(str)
    return df

# ----保存CSV----
def save_to_csv(df):
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    file_name = f"fb_ad_data_{yesterday}.csv"

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