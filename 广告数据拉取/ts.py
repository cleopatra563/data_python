import requests
import datetime
import pandas as pd
from io import StringIO

# ===== 全局配置 =====
API_TOKEN = "Fz8AH944zjSazRWN4PAd"
APP_TOKEN = "3co2hdg4sr0g"

BASE_URL = "https://dash.adjust.com/control-center/reports-service/csv_report"


# ===== 1. 初始化参数 =====
def init_api():
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }

    params = {
        "app_token__in": APP_TOKEN,
        # 👉 建议改成动态时间
        # "date_period": "2026-02-01:2026-02-28",
        "date_period": get_date_range(),
        "dimensions": "day,country,os_name,network,campaign",
        "metrics": "installs,clicks,impressions,events,revenue",
        "format": "csv"
    }

    return headers, params


# ===== 时间函数（更灵活）=====
def get_date_range():
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    start = yesterday.strftime("%Y-%m-%d")
    end = yesterday.strftime("%Y-%m-%d")
    return f"{start}:{end}"


# ===== 2. 拉取 Adjust 数据 =====
def get_adjust_campaign_data(headers, params):
    try:
        response = requests.get(BASE_URL, headers=headers, params=params)

        if response.status_code != 200:
            print("❌ 请求失败")
            print(response.text)
            return None

        print("✅ 请求成功")

        content = response.content.decode("utf-8", errors="ignore")
        df = pd.read_csv(StringIO(content))

        return df

    except Exception as e:
        print("🚨 请求异常:", e)
        return None


# ===== 3. 数据处理 =====
def process_data(df):
    if df is None or df.empty:
        print("⚠️ 无数据可处理")
        return None

    # 去重
    df = df.drop_duplicates()

    # ===== campaign 拆解 =====
    df[["prefix", "country", "type"]] = df["campaign"].str.extract(
        r"^(\d+)-([A-Z]+)-(.+?)\s*\("
    )

    df["campaign_id"] = df["campaign"].str.extract(r"\((\d+)\)")
    df["campaign_id"] = df["campaign_id"].astype(str)

    # ===== type 二次拆解 =====
    df[["stage", "material"]] = df["type"].str.split("-", n=1, expand=True)

    return df


# ===== 4. 保存 CSV =====
def save_to_csv(df):
    if df is None or df.empty:
        print("⚠️ 无数据可保存")
        return

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    file_name = f"adjust_report_{yesterday}.csv"
    df.to_csv(file_name, index=False, encoding="utf-8-sig")

    print(f"✅ 数据已保存：{file_name}")


# ===== 主流程 =====
def main():
    headers, params = init_api()
    raw_df = get_adjust_campaign_data(headers, params)
    clean_df = process_data(raw_df)
    save_to_csv(clean_df)


if __name__ == "__main__":
    main()