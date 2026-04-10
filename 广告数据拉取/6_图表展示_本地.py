import pandas as pd
from flask import Flask, render_template_string
import matplotlib.pyplot as plt


app = Flask(__name__)
# 设置全局字体，解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']  # 优先使用的字体列表
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号


def load_chart_data():
    """读取 CSV 并按日期汇总 installs、spend、clicks。"""
    file_path = "merged_adjust_fb.csv"
    df = pd.read_csv(file_path, dtype={"campaign_id": str})

    # 统一字段，避免空值导致汇总异常
    df["day"] = pd.to_datetime(df["day"], errors="coerce")
    for col in ["installs", "spend", "clicks"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    grouped = (
        df.groupby("day", as_index=False)[["installs", "spend", "clicks"]]
        .sum()
        .sort_values("day")
    )
    grouped["day"] = grouped["day"].dt.strftime("%Y-%m-%d")

    return {
        "days": grouped["day"].tolist(),
        "installs": grouped["installs"].round(2).tolist(),
        "spend": grouped["spend"].round(2).tolist(),
        "clicks": grouped["clicks"].round(2).tolist(),
    }


@app.route("/")
def dashboard():
    chart_data = load_chart_data()
    return render_template_string(
        """
<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>广告数据仪表盘</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; background: #f7f8fa; }
        .wrap { max-width: 1200px; margin: 20px auto; padding: 0 16px; }
        .card { background: #fff; border-radius: 10px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        h2 { margin: 0 0 12px; }
        #barChart { width: 100%; height: 560px; }
    </style>
</head>
<body>
    <div class="wrap">
        <div class="card">
            <h2>按日期汇总（installs / spend / clicks）</h2>
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
    app.run(host="127.0.0.1", port=5000, debug=True)
