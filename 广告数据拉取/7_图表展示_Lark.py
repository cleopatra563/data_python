import importlib.util
import pathlib

import pandas as pd
import requests
from flask import Flask, render_template_string


app = Flask(__name__)


def load_feishu_writer_module():
    """动态加载写入飞书脚本，复用其鉴权配置。"""
    path = pathlib.Path(__file__).parent / "4_写入飞书表格.py"
    if not path.exists():
        raise FileNotFoundError(f"找不到脚本文件: {path}")

    spec = importlib.util.spec_from_file_location("feishu_writer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fetch_bitable_records(token, app_token, table_id):
    """从飞书多维表格分页拉取全部记录。"""
    url = f"https://open.larksuite.com/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {token}"}

    all_items = []
    page_token = ""

    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token

        resp = requests.get(url, headers=headers, params=params, timeout=30)
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"拉取飞书多维表格失败: {data}")

        result = data.get("data", {})
        items = result.get("items", [])
        all_items.extend(items)

        if not result.get("has_more"):
            break
        page_token = result.get("page_token", "")

    return all_items


def to_day_string(value):
    """将飞书返回的日期值转换为 YYYY-MM-DD。"""
    if pd.isna(value) or value == "":
        return None

    def format_dt(dt_value):
        if pd.isna(dt_value):
            return None
        return dt_value.strftime("%Y-%m-%d")

    if isinstance(value, (int, float)):
        # 飞书日期字段常见为 Unix 毫秒时间戳
        dt = pd.to_datetime(value, unit="ms", errors="coerce")
        return format_dt(dt)

    text = str(value).strip()
    if text.isdigit():
        dt = pd.to_datetime(int(text), unit="ms", errors="coerce")
        return format_dt(dt)

    dt = pd.to_datetime(text, errors="coerce")
    return format_dt(dt)


def load_chart_data_from_lark():
    """拉取飞书多维表格数据并按日期汇总 installs、spend、clicks。"""
    feishu = load_feishu_writer_module()
    token = feishu.get_tenant_access_token(feishu.app_id, feishu.app_secret)
    if not token:
        raise RuntimeError("获取飞书 tenant_access_token 失败")

    items = fetch_bitable_records(token, feishu.APP_TOKEN, feishu.TABLE_ID)
    rows = [item.get("fields", {}) for item in items]
    if not rows:
        return {"days": [], "installs": [], "spend": [], "clicks": []}

    df = pd.DataFrame(rows)

    if "day" not in df.columns:
        raise RuntimeError("飞书多维表格中缺少 day 字段")

    for col in ["installs", "spend", "clicks"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["day"] = df["day"].apply(to_day_string)
    df = df.dropna(subset=["day"])

    grouped = (
        df.groupby("day", as_index=False)[["installs", "spend", "clicks"]]
        .sum()
        .sort_values("day")
    )

    return {
        "days": grouped["day"].tolist(),
        "installs": grouped["installs"].round(2).tolist(),
        "spend": grouped["spend"].round(2).tolist(),
        "clicks": grouped["clicks"].round(2).tolist(),
    }


@app.route("/")
def dashboard():
    chart_data = load_chart_data_from_lark()
    return render_template_string(
        """
<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>广告数据仪表盘（飞书多维表格）</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; background: #f7f8fa; }
        .wrap { max-width: 1200px; margin: 20px auto; padding: 0 16px; }
        .card { background: #fff; border-radius: 10px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        h2 { margin: 0 0 12px; }
        #barChart { width: 100%; height: 560px; }
        .hint { color: #666; margin-bottom: 8px; }
    </style>
</head>
<body>
    <div class="wrap">
        <div class="card">
            <h2>按日期汇总（数据源：飞书多维表格）</h2>
            <div class="hint">指标：installs / spend / clicks</div>
            <div id="barChart"></div>
        </div>
    </div>

    <script>
        const days = {{ chart_data.days | tojson }};
        const installs = {{ chart_data.installs | tojson }};
        const spend = {{ chart_data.spend | tojson }};
        const clicks = {{ chart_data.clicks | tojson }};

        const chart = echarts.init(document.getElementById("barChart"));
        const option = {
            tooltip: { trigger: "axis" },
            legend: { data: ["installs", "spend", "clicks"] },
            grid: { left: 50, right: 20, top: 50, bottom: 80 },
            xAxis: {
                type: "category",
                data: days,
                axisLabel: { rotate: 45 }
            },
            yAxis: { type: "value" },
            series: [
                { name: "installs", type: "bar", data: installs },
                { name: "spend", type: "bar", data: spend },
                { name: "clicks", type: "bar", data: clicks }
            ]
        };

        chart.setOption(option);
        window.addEventListener("resize", function () {
            chart.resize();
        });
    </script>
</body>
</html>
        """,
        chart_data=chart_data,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
