import os
import sys
import datetime
import pandas as pd
import requests

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 确保当前目录在Python路径中
sys.path.append(current_dir)

# 飞书应用信息
app_id = 'cli_a94080d14d39ded0'
app_secret = 'eMIeYzPFc8yIz0CLDMXNUfIukJ8j5rDk'

# 多维表格信息
APP_TOKEN = "UQvubhvsFaaYRnsIgIUlle6ygYc"   # BASE开头
TABLE_ID = "tbl8XGNDXCY9LVxB"   # tbl开头

# 步骤1：执行Adjust拉取脚本
def run_adjust_fetch():
    print("执行Adjust拉取脚本...")
    adjust_script = os.path.join(current_dir, 'Adjust拉取.py')
    exec(open(adjust_script).read())

# 步骤2：执行FB拉取脚本
def run_fb_fetch():
    print("\n执行FB拉取脚本...")
    fb_script = os.path.join(current_dir, 'FB拉取.py')
    exec(open(fb_script).read())

# 步骤3：拼接数据
def merge_data():
    # 获取昨天的日期
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')

    # 构建文件路径
    adjust_file = os.path.join(current_dir, f"adjust_report_{yesterday_str}.csv")
    fb_file = os.path.join(current_dir, f"fb_campaign_data_{yesterday_str}.csv")

    # 检查文件是否存在
    if not os.path.exists(adjust_file):
        print(f"错误：Adjust文件 {adjust_file} 不存在")
        return None

    if not os.path.exists(fb_file):
        print(f"错误：FB文件 {fb_file} 不存在")
        return None

    # 读取CSV文件
    print("\n读取Adjust数据...")
    adjust_df = pd.read_csv(adjust_file)
    print(f"Adjust数据形状: {adjust_df.shape}")

    print("读取FB数据...")
    fb_df = pd.read_csv(fb_file)
    print(f"FB数据形状: {fb_df.shape}")

    # 拼接数据（以Adjust作为左表，通过campaign_id关联）
    print("\n拼接数据...")
    merged_df = pd.merge(adjust_df, fb_df, on='campaign_id', how='left')
    print(f"拼接后数据形状: {merged_df.shape}")

    # 保存拼接结果
    output_file = os.path.join(current_dir, f"merged_ad_data_{yesterday_str}.csv")
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n拼接结果已保存到: {output_file}")

    return merged_df

# 步骤4：写入飞书表格
def get_tenant_access_token(app_id, app_secret):
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"

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

    # 分批写入（飞书限制100条）
    batch_size = 100

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        resp = requests.post(url, headers=headers, json={
            "records": batch
        })

        print(f"写入批次 {i//batch_size + 1}")
        print(resp.status_code, resp.text)

def main():
    # 步骤1：执行Adjust拉取
    run_adjust_fetch()
    
    # 步骤2：执行FB拉取
    run_fb_fetch()
    
    # 步骤3：拼接数据
    merged_df = merge_data()
    
    if merged_df is None:
        print("数据拼接失败，无法继续执行")
        return
    
    # 步骤4：写入飞书表格
    print("\n获取飞书token...")
    token = get_tenant_access_token(app_id, app_secret)
    
    if not token:
        print("获取token失败，无法写入飞书")
        return
    
    print("\n写入飞书表格...")
    # 可选：字段清洗
    # 去掉列名空格
    merged_df.columns = [col.strip() for col in merged_df.columns]
    
    # NaN处理
    numeric_cols = ['clicks', 'impressions', 'installs', 'spend']
    for col in numeric_cols:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].astype(float).fillna(0)
    
    write_to_bitable(merged_df, token)
    
    print("\n所有任务执行完成！")

if __name__ == "__main__":
    main()