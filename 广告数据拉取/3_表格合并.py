from dataclasses import fields
from numpy.random import f
import pandas as pd
import glob
import os
from decimal import Decimal, InvalidOperation
import time

# ===== 文件路径 =====
ADJUST_FILE_PATTERN = "adjust_report_*.csv"
FB_FILE_PATTERN = "fb_ad_data_*.csv"

# ===== 读取最新文件 =====
def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"未找到文件: {pattern}")
    latest_file = max(files, key=os.path.getctime)
    return latest_file

def normalize_id(value):
    """统一ID格式，兼容科学计数法、.0 以及 Excel 文本包裹格式。"""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""

    # 兼容 Excel 导出的 ="123456" 文本格式
    if text.startswith('="') and text.endswith('"'):
        text = text[2:-1]

    # 兼容浮点转字符串后的尾部 .0
    if text.endswith(".0"):
        text = text[:-2]

    # 兼容科学计数法，保持长数字ID不丢位
    if "e+" in text.lower() or "e-" in text.lower():
        try:
            text = format(Decimal(text), "f")
            if "." in text:
                text = text.rstrip("0").rstrip(".")
        except (InvalidOperation, ValueError):
            pass
    return text

# ===== 主流程 =====
def main():
    # 1. 获取最新文件
    adjust_file = get_latest_file(ADJUST_FILE_PATTERN)
    fb_file = get_latest_file(FB_FILE_PATTERN)

    print(f"使用 Adjust 文件: {adjust_file}")
    print(f"使用 FB 文件: {fb_file}")

    # 2. 读取数据
    df_adjust = pd.read_csv(adjust_file, dtype={"creative_id_network": str, "campaign_id": str})
    df_fb = pd.read_csv(fb_file, dtype={"ad_id": str})

    # 3. 统一字段类型（关键）
    df_adjust["creative_id_network"] = df_adjust["creative_id_network"].apply(normalize_id)
    df_adjust["campaign_id"] = df_adjust["campaign_id"].apply(normalize_id)
    df_fb["ad_id"] = df_fb["ad_id"].apply(normalize_id)
    df_adjust["day"] = df_adjust["day"].astype(str).str.strip()
    df_fb["date"] = df_fb["date"].astype(str).str.strip()
    df_fb["account_id"] = df_fb["account_id"].astype(str).str.strip()

    # 4. 左连接（Adjust 为主表，按广告ID+日期合并）
    df = pd.merge(
        df_adjust,
        df_fb,
        left_on=["creative_id_network", "day"],
        right_on=["ad_id", "date"],
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

    # 数据去重,先排序后去重，keep='first'
    df2 = df[['day', 'os_name', 'country','events', 'campaign_id', 
        'creative_id_network', 'creative_network', 'account_id', 'ad_id', 'ad_name', 'spend',  'installs',
         'revenue','impressions_adjust','clicks_adjust',
        'impressions_fb', 'clicks_fb'
        ,'视频播放进度25%次数','视频播放进度50%次数','视频平均播放时长']].copy()
    df2.rename(columns={'impressions_fb':'impressions','clicks_fb':'clicks'}, inplace=True)

    keys = ['day','creative_id_network', 'campaign_id', 'ad_id', 'account_id']
    df2['match_prio'] = (df2['impressions'] == df2['impressions_adjust']).astype(int)
    df2 = df2.sort_values(by='match_prio',ascending = False)
    df2 = df2.drop_duplicates(subset=keys,keep='first')
    

    # 导出前将创意ID写成 Excel 文本格式，避免本地打开显示科学计数法
    df2["creative_id_network"] = df2["creative_id_network"].apply(
        lambda x: f'="{x}"' if str(x).strip() else ""
    )
    df2["campaign_id"] = df2["campaign_id"].apply(lambda x: f'="{x}"' if str(x).strip() else ""
    )
    df2["ad_id"] = df2["ad_id"].apply(lambda x: f'="{x}"' if str(x).strip() else ""
    )
    df2["account_id"] = df2["account_id"].apply(lambda x: f'="{x}"' if str(x).strip() else ""
    )

    # 6. 输出文件
    timestamp = time.strftime("%Y%m%d%H%M%S")
    output_file = f"merged_adjust_fb_{timestamp}.csv"
    df2.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"合并完成，已输出: {output_file}")
    print(df.head())


if __name__ == "__main__":
    # 结果校验
    main()

    #读最新的数据
    output_file =get_latest_file('merged_adjust_fb_*.csv')
    df_out = pd.read_csv(output_file,dtype=str).fillna("")

    print(f"\n测试文件：{output_file}")
    print(f"\n输出总行数：{len(df_out)}")

    #数据质量检查_重复数据检测
    keys = ['day','creative_id_network', 'campaign_id', 'ad_id', 'account_id']
    dup_mask = df_out.duplicated(subset=keys,keep=False)
    dup_count = int(dup_mask.sum())

    print(f"重复行数(按{keys}): {dup_count}")
    if dup_count > 0:
        print("发现重复，示例前20行:")
        print(df_out.loc[dup_mask, keys + ['impressions', 'clicks', 'spend']].head(20))
    else:
        print("未发现重复数据")