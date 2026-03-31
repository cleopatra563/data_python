
import requests
import pandas as pd

# ===== 飞书应用信息 =====
app_id = 'cli_a94080d14d39ded0'
app_secret = 'eMIeYzPFc8yIz0CLDMXNUfIukJ8j5rDk'

# ===== 多维表格信息 =====
APP_TOKEN = "UQvubhvsFaaYRnsIgIUlle6ygYc"   # BASE开头
TABLE_ID = "tbl8XGNDXCY9LVxB"   # tbl开头


# ===== 获取 tenant_access_token =====
def get_tenant_access_token(app_id, app_secret):
    url = "	https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"

    resp = requests.post(url, json={
        "app_id": app_id,
        "app_secret": app_secret
    })

    print("状态码:", resp.status_code)
    print("返回:", resp.text)

    data = resp.json()

    if data.get("code") != 0:
        print("获取 token 失败")
        return None

    print("token 获取成功")
    return data.get("tenant_access_token")


# ===== 写入多维表格 =====
def write_to_bitable(df, token):
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/batch_create"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json;charset=utf-8"
    }

    records = []

    for _, row in df.iterrows():
        fields = {}

        for col in df.columns:
            value = row[col]

            # 处理 NaN
            if pd.isna(value):
                value = ""

            # 防止 numpy 类型报错
            if isinstance(value, (pd.Timestamp)):
                value = str(value)

            fields[col] = value

        records.append({"fields": fields})

    # ===== 分批写入（飞书限制100条）=====
    batch_size = 100

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        resp = requests.post(url, headers=headers, json={
            "records": batch
        })

        print(f"写入批次 {i//batch_size + 1}")
        print(resp.status_code, resp.text)


# ===== 示例：构造一份测试数据 =====
def mock_data():
    data = {
        "day":'2026-03-30',
        "os_name": "os_name",
        "campaign_id": ["123", "456"],
        "campaign_name": ["test_A", "test_B"],
        "installs": [100,200],
        "spend": [100.5, 200.0],
        "impressions": [100.0, 200.0],
        "clicks": [10, 20]
    }
    return pd.DataFrame(data)


# ===== 主流程 =====
if __name__ == "__main__":
    token = get_tenant_access_token(app_id, app_secret)

    if not token:
        exit()

    # ===== 读取CSV =====
    file_path = "merged_adjust_fb.csv"
    df = pd.read_csv(file_path,dtype = {"campaign_id":str})


    # ===== 可选：字段清洗（建议）=====
    # 去掉列名空格
    df.columns = [col.strip() for col in df.columns]

    # NaN处理（也可以交给 write_to_bitable）
    numeric_cols = ['clicks', 'impressions', 'installs', 'spend']
    for col in numeric_cols:
        df[col] = df[col].astype(float).fillna(0)

    # ===== 写入飞书 =====
    write_to_bitable(df, token)

# if __name__ == "__main__":
#     token = get_tenant_access_token(app_id, app_secret)
#
#     if not token:
#         exit()
#     # 这里你可以换成你的 merged df
#     df = mock_data()
#     write_to_bitable(df, token)