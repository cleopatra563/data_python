import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import requests


# ===== 机器人 Webhook（替换成你自己的）=====
FEISHU_BOT_WEBHOOK = "https://open.larksuite.com/open-apis/bot/v2/hook/3b97dad8-443a-491d-91b6-9199d6018b66"

# ===== 机器人所属应用凭证（必须是已开启机器人能力的应用）=====
BOT_APP_ID = "cli_a94080d14d39ded0"
BOT_APP_SECRET = "eMIeYzPFc8yIz0CLDMXNUfIukJ8j5rDk"

# ===== 数据与图片文件 =====
CSV_FILE = "merged_adjust_fb.csv"
CHART_FILE = "ad_dashboard.jpg"

def get_bot_tenant_access_token():
    """使用机器人应用凭证获取 tenant_access_token。"""
    if BOT_APP_ID.startswith("请替换") or BOT_APP_SECRET.startswith("请替换"):
        raise RuntimeError("请先在脚本顶部配置 BOT_APP_ID 和 BOT_APP_SECRET")

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(
        url,
        json={"app_id": BOT_APP_ID, "app_secret": BOT_APP_SECRET},
        timeout=30,
    )
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"获取机器人 token 失败: {data}")
    return data.get("tenant_access_token")


def build_chart_image(csv_file: str, chart_file: str):
    """读取 merged CSV 后按日期聚合并生成图表图片。"""
    df = pd.read_csv(csv_file, dtype={"campaign_id": str})
    df["day"] = pd.to_datetime(df["day"], errors="coerce")

    for col in ["installs", "spend", "clicks"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    grouped = (
        df.groupby("day", as_index=False)[["installs", "spend", "clicks"]]
        .sum()
        .sort_values("day")
    )
    grouped["day_str"] = grouped["day"].dt.strftime("%Y-%m-%d")

    plt.figure(figsize=(14, 7))
    plt.plot(grouped["day_str"], grouped["installs"], marker="o", label="installs")
    plt.plot(grouped["day_str"], grouped["spend"], marker="o", label="spend")
    plt.plot(grouped["day_str"], grouped["clicks"], marker="o", label="clicks")
    # 使用英文标题，避免当前环境缺失中文字形导致告警
    plt.title("Ad Metrics by Date")
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    # 导出为 JPG，避免 PNG 透明通道导致的 libpng 警告
    plt.savefig(chart_file, dpi=200, format="jpg")
    plt.close()


def upload_image_to_feishu(token: str, image_path: str) -> str:
    """上传图片到飞书，返回 image_key。"""
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    headers = {"Authorization": f"Bearer {token}"}
    suffix = pathlib.Path(image_path).suffix.lower()
    mime_type = "image/jpeg" if suffix in [".jpg", ".jpeg"] else "image/png"

    with open(image_path, "rb") as f:
        files = {"image": (pathlib.Path(image_path).name, f, mime_type)}
        data = {"image_type": "message"}
        resp = requests.post(url, headers=headers, data=data, files=files, timeout=30)

    resp_data = resp.json()
    if resp_data.get("code") != 0:
        if resp_data.get("code") == 234007:
            raise RuntimeError(
                "上传飞书图片失败：当前 BOT_APP_ID 对应应用未开启机器人能力。"
                "请到飞书开放平台打开该应用的机器人能力后重试。"
            )
        raise RuntimeError(f"上传飞书图片失败: {resp_data}")

    image_key = resp_data["data"]["image_key"]
    return image_key


def send_image_by_bot(webhook_url: str, image_key: str):
    """通过飞书机器人向群聊发送图片消息。"""
    payload = {"msg_type": "image", "content": {"image_key": image_key}}
    resp = requests.post(webhook_url, json=payload, timeout=30)
    resp_data = resp.json()
    if resp_data.get("code") != 0:
        raise RuntimeError(f"飞书机器人发送失败: {resp_data}")


def main():
    token = get_bot_tenant_access_token()
    build_chart_image(CSV_FILE, CHART_FILE)
    image_key = upload_image_to_feishu(token, CHART_FILE)
    send_image_by_bot(FEISHU_BOT_WEBHOOK, image_key)
    print(f"发送成功，图片文件: {CHART_FILE}")


if __name__ == "__main__":
    main()
