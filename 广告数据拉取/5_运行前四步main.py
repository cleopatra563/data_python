"""
main.py — 主调度脚本
按顺序执行：
  1. Adjust 数据拉取
  2. Facebook 数据拉取
  3. 表格合并
  4. 写入飞书多维表格

使用说明：
  将 main.py 与四个脚本放在同一目录下，直接运行：
      python main.py
"""

import sys
import traceback
import importlib.util
import pathlib
import pandas as pd


# ──────────────────────────────────────────────
# 动态加载模块（处理文件名以数字/中文开头的情况）
# ──────────────────────────────────────────────
def load_module(filename: str, alias: str):
    """根据文件名动态加载 Python 模块，返回 module 对象。"""
    path = pathlib.Path(__file__).parent / filename
    if not path.exists():
        raise FileNotFoundError(f"找不到脚本文件: {path}")
    spec = importlib.util.spec_from_file_location(alias, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────
def step_banner(n: int, title: str):
    print(f"\n{'='*55}")
    print(f"  Step {n}: {title}")
    print(f"{'='*55}")


# ──────────────────────────────────────────────
# Step 1 — Adjust 数据拉取
# ──────────────────────────────────────────────
def run_step1():
    step_banner(1, "Adjust 数据拉取")
    m = load_module("1_Adjust拉取.py", "adjust")

    headers, params = m.init_api()
    raw_df   = m.get_adjust_campaign_data(headers, params)
    clean_df = m.process_data(raw_df)
    m.save_to_csv(clean_df)

    print("✅ Step 1 完成")
    return clean_df


# ──────────────────────────────────────────────
# Step 2 — Facebook 数据拉取
# ──────────────────────────────────────────────
def run_step2():
    step_banner(2, "Facebook 数据拉取")
    m = load_module("2_FB拉取.py", "fb")

    m.init_api()
    df = m.get_fb_campaign_data()

    if df.empty:
        raise ValueError("FB 数据为空，请检查账号配置或时间范围")

    m.save_to_csv(df)
    print("✅ Step 2 完成")
    return df


# ──────────────────────────────────────────────
# Step 3 — 表格合并
# ──────────────────────────────────────────────
def run_step3():
    step_banner(3, "表格合并 (Adjust ← FB 左连接)")
    m = load_module("3_表格合并.py", "merge")

    adjust_file = m.get_latest_file(m.ADJUST_FILE_PATTERN)
    fb_file     = m.get_latest_file(m.FB_FILE_PATTERN)
    print(f"  Adjust 文件: {adjust_file}")
    print(f"  FB     文件: {fb_file}")

    df_adjust = pd.read_csv(adjust_file, dtype={"campaign_id": str})
    df_fb     = pd.read_csv(fb_file,     dtype={"campaign_id": str})

    df_adjust["campaign_id"] = df_adjust["campaign_id"].astype(str)
    df_fb["campaign_id"]     = df_fb["campaign_id"].astype(str)

    # 左连接，Adjust 为主表
    df = pd.merge(
        df_adjust, df_fb,
        on="campaign_id",
        how="left",
        suffixes=("_adjust", "_fb")
    )

    # 数值列填 0，字符串列填空字符串
    num_cols = df.select_dtypes(include=["number"]).columns
    df[num_cols] = df[num_cols].fillna(0)
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    df[str_cols] = df[str_cols].fillna("")

    # 取目标列并重命名
    df_out = df[[
        "day", "os_name", "campaign_id", "campaign_name",
        "installs", "spend", "impressions_fb", "clicks_fb"
    ]].copy()
    df_out.rename(columns={
        "impressions_fb": "impressions",
        "clicks_fb":      "clicks"
    }, inplace=True)

    output_file = "merged_adjust_fb.csv"
    df_out.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"  合并完成 → {output_file}  ({len(df_out)} 行)")
    print("✅ Step 3 完成")
    return df_out



# ──────────────────────────────────────────────
# Step 4 — 写入飞书多维表格
# ──────────────────────────────────────────────
def run_step4(df: pd.DataFrame):
    step_banner(4, "写入飞书多维表格")
    m = load_module("4_写入飞书表格.py", "feishu")

    token = m.get_tenant_access_token(m.app_id, m.app_secret)
    if not token:
        raise RuntimeError("获取飞书 tenant_access_token 失败，请检查 app_id / app_secret")

    # 字段清洗
    df = df.copy()
    df.columns = [col.strip() for col in df.columns]
    for col in ["clicks", "impressions", "installs", "spend"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)

    m.write_to_bitable(df, token)
    print("✅ Step 4 完成")


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────
def main():
    print("\n🚀 数据管道启动\n")

    try:
        run_step1()
    except Exception:
        print("Step 1 失败，管道终止")
        traceback.print_exc()
        sys.exit(1)

    try:
        run_step2()
    except Exception:
        print("Step 2 失败，管道终止")
        traceback.print_exc()
        sys.exit(1)

    try:
        merged_df = run_step3()
    except Exception:
        print("Step 3 失败，管道终止")
        traceback.print_exc()
        sys.exit(1)

    try:
        run_step4(merged_df)
    except Exception:
        print("Step 4 失败，管道终止")
        traceback.print_exc()
        sys.exit(1)

    print("\n🎉 全部步骤执行完毕！\n")


if __name__ == "__main__":
    main()