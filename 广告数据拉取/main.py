import pandas as pd
import glob
import os

# ===== 文件路径 =====
ADJUST_FILE_PATTERN = "adjust_report_*.csv"
FB_FILE_PATTERN = "fb_campaign_data_*.csv"

# ===== 读取最新文件 =====
def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"未找到文件: {pattern}")
    latest_file = max(files, key=os.path.getctime)
    return latest_file

# ===== 主流程 =====
def main():
    # 1. 获取最新文件
    adjust_file = get_latest_file(ADJUST_FILE_PATTERN)
    fb_file = get_latest_file(FB_FILE_PATTERN)

    print(f"使用 Adjust 文件: {adjust_file}")
    print(f"使用 FB 文件: {fb_file}")

    # 2. 读取数据
    df_adjust = pd.read_csv(adjust_file,dtype={"campaign_id":str})
    df_fb = pd.read_csv(fb_file,dtype={"campaign_id":str})

    # 3. 统一字段类型（关键）
    df_adjust["campaign_id"] = df_adjust["campaign_id"].astype(str)
    df_fb["campaign_id"] = df_fb["campaign_id"].astype(str)

    # 4. 左连接（Adjust 为主表）
    df = pd.merge(
        df_adjust,
        df_fb,
        on="campaign_id",
        how="left",
        suffixes=("_adjust", "_fb")
    )

    # 5. 基础清洗（可选）
    # 数值列 → 填 0
    num_cols = df.select_dtypes(include=["number"]).columns
    df[num_cols] = df[num_cols].fillna(0)

    # 字符串列 → 填空字符串
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    df[str_cols] = df[str_cols].fillna("")

    # 6. 输出文件
    output_file = "merged_adjust_fb.csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"合并完成，已输出: {output_file}")
    print(df.head())


if __name__ == "__main__":
    main()
