import requests
import datetime
import pandas as pd
from io import StringIO

# ===== 基础配置 =====
API_TOKEN = "Fz8AH944zjSazRWN4PAd"
APP_TOKEN = "3co2hdg4sr0g" #DMG
# url = "https://dash.adjust.com/control-center/reports-service/csv_report"
url = "https://automate.adjust.com/reports-service/csv_report"

# 时间范围
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)

def init_api():
    # ===== 请求头 =====
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }
    # ===== 参数 =====
    params = {
        "app_token__in": APP_TOKEN,
        "date_period": "2026-02-01:2026-02-28",
        "dimensions": "day,country,os_name,network,campaign,creative_network,creative_id_network,adgroup_id_network,campaign_id_network",
        "metrics": "installs,clicks,impressions,events,revenue",
        "format": "csv"
    }
    return headers,params

def get_adjust_campaign_data(headers, params):
    # ===== 发请求 =====
    response = requests.get(url, headers=headers, params=params)

    # ===== 状态检查 =====
    if response.status_code != 200:
        print("请求失败")
        print(response.text)
        exit()

    print("请求成功")

    # ===== 解析CSV =====
    content = response.content.decode("utf-8", errors="ignore")
    df = pd.read_csv(StringIO(content))
    return df

def process_data(df):
    # ===== 数据清洗 =====
    df = df.drop_duplicates()

    # ===== campaign 拆解 =====
    # prefix / country / type
    df[["prefix", "country", "type"]] = df["campaign"].str.extract(r"^(\d+)-([A-Z]+)-(.+?)\s*\(")

    # campaign_id
    df["campaign_id"] = df["campaign"].str.extract(r"\((\d+)\)")
    df["campaign_id"] = df["campaign_id"].astype(str)

    # ===== 类型再拆（可选）=====
    df[["stage", "material"]] = df["type"].str.split("-", n=1, expand=True)
    return df

# ===== 保存文件 =====
def save_to_csv(df):
    file_name = f"adjust_report_{yesterday}.csv"
    df.to_csv(file_name, index=False, encoding="utf-8-sig")

    print(f"数据已保存：{file_name}")
    print(df.head())

# ===== 主流程 =====
def main():
    headers, params = init_api()
    raw_df = get_adjust_campaign_data(headers, params)
    clean_df = process_data(raw_df)
    save_to_csv(clean_df)

if __name__ == "__main__":
    main()